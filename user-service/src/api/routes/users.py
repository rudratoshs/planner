from fastapi import APIRouter, Depends
from ...api.dependencies.auth import get_current_user
from ...utils.response import success_response

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
async def get_my_profile(current_user: dict = Depends(get_current_user), lang: str = "en"):
    """Return the currently authenticated user's profile."""
    return success_response(
        {"email": current_user["sub"]},
        "USER_PROFILE_FETCHED",
        lang
    )