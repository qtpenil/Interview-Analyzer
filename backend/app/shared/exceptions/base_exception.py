from http import HTTPStatus


class AppException(Exception):
    """
    Base exception for the entire project.
    All custom exceptions MUST inherit from this.
    """

    default_message = "An application error occurred"
    status_code: int = HTTPStatus.BAD_REQUEST
    error_code = "app_error"

    def __init__(
        self,
        message: str | None = None,
        status_code: int | None = None,
        error_code: str | None = None,
    ):
        self.message = message or self.default_message
        self.status_code = status_code or self.status_code
        self.error_code = error_code or self.error_code
        super().__init__(self.message)
