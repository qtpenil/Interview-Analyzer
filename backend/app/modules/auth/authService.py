from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis import redis_client
from app.core.security import (
    decode_token,
    generate_OTP,
    generate_token,
    password_hasher,
    validate_verification_token,
)
from app.modules.user.UserModel import User
from app.shared.exceptions.base_exception import AppException
from app.shared.exceptions.custom_exceptions import (
    AlreadyExistError,
    AuthenticationError,
    InternalServerError,
    InvalidOTPError,
    OTPExpiredError,
    TooManyRequestsError,
    UserNotFoundError,
)
from app.shared.logger.logger import get_logger
from app.tasks.email_tasks import send_otp_email

from .authSchema import (
    LoginRequest,
    RegisterRequest,
    ResetPasswordSchema,
    SendEmailSchema,
    UserCheckResponse,
    VerifyEmailSchema,
    VerifyOTPResponse,
)

logger = get_logger(__name__)


def register_service(db: Session, data: RegisterRequest):

    existing_user = db.query(User).filter_by(email=data.email).first()

    if existing_user:
        raise AlreadyExistError("User already exists")

    hashed_password = password_hasher.hash(data.password)

    user = User(  # type: ignore[call-arg]  # sqlalchemy plugin cannot infer mapped kwargs
        email=data.email,
        name=data.name,
        password_hash=hashed_password,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()
        raise AlreadyExistError("User already exists")

    except AppException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error occurred while registering user.")
        raise InternalServerError()

    access_token = generate_token("access", str(user.id))
    refresh_token = generate_token("refresh", str(user.id))

    user_response = UserCheckResponse.model_validate(user)

    return {
        "user": user_response,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def login_service(db: Session, data: LoginRequest):

    user = db.query(User).filter_by(email=data.email).first()

    if user is None:
        raise UserNotFoundError("No such user found.")

    if not password_hasher.verify(data.password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")

    access_token = generate_token("access", str(user.id))
    refresh_token = generate_token("refresh", str(user.id))

    user_response = UserCheckResponse.model_validate(user)

    return {
        "user": user_response,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def refresh_access_token_service(refresh_token: str):

    if not refresh_token:
        raise AuthenticationError("Not logged in")

    user_id = decode_token(refresh_token)

    new_access_token = generate_token("access", user_id)

    return {"access_token": new_access_token}


async def send_verification_email_service(data: SendEmailSchema, db: Session):
    try:
        user = db.query(User).filter_by(email=data.email).first()

        if not user:
            raise UserNotFoundError("No User found with provided email")

        otp = generate_OTP()

        await redis_client.set(
            f"otp:{data.email}",
            otp,
            ex=settings.REDIS_DATA_EXPIRE,
        )

        logger.info(
            "OTP stored in Redis for %s",
            data.email,
        )

        send_otp_email.delay(
            to_email=data.email,
            otp_code=otp,
        )

        logger.info(
            "OTP email queued for %s",
            data.email,
        )

        return {"message": "OTP sent successfully"}

    except Exception:
        logger.exception(
            "Failed to generate OTP for %s",
            data.email,
        )
        raise AppException("Couldn't send the email.")


async def resend_otp_service(data: SendEmailSchema, db: Session):
    try:
        user = db.query(User).filter_by(email=data.email).first()
        if not user:
            raise UserNotFoundError("No User found with provided email")

        cooldown_key = f"resend_cooldown:{data.email}"
        existing = await redis_client.get(cooldown_key)
        if existing:
            raise TooManyRequestsError("Please wait before requesting another OTP")

        otp = generate_OTP()

        await redis_client.set(
            f"otp:{data.email}",
            otp,
            ex=settings.REDIS_DATA_EXPIRE,
        )

        await redis_client.set(cooldown_key, "1", ex=30)

        send_otp_email.delay(to_email=data.email, otp_code=otp)

        return {"message": "OTP resent successfully"}

    except (UserNotFoundError, TooManyRequestsError):
        raise

    except Exception:
        logger.exception("Failed to resend OTP for %s", data.email)
        raise AppException("Couldn't resend the OTP.")


async def verify_otp_service(data: VerifyEmailSchema):
    try:
        stored_otp = await redis_client.get(f"otp:{data.email}")

        if not stored_otp:
            logger.warning(f"OTP verification attempted with no stored OTP for {data.email}")
            raise OTPExpiredError("This OTP is expired")

        if data.otp != stored_otp:
            logger.warning(f"Invalid OTP submitted for {data.email}")
            raise InvalidOTPError("The entered OTP is invalid")

        await redis_client.delete(f"otp:{data.email}")

        verification_token = generate_token("verification", data.email)

        await redis_client.set(
            f"verify:{verification_token}",
            data.email,
            ex=int(settings.VERIFICATION_TOKEN_EXPIRE_MINUTES) * 60,
        )

        return VerifyOTPResponse(
            message="OTP verified successfully",
            verification_token=verification_token,
        )

    except (OTPExpiredError, InvalidOTPError):
        # Don't convert these into AppException
        raise

    except Exception:
        logger.exception(f"Unexpected error verifying OTP for {data.email}")
        raise AppException("Couldn't verify OTP")


async def update_password_service(db: Session, data: ResetPasswordSchema, verification_token: str):
    try:
        logger.info("Update Password Service entered")

        stored_email = await validate_verification_token(verification_token)

        user = db.query(User).filter_by(email=stored_email).first()

        if not user:
            raise UserNotFoundError()

        user.password_hash = password_hasher.hash(data.new_password)

        db.commit()

        await redis_client.delete(f"verify:{verification_token}")

        logger.info("Password updated successfully")

        return {"user_id": user.id, "email": user.email}

    except AppException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        logger.error(f"Update password error: {e!s}")
        raise AppException("Something went wrong")
