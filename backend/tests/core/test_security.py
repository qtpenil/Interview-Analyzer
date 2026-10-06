import time
from datetime import timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest

from app.core.security import (
    decode_token,
    generate_OTP,
    generate_token,
    get_current_user,
    validate_verification_token,
    validated_Pass,
)
from app.shared.exceptions.custom_exceptions import (
    AuthenticationError,
    InvalidVerificationToken,
)


class TestPasswordValidation:
    def test_valid_password_passes(self):
        assert validated_Pass("Strong@Pass1") == "Strong@Pass1"

    def test_missing_uppercase_raises(self):
        with pytest.raises(ValueError, match="uppercase"):
            validated_Pass("weak@pass1")

    def test_missing_lowercase_raises(self):
        with pytest.raises(ValueError, match="lowercase"):
            validated_Pass("WEAK@PASS1")

    def test_missing_digit_raises(self):
        with pytest.raises(ValueError, match="digit"):
            validated_Pass("Weak@Pass")

    def test_missing_special_char_raises(self):
        with pytest.raises(ValueError, match="special character"):
            validated_Pass("WeakPass1")

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="8 character"):
            validated_Pass("Sh@1")

    def test_empty_password_raises(self):
        with pytest.raises(ValueError):
            validated_Pass("")


class TestTokenGeneration:
    def test_generate_access_token(self):
        token = generate_token("access", "test-subject")
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_generate_refresh_token(self):
        token = generate_token("refresh", "test-subject")
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_generate_verification_token(self):
        token = generate_token("verification", "test-subject")
        assert isinstance(token, str)

    def test_token_contains_expected_claims(self):
        token = generate_token("access", "user-123")
        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload["sub"] == "user-123"
        assert payload["token_type"] == "access"

    def test_token_expiry(self):
        token = generate_token("access", "user-123")
        payload = jwt.decode(token, options={"verify_signature": False})
        assert "exp" in payload
        assert payload["exp"] > time.time()


class TestTokenDecoding:
    def test_decode_valid_token(self):
        with patch("app.core.config.settings.SECRET_KEY", "test-secret"):
            token = generate_token("refresh", "user-123")
            user_id = decode_token(token)
            assert user_id == "user-123"

    def test_decode_expired_token_raises(self):
        with patch("app.core.config.settings.SECRET_KEY", "test-secret"):
            token = jwt.encode(
                {
                    "sub": "user-123",
                    "token_type": "refresh",
                    "exp": 0,
                },
                "test-secret",
                algorithm="HS256",
            )
            with pytest.raises(AuthenticationError, match="Refresh token expired"):
                decode_token(token)

    def test_decode_invalid_signature_raises(self):
        token = jwt.encode(
            {"sub": "user-123", "token_type": "refresh"},
            "wrong-secret",
            algorithm="HS256",
        )
        with pytest.raises(AuthenticationError, match="Invalid refresh token"):
            decode_token(token)


class TestOTPGeneration:
    def test_generate_otp_returns_six_digit_string(self):
        otp = generate_OTP()
        assert len(otp) == 6
        assert otp.isdigit()

    def test_generate_otp_is_random(self):
        otps = {generate_OTP() for _ in range(100)}
        assert len(otps) > 1


class TestVerificationToken:
    @pytest.mark.asyncio
    async def test_validate_verification_token_invalid_raises(self):
        with pytest.raises(InvalidVerificationToken):
            await validate_verification_token("invalid-token")


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_no_cookie_raises(self):
        from fastapi import Request

        request = MagicMock(spec=Request)
        request.cookies = {}

        with pytest.raises(AuthenticationError, match="Not logged in"):
            await get_current_user(request)

    def _make_mock_request(self, cookies: dict):
        from unittest.mock import MagicMock

        from fastapi import Request

        request = MagicMock(spec=Request)
        request.cookies = cookies
        return request
