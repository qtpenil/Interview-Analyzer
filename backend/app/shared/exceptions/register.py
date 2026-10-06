from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded

from app.shared.exceptions.base_exception import AppException
from app.shared.exceptions.handlers import (
    app_exception_handler,
    global_exception_handler,
    rate_limit_exceeded_handler,
)


def register_exception_handlers(app: FastAPI):

    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]

    app.add_exception_handler(Exception, global_exception_handler)
