from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


# Schema for meta data
class MetaData(BaseModel):
    total: int | None = None
    page: int | None = None
    page_size: int | None = None

    model_config = {"extra": "allow"}


# Schema for Success Response
class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T | None = None
    meta: MetaData | None = None


# Schema For Error Response
class ErrorDetail(BaseModel):
    error_code: str
    error_type: str


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: ErrorDetail | None = None
