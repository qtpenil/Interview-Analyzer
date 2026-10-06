from http import HTTPStatus

from app.shared.exceptions.base_exception import AppException


# Auth Based Exceptions
class AuthenticationError(AppException):
    default_message = "Authentication failed"
    status_code = HTTPStatus.UNAUTHORIZED
    error_code = "authentication_error"


class AccessTokenExpired(AppException):
    default_message = "Access token expired"
    status_code = HTTPStatus.UNAUTHORIZED
    error_code = "acces_token_expired"


class InvalidOTPError(AppException):
    default_message = "Invalid OTP"
    status_code = HTTPStatus.BAD_REQUEST
    error_code = "invalid_otp"


class InvalidVerificationToken(AppException):
    default_message = "Invalid or expired verification token"
    status_code = HTTPStatus.UNAUTHORIZED
    error_code = "invalid_verification_token"


class MissingVerificationToken(AppException):
    default_message = "Verification Token is missing"
    status_code = HTTPStatus.BAD_REQUEST
    error_code = "missing_verification_token"


class UserNotFoundError(AppException):
    default_message = "Invalid request"
    status_code = HTTPStatus.BAD_REQUEST
    error_code = "user_not_found"


class InternalServerError(AppException):
    default_message = "Something went wrong"
    status_code = 500
    error_code = "internal_server_error"


class ResourceNotFoundException(AppException):
    default_message = "Resource not Found"
    status_code = HTTPStatus.NOT_FOUND
    error_code = "resource_not_found"


class BadRequestException(AppException):
    default_message = "Bad Request"
    status_code = HTTPStatus.BAD_REQUEST
    error_code = "bad_request"


class AlreadyExistError(AppException):
    default_message = "Already Exists"
    status_code = HTTPStatus.CONFLICT
    error_code = "entity_already_error"


class TooManyRequestsError(AppException):
    default_message = "Too many requests"
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    error_code = "too_many_requests"


class OTPExpiredError(AppException):
    default_message = "OTP has expired"
    status_code = HTTPStatus.BAD_REQUEST
    error_code = "otp_expired"


class FileUploadException(AppException):
    def __init__(self, message: str = "File upload failed"):
        super().__init__(message=message, status_code=400)


class FFmpegNotFoundException(AppException):
    def __init__(
        self,
        message: str = ("FFmpeg executable not found. Please verify FFmpeg installation."),
    ):
        super().__init__(message=message, status_code=500)


class FFmpegExecutionException(AppException):
    def __init__(self, message: str = "FFmpeg processing failed."):
        super().__init__(message=message, status_code=500)
