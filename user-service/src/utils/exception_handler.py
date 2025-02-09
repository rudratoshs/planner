from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom error response for validation errors."""
    errors = []

    for error in exc.errors():
        # Extract location information
        loc = error.get("loc", [])

        # Determine the most specific field name
        field = "body"
        if len(loc) > 1:
            # Prefer the last item in location if it's not 'body'
            field = loc[-1] if loc[-1] != 'body' else loc[-2] if len(loc) > 2 else "body"

        # Customize error messages
        error_messages = {
            "INVALID_EMAIL_FORMAT": "Invalid email format. Please provide a valid email address.",
            "PASSWORD_TOO_SHORT": "Password must be at least 8 characters long.",
            "PASSWORD_MISSING_UPPERCASE": "Password must contain at least one uppercase letter.",
            "PASSWORD_MISSING_LOWERCASE": "Password must contain at least one lowercase letter.",
            "PASSWORD_MISSING_DIGIT": "Password must contain at least one digit.",
        }

        # Try to find a matching custom error message
        message = error.get("msg", "Validation failed")
        for key, custom_message in error_messages.items():
            if key in message:
                message = custom_message
                break

        errors.append({
            "field": field,
            "message": message
        })

    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "code": 422,
            "error": {
                "type": "VALIDATION_FAILED",
                "details": errors,
            }
        },
    )

def setup_exception_handlers(app: FastAPI):
    """Register the custom exception handler."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)