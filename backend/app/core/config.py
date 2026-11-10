"""Environment-backed settings for the VoxEthos research API."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings shared by API startup and service wiring."""

    platform_name: str = "VoxEthos"
    tagline: str = "Turkish speech research with transparent, request-scoped audio analysis."
    api_version: str = "0.2.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:5173"
    max_audio_bytes: int = 10 * 1024 * 1024

    def __post_init__(self) -> None:
        if self.api_port < 1 or self.api_port > 65535:
            raise ValueError("api_port must be between 1 and 65535")
        if self.max_audio_bytes < 1 or self.max_audio_bytes > 100 * 1024 * 1024:
            raise ValueError("max_audio_bytes must be between 1 byte and 100 MiB")
        if not self.frontend_origin.startswith(("http://", "https://")):
            raise ValueError("frontend_origin must be an explicit HTTP(S) origin")

    @classmethod
    def from_environment(cls) -> "Settings":
        """Load deployment-safe overrides without exposing secrets in source."""
        defaults = cls()
        return cls(
            platform_name=os.getenv("VOXETHOS_PLATFORM_NAME", defaults.platform_name),
            tagline=os.getenv("VOXETHOS_TAGLINE", defaults.tagline),
            api_version=os.getenv("VOXETHOS_API_VERSION", defaults.api_version),
            api_host=os.getenv("VOXETHOS_API_HOST", defaults.api_host),
            api_port=int(os.getenv("VOXETHOS_API_PORT", str(defaults.api_port))),
            frontend_origin=os.getenv("VOXETHOS_FRONTEND_ORIGIN", defaults.frontend_origin),
            max_audio_bytes=int(os.getenv("VOXETHOS_MAX_AUDIO_BYTES", str(defaults.max_audio_bytes))),
        )


settings = Settings.from_environment()
