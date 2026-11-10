"""Bounded upload intake without storage or analysis side effects."""

from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import AppError


class UploadService:
    """Read supported audio bytes once with a strict request-size ceiling."""

    ALLOWED_CONTENT_TYPES = frozenset({"audio/wav", "audio/x-wav", "audio/wave", "application/octet-stream"})

    def __init__(self, maximum_input_bytes: int | None = None) -> None:
        self.maximum_input_bytes = maximum_input_bytes or settings.max_audio_bytes

    async def read_bounded_payload(self, audio: UploadFile) -> tuple[bytes, str]:
        content_type = (audio.content_type or "application/octet-stream").lower().split(";", 1)[0].strip()
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise AppError("UNSUPPORTED_AUDIO", "Upload a PCM WAV recording.", 415)
        payload = await audio.read(self.maximum_input_bytes + 1)
        if not payload:
            raise AppError("EMPTY_AUDIO", "The uploaded audio file is empty.", 400)
        if len(payload) > self.maximum_input_bytes:
            raise AppError("AUDIO_TOO_LARGE", "The uploaded audio exceeds the configured size limit.", 413)
        return payload, content_type
