from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from ..utils.response import error_response

async def validation_exception_handler(request, exc: RequestValidationError):
    errors = {err["loc"][-1]: err["msg"] for err in exc.errors()}
    return JSONResponse(
        content=error_response("validation_failed", "VALIDATION_ERROR", details=errors),
        status_code=HTTP_422_UNPROCESSABLE_ENTITY
    )