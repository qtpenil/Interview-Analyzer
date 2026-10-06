from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.shared.exceptions.custom_exceptions import AuthenticationError, MissingVerificationToken
from app.shared.logger.logger import get_logger
from app.shared.response_handler.response_cookie_setter import (
    clear_auth_cookie,
    set_auth_cookie,
)
from app.shared.response_handler.responseSchema import SuccessResponse

from .authSchema import (
    LoginRequest,
    RegisterRequest,
    ResetPasswordSchema,
    SendEmailSchema,
    VerifyEmailSchema,
)
from .authService import (
    login_service,
    refresh_access_token_service,
    register_service,
    resend_otp_service,
    send_verification_email_service,
    update_password_service,
    verify_otp_service,
)

logger = get_logger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/register")
@limiter.limit("5/minutes")
async def register(
    request: Request,
    data: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    result = register_service(db, data)

    set_auth_cookie(response, result["access_token"], "access")
    set_auth_cookie(response, result["refresh_token"], "refresh")

    return SuccessResponse(message="User successfully registered", data=result["user"])


@auth_router.post("/login")
@limiter.limit("5/minutes")
async def login(
    request: Request,
    data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    result = login_service(db, data)

    set_auth_cookie(response, result["access_token"], "access")
    set_auth_cookie(response, result["refresh_token"], "refresh")
    logger.info(f"User {data.email} logged in successfully")

    return SuccessResponse(message="User successfully logged in", data=result["user"])


@auth_router.post("/logout")
async def logout(response: Response):
    """
    Logout endpoint - clears the access and refresh token cookies.

    Both are httpOnly, so the frontend cannot clear them itself via
    document.cookie; this route is the only way to remove them.
    """
    clear_auth_cookie(response, "access")
    clear_auth_cookie(response, "refresh")

    logger.info("User logged out successfully")

    return SuccessResponse(message="Logged out successfully")


@auth_router.post("/refreshToken")
async def auth_refresh_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise AuthenticationError("Missing refresh token")

    result = refresh_access_token_service(refresh_token)

    set_auth_cookie(response, result["access_token"], "access")

    logger.info("Token refreshed successfully")

    return SuccessResponse(message="Token refreshed")


@auth_router.post("/forgot-password")
@limiter.limit("5/minutes")
async def auth_forgot_password(request: Request, data: SendEmailSchema, db: Session = Depends(get_db)):
    result = await send_verification_email_service(data, db)
    return SuccessResponse(message=result["message"])


@auth_router.post("/resend-otp")
@limiter.limit("3/minute")
async def auth_resend_otp(request: Request, data: SendEmailSchema, db: Session = Depends(get_db)):
    result = await resend_otp_service(data, db)
    return SuccessResponse(message=result["message"])


@auth_router.post("/verify-otp")
@limiter.limit("5/minutes")
async def verify_otp_route(request: Request, data: VerifyEmailSchema, response: Response):

    result = await verify_otp_service(data)

    set_auth_cookie(response, token=result.verification_token, token_type="verification")

    return SuccessResponse(message=result.message)


@auth_router.post("/update-password")
@limiter.limit("5/minutes")
async def auth_update_password(
    data: ResetPasswordSchema,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Update password endpoint - requires verification_token cookie.
    """
    verification_token = request.cookies.get("verification_token")

    if not verification_token:
        raise MissingVerificationToken("Email verification required")

    await update_password_service(db=db, data=data, verification_token=verification_token)

    # Clean up verification cookie
    clear_auth_cookie(response, "verification")

    return SuccessResponse(message="Password updated successfully")
