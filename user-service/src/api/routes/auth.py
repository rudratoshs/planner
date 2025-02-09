import redis
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from ...core.schemas.auth import Token, PasswordResetRequest, PasswordResetConfirm, RefreshTokenRequest
from ...core.schemas.user import UserCreate
from ...core.services.user_service import create_user, get_user_by_email
from ...core.services.auth_service import authenticate_user, record_failed_login
from ...core.services.password_reset_service import generate_password_reset_token, reset_password
from ...utils.security import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    expire_inactive_sessions,
)
from ...utils.response import success_response, error_response
from ...config.settings import (
    API_V1_PREFIX,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from datetime import datetime, timedelta
from prisma import Prisma
from ...utils.rate_limit import is_rate_limited
from ...utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_V1_PREFIX}/auth/login")

db = Prisma()

async def get_db():
    """Ensure Prisma connection"""
    if not db.is_connected():
        await db.connect()
    return db

# Initialize Redis connection
redis_client = redis.StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True
)

RATE_LIMIT_SECONDS = 60  # Allow 1 request per minute

@router.post("/register")
async def register_user(user_data: UserCreate, lang: str = "en"):
    """Register a new user"""
    if is_rate_limited("register", user_data.email):
        logger.warning("Rate limit reached for registration", {"email": user_data.email})
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_response("TOO_MANY_REGISTER_ATTEMPTS", lang, 429)
        )

    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        logger.warning("Registration attempt with existing email", {"email": user_data.email})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("EMAIL_ALREADY_REGISTERED", lang, 400),
        )

    user = await create_user(user_data.email, user_data.password, user_data.full_name)
    logger.info("New user registered", {"user_id": user.id, "email": user.email})

    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    return success_response(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_at": expires_at.isoformat() + "Z",
            "user": {"id": user.id, "email": user.email},
        },
        "USER_REGISTERED_SUCCESS",
        lang,
    )

@router.post("/login")
async def login_user(request: Request, email: str, password: str, lang: str = "en"):
    """Authenticate user and return access & refresh tokens"""
    if is_rate_limited("login", email):
        logger.warning("Rate limit reached for login", {"email": email, "ip": request.client.host})
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_response("TOO_MANY_LOGIN_ATTEMPTS", lang, 429)
        )

    await expire_inactive_sessions()
    user = await authenticate_user(email, password)

    if not user:
        await record_failed_login(email, request.client.host)
        logger.warning("Failed login attempt", {"email": email, "ip": request.client.host})
        raise HTTPException(
            status_code=400, detail=error_response("INVALID_CREDENTIALS", lang, 400)
        )

    access_token = create_access_token({"sub": user.email, "user_id": user.id})
    refresh_token = create_refresh_token({"sub": user.email, "user_id": user.id})

    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    logger.info("User logged in", {"user_id": user.id, "email": user.email, "ip": request.client.host})

    return success_response(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_at": expires_at.isoformat() + "Z",
            "user": {"id": user.id, "email": user.email},
        },
        "LOGIN_SUCCESS",
        lang,
    )

@router.post("/logout")
async def logout(request: RefreshTokenRequest, lang: str = "en", db: Prisma = Depends(get_db)):
    """Logout user by blacklisting refresh token and logging the timestamp"""
    if not request.refresh_token:
        raise HTTPException(
            status_code=400, detail=error_response("MISSING_REFRESH_TOKEN", lang, 400)
        )

    session = await db.user_session.find_unique(where={"session_token": request.refresh_token})
    if session:
        await db.user_session.update(where={"id": session.id}, data={"logout_at": datetime.utcnow()})
    
    blacklist_token(request.refresh_token, expiration=30 * 24 * 60 * 60)
    logger.info("User logged out", {"session_token": request.refresh_token})

    return success_response({}, "LOGOUT_SUCCESS", lang)

@router.post("/request-password-reset")
async def request_password_reset(request: PasswordResetRequest, lang: str = "en"):
    """Handles password reset requests"""
    if is_rate_limited(request.email):
        logger.warning("Rate limit reached for password reset", {"email": request.email})
        raise HTTPException(
            status_code=429, detail=error_response("TOO_MANY_REQUESTS", lang, 429)
        )

    success = await generate_password_reset_token(request.email)
    if not success:
        raise HTTPException(
            status_code=404, detail=error_response("USER_NOT_FOUND", lang, 404)
        )

    logger.info("Password reset requested", {"email": request.email})
    return success_response(None, "PASSWORD_RESET_SENT", lang)

@router.post("/reset-password")
async def reset_password_endpoint(request: PasswordResetConfirm, lang: str = "en"):
    """Verifies reset token and updates password"""
    success = await reset_password(request.token, request.new_password)
    if not success:
        logger.warning("Invalid password reset attempt", {"token": request.token})
        raise HTTPException(
            status_code=400,
            detail=error_response("INVALID_OR_EXPIRED_TOKEN", lang, 400),
        )

    logger.info("User password reset successful", {"token": request.token})
    return success_response(None, "PASSWORD_RESET_SUCCESS", lang)

@router.post("/refresh-token")
async def refresh_token_endpoint(request: RefreshTokenRequest, lang: str = "en"):
    """Generate a new access token using a refresh token"""
    if is_rate_limited("refresh_token", request.refresh_token):
        logger.warning("Rate limit reached for token refresh", {"refresh_token": request.refresh_token})
        raise HTTPException(
            status_code=429,
            detail=error_response("TOO_MANY_REFRESH_ATTEMPTS", lang, 429)
        )

    payload = decode_access_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=401, detail=error_response("INVALID_REFRESH_TOKEN", lang, 401)
        )

    user_email = payload.get("sub")
    new_access_token = create_access_token({"sub": user_email})
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    logger.info("Access token refreshed", {"email": user_email})
    return success_response(
        {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_at": expires_at.isoformat() + "Z",
        },
        "TOKEN_REFRESH_SUCCESS",
        lang,
    )