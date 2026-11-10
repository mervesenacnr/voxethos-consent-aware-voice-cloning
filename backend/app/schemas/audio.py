"""Audio metadata and input contract schemas."""

from pydantic import BaseModel, Field


class AudioMetadata(BaseModel):
    """Metadata associated with an uploaded or generated audio asset."""

    filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    duration_ms: int | None = Field(default=None, ge=0)
    sample_rate_hz: int | None = Field(default=None, ge=1)
    channels: int | None = Field(default=None, ge=1)
