"""Readiness and health endpoints."""

from fastapi import APIRouter

from app.core.config import settings
from app.models.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return a lightweight readiness response for the platform API."""
    return HealthResponse(status="ok", service=settings.platform_name)
