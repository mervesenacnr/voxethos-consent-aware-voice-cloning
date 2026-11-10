"""Health contract schema."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Stable readiness response preserved from Phase 3."""

    status: str = Field(min_length=1)
    service: str = Field(min_length=1)
