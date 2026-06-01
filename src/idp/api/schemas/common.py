"""Common API schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail object."""

    code: str = Field(..., description="Application specific error code")
    message: str = Field(..., description="Human readable error message")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total number of items")


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard response envelope for all API responses."""

    data: T | None = Field(None, description="Response payload")
    meta: PaginationMeta | None = Field(None, description="Pagination metadata, if applicable")
    error: ErrorDetail | None = Field(None, description="Error details, if any")
