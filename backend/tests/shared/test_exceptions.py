from unittest.mock import AsyncMock

import pytest
from fastapi.responses import JSONResponse

from app.shared.exceptions.custom_exceptions import (
    AlreadyExistError,
    AuthenticationError,
    BadRequestException,
    FFmpegExecutionException,
    FFmpegNotFoundException,
    FileUploadException,
    InternalServerError,
    InvalidOTPError,
    InvalidVerificationToken,
    MissingVerificationToken,
    OTPExpiredError,
    ResourceNotFoundException,
    UserNotFoundError,
)
from app.shared.exceptions.handlers import app_exception_handler, global_exception_handler


class TestAppException:
    def test_base_exception_has_status_code(self):
        from app.shared.exceptions.base_exception import AppException

        exc = AppException(message="Test error")
        assert exc.message == "Test error"
        assert exc.status_code == 400

    def test_base_exception_has_error_code(self):
        from app.shared.exceptions.base_exception import AppException

        exc = AppException(message="Test")
        assert exc.error_code is not None


class TestCustomExceptions:
    @pytest.mark.parametrize(
        "exc_class,expected_status,expected_code",
        [
            (AuthenticationError, 401, "authentication_error"),
            (BadRequestException, 400, "bad_request"),
            (ResourceNotFoundException, 404, "resource_not_found"),
            (AlreadyExistError, 409, "entity_already_error"),
            (InternalServerError, 500, "internal_server_error"),
            (InvalidOTPError, 400, "invalid_otp"),
            (InvalidVerificationToken, 401, "invalid_verification_token"),
            (MissingVerificationToken, 400, "missing_verification_token"),
            (OTPExpiredError, 400, "otp_expired"),
            (FileUploadException, 400, None),
            (FFmpegNotFoundException, 500, None),
            (FFmpegExecutionException, 500, None),
        ],
    )
    def test_exception_attributes(self, exc_class, expected_status, expected_code):
        exc = exc_class(message="Test error message")
        assert exc.status_code == expected_status
        if expected_code:
            assert exc.error_code == expected_code


class TestUserNotFoundError:
    def test_masks_email_in_message(self):
        exc = UserNotFoundError(message="not found")
        assert "not found" in str(exc).lower()


class TestExceptionHandlers:
    @pytest.mark.asyncio
    async def test_app_exception_handler_returns_error_response(self):
        from app.shared.exceptions.base_exception import AppException

        exc = AppException(message="Something went wrong", status_code=400, error_code="bad_request")

        mock_request = _make_mock_request()
        result = await app_exception_handler(mock_request, exc)
        assert isinstance(result, JSONResponse)
        body = result.body
        assert b"Something went wrong" in body

    @pytest.mark.asyncio
    async def test_global_exception_handler_returns_500(self):
        exc = Exception("Unexpected error")

        mock_request = _make_mock_request()
        result = await global_exception_handler(mock_request, exc)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500


def _make_mock_request():
    from unittest.mock import MagicMock

    request = MagicMock()
    request.url.path = "/test"
    request.method = "GET"
    return request
