from typing import Optional

from app.shared.response_handler.responseSchema import (
    ErrorDetail,
    ErrorResponse,
    MetaData,
    SuccessResponse,
)


class TestMetaData:
    def test_metadata_creation(self):
        meta = MetaData(total=100, page=1, page_size=20)
        assert meta.total == 100
        assert meta.page == 1
        assert meta.page_size == 20


class TestSuccessResponse:
    def test_success_response_with_data(self):
        response = SuccessResponse(
            message="Success",
            data={"key": "value"},
            meta=MetaData(total=1, page=1, page_size=10),
        )
        assert response.success is True
        assert response.message == "Success"
        assert response.data == {"key": "value"}
        assert response.meta.total == 1

    def test_success_response_without_data(self):
        response = SuccessResponse(message="No content")
        assert response.success is True
        assert response.data is None
        assert response.meta is None

    def test_success_response_generic_type(self):
        response = SuccessResponse[dict](message="OK", data={"id": "123"})
        assert response.data["id"] == "123"


class TestErrorDetail:
    def test_error_detail_creation(self):
        detail = ErrorDetail(error_code="NOT_FOUND", error_type="resource")
        assert detail.error_code == "NOT_FOUND"
        assert detail.error_type == "resource"


class TestErrorResponse:
    def test_error_response(self):
        response = ErrorResponse(message="Something went wrong")
        assert response.success is False
        assert response.message == "Something went wrong"
        assert response.error is None

    def test_error_response_with_detail(self):
        detail = ErrorDetail(error_code="VALIDATION", error_type="validation")
        response = ErrorResponse(message="Invalid input", error=detail)
        assert response.error.error_code == "VALIDATION"
        assert response.error.error_type == "validation"
