from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.shared.exceptions.base_exception import AppException
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
):

    logger.warning(
        f"Rate limit exceeded for {request.method} {request.url.path} from "
        f"{request.client.host if request.client else 'unknown'}"
    )

    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "message": "Too many requests. Please try again later.",
            "data": None,
        },
        headers={"Retry-After": "60"},
    )


async def app_exception_handler(request: Request, exc: AppException):

    logger.error(f"{request.method} {request.url.path} - {exc.message}")

    return JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.message, "data": None})


async def global_exception_handler(request: Request, exc: Exception):

    logger.exception(f"Unexpected error: {exc!s}")

    return JSONResponse(status_code=500, content={"success": False, "message": "Internal Server Error", "data": None})
