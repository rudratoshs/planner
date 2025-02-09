import json
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import Request
from ...utils.logger import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # ✅ Clone request body (avoid exhausting the stream)
        request_body = await request.body()
        request_body_str = request_body.decode("utf-8") if request_body else None

        logger.info(
            "Incoming request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "body": request_body_str,
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        # ✅ Recreate the request stream to prevent blocking
        async def new_receive():
            return {"type": "http.request", "body": request_body, "more_body": False}

        request._receive = new_receive  # Override the request stream with cloned data

        # ✅ Proceed with the request
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            "Response sent",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": f"{process_time:.2f}s",
                "ip_address": request.client.host if request.client else None,
            },
        )

        return response