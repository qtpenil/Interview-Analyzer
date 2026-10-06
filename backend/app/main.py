from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.rate_limiter import limiter
from app.modules.auth.authRoutes import auth_router
from app.modules.dashboard.routes import router as dashboard_router
from app.modules.files.file import File as FileModel  # noqa: F401
from app.modules.interview.InterviewModel import Interview  # noqa: F401
from app.modules.interview.routes import router as interview_router
from app.modules.interviewTopics.interviewTopics import InterviewTopic  # noqa: F401
from app.modules.user.OTPModel import OTP  # noqa: F401
from app.modules.user.UserModel import User  # noqa: F401
from app.shared.exceptions.register import register_exception_handlers
from app.shared.logger.logger import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Application startup complete")
    yield
    logger.info("Application shutting down")


def register_middlewares(app: FastAPI):

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # Expose Content-Disposition so the frontend can read the server-provided
        # download filename (e.g. interview-report-{username}.pdf).
        expose_headers=["Content-Disposition"],
    )


def register_routes(app: FastAPI):

    app.include_router(interview_router)
    app.include_router(auth_router)
    app.include_router(dashboard_router)

    @app.get("/")
    def health_check():
        return {"message": "Application Running"}


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    register_middlewares(app)
    register_exception_handlers(app)
    register_routes(app)
    app.state.limiter = limiter

    return app


app = create_app()
