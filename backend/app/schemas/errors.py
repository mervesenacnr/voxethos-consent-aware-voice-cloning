"""Structured error response contract."""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Machine-readable error payload preserved from the backend boundary."""

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, object] | list[object] | None = None


class ErrorResponse(BaseModel):
    """Stable top-level API error envelope."""

    error: ErrorDetail
