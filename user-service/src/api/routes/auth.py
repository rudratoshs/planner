import redis
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ...core.schemas.auth import Token, PasswordResetRequest, PasswordResetConfirm
from ...core.schemas.user import UserCreate
from ...core.services.user_service import create_user, get_user_by_email
from ...core.services.auth_service import authenticate_user
from ...core.services.password_reset_service import generate_password_reset_token, reset_password
from ...utils.security import blacklist_token,create_access_token, create_refresh_token
from ...utils.response import success_response, error_response
from ...config.settings import API_V1_PREFIX, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD,ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_V1_PREFIX}/auth/login")

# Initialize Redis connection
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
RATE_LIMIT_SECONDS = 60  # Allow 1 request per minute

def is_rate_limited(email: str) -> bool:
    """Check if the email is rate-limited"""
    key = f"reset_limit:{email}"
    if redis_client.exists(key):
        return True
    redis_client.setex(key, RATE_LIMIT_SECONDS, "locked")
    return False

@router.post("/register")
async def register_user(user_data: UserCreate, lang: str = "en"):
    """Register a new user"""
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_response("EMAIL_ALREADY_REGISTERED", lang, 400))

    user = await create_user(user_data.email, user_data.password, user_data.full_name)
    
    # Generate tokens
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return success_response(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_at": expires_at.isoformat() + "Z",
            "user": {
                "id": user.id,
                "email": user.email
            }
        },
        "USER_REGISTERED_SUCCESS",
        lang
    )

async def login_user(email: str, password: str, lang: str = "en"):
    """Authenticate user and return access & refresh tokens"""
    user = await authenticate_user(email, password)
    if not user:
        raise HTTPException(status_code=400, detail=error_response("INVALID_CREDENTIALS", lang, 400))

    # Generate tokens
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    return success_response(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_at": expires_at.isoformat() + "Z",
            "user": {
                "id": user.id,
                "email": user.email
            }
        },
        "LOGIN_SUCCESS",
        lang
    )

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme), lang: str = "en"):
    blacklist_token(token)
    return success_response(None, "LOGOUT_SUCCESS", lang)

@router.post("/request-password-reset")
async def request_password_reset(request: PasswordResetRequest, lang: str = "en"):
    if is_rate_limited(request.email):
        raise HTTPException(status_code=429, detail=error_response("TOO_MANY_REQUESTS", lang, 429))

    success = await generate_password_reset_token(request.email)
    if not success:
        raise HTTPException(status_code=404, detail=error_response("USER_NOT_FOUND", lang, 404))
    
    return success_response(None, "PASSWORD_RESET_SENT", lang)

@router.post("/reset-password")
async def reset_password_endpoint(request: PasswordResetConfirm, lang: str = "en"):
    success = await reset_password(request.token, request.new_password)
    if not success:
        raise HTTPException(status_code=400, detail=error_response("INVALID_OR_EXPIRED_TOKEN", lang, 400))
    
    return success_response(None, "PASSWORD_RESET_SUCCESS", lang)