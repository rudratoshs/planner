from fastapi import APIRouter, Depends, HTTPException, status
from ...core.schemas.auth import Token
from ...core.schemas.user import UserCreate
from ...core.services.user_service import create_user, get_user_by_email
from ...core.services.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

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