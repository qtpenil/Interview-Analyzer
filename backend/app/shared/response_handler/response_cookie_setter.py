from typing import Literal, cast

from fastapi import Response

from app.core.config import settings

SAMESITE_TYPE = Literal["lax", "strict", "none"]


def set_auth_cookie(response: Response, token: str, token_type: str):
    config = settings.TOKEN_CONFIG.get(token_type)

    if not config:
        raise ValueError("Invalid token type")

    response.set_cookie(
        key=config["cookie_name"],
        value=token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=cast(SAMESITE_TYPE, settings.COOKIE_SAMESITE),
        max_age=int(config["expiry"]),
        path="/",
    )


def clear_auth_cookie(response: Response, token_type: str):
    """Clear an authentication cookie by settings it to expire immediately.

    Must use same path/secure settings as when the cookie was set.
    """
    config = settings.TOKEN_CONFIG.get(token_type)

    if not config:
        raise ValueError("Invalid token type")

    response.delete_cookie(
        key=config["cookie_name"],
        path="/",
        secure=settings.COOKIE_SECURE,
        httponly=settings.COOKIE_HTTPONLY,
        samesite=cast(SAMESITE_TYPE, settings.COOKIE_SAMESITE),
    )
