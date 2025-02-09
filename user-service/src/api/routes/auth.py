import redis
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ...core.schemas.auth import Token
from ...core.schemas.user import UserCreate
from ...core.services.user_service import create_user, get_user_by_email
from ...core.services.auth_service import authenticate_user
from ...core.services.password_reset_service import generate_password_reset_token, reset_password
from ...core.schemas.auth import PasswordResetRequest, PasswordResetConfirm
from ...utils.security import blacklist_token
from ...config.settings import API_V1_PREFIX
from ...config.settings import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/{API_V1_PREFIX}/auth/login")

# Initialize Redis connection
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
RATE_LIMIT_SECONDS = 60  # Allow 1 request per minute

def is_rate_limited(email: str) -> bool:
    """ Check if the email is rate-limited """
    key = f"reset_limit:{email}"
    if redis_client.exists(key):
        return True
    redis_client.setex(key, RATE_LIMIT_SECONDS, "locked")
    return False

@router.post("/register", response_model=Token)
async def register_user(user_data: UserCreate):
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = await create_user(user_data.email, user_data.password, user_data.full_name)
    token = await authenticate_user(user.email, user_data.password)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login_user(email: str, password: str):
    token = await authenticate_user(email, password)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    blacklist_token(token)
    return {"message": "Logged out successfully"}

@router.post("/request-password-reset")
async def request_password_reset(request: PasswordResetRequest):
    if is_rate_limited(request.email):
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")

    success = await generate_password_reset_token(request.email)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Password reset token sent"}

@router.post("/reset-password")
async def reset_password_endpoint(request: PasswordResetConfirm):
    success = await reset_password(request.token, request.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    return {"message": "Password has been reset successfully"}