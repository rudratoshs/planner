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

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/{API_V1_PREFIX}/auth/login")

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
    reset_token = await generate_password_reset_token(request.email)
    if not reset_token:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Password reset token generated", "token": reset_token}

@router.post("/reset-password")
async def reset_password_endpoint(request: PasswordResetConfirm):
    success = await reset_password(request.token, request.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    return {"message": "Password has been reset successfully"}