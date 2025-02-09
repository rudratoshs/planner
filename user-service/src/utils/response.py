from pydantic import BaseModel
from typing import Any, Optional, Dict
from .translator import translate

class SuccessResponse(BaseModel):
    status: str = "success"
    code: int
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    status: str = "error"
    code: int
    error: Dict[str, Any]


def success_response(data: Any, message_key: str, lang: str, code: int = 200):
    return {
        "status": "success",
        "code": code,
        "message": translate(message_key, lang),
        "data": data,
    }


def error_response(error_key: str, lang: str, code: int, **extra):
    return {
        "status": "error",
        "code": code,
        "error": {
            "type": error_key,
            "message": translate(error_key, lang, **extra),
        },
    }