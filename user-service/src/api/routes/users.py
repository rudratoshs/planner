from fastapi import APIRouter, Depends
from ...api.dependencies.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    return {"email": current_user["sub"]}