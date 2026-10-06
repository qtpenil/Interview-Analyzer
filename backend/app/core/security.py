import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Request
from pwdlib import PasswordHash
from pydantic import AfterValidator

from app.core.config import settings
from app.core.redis import redis_client
from app.shared.exceptions.custom_exceptions import (
    AccessTokenExpired,
    AuthenticationError,
    InvalidVerificationToken,
)

password_hasher = PasswordHash.recommended()


def generate_token(token_type: str, subject: str):

    config = settings.TOKEN_CONFIG.get(token_type)

    if not config:
        raise ValueError(f"Invalid token type: {token_type}")

    expire = config["expiry"]

    payload = {
        "token_type": token_type,
        "sub": str(subject),  # JWT sub must be a string
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(seconds=expire),
    }

    token = jwt.encode(payload, settings.SECRET_KEY, settings.ALGORITHM)
    return token


def decode_token(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        sub = payload["sub"]
        # Try to convert to int (for user_id), otherwise keep as string (for email)
        try:
            user_id = int(sub)
        except ValueError:
            user_id = sub  # Keep as string for email

        if payload.get("token_type") != "refresh":
            raise AuthenticationError("Invalid token type")

        return user_id

    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Refresh token expired")

    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid refresh token")


def generate_OTP():
    otp_code = "".join(secrets.choice("0123456789") for _ in range(6))
    return otp_code


def get_current_user(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise AuthenticationError("Not logged in")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload["sub"]
        # Try to convert to int (for user_id), otherwise keep as string (for email)
        try:
            user_id = int(sub)
        except ValueError:
            user_id = sub  # Keep as string for email
        return user_id

    except jwt.ExpiredSignatureError:
        raise AccessTokenExpired("Access token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")
    except Exception:
        raise AuthenticationError("Invalid token")


def validated_Pass(password):
    pattern = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*?])"

    if not re.match(pattern, password):
        raise ValueError(
            "Password must contain 1 uppercase letter, 1 lowercase letter, 1 digit and 1 special character"
        )

    if len(password) < 8:
        raise ValueError("Password must be atleast 8 character long")

    return password


async def validate_verification_token(verification_token: str) -> str:
    if not verification_token:
        raise InvalidVerificationToken("Verification token is missing")

    redis_key = f"verify:{verification_token}"
    email = await redis_client.get(redis_key)

    if not email:
        raise InvalidVerificationToken("Invalid or expired verification token")

    return email


PasswordStr = Annotated[str, AfterValidator(validated_Pass)]
