"""Immutable, safe results produced by the technical audio boundary."""

from dataclasses import dataclass
import math
from enum import StrEnum


class TechnicalQualityStatus(StrEnum):
    ACCEPTABLE = "ACCEPTABLE"
    DEGRADED = "DEGRADED"


class SpeechPresenceStatus(StrEnum):
    NOT_EVALUATED = "NOT_EVALUATED"


def _finite(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _unit(value: float, name: str) -> float:
    result = _finite(value, name)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be between zero and one.")
    return result


@dataclass(frozen=True, slots=True)
class AudioFormatMetadata:
    container: str
    encoding: str
    sample_rate_hz: int
    channels: int
    sample_width_bytes: int
    frame_count: int
    duration_seconds: float

    def __post_init__(self) -> None:
        if self.container != "RIFF/WAVE" or self.encoding != "PCM16_LE":
            raise ValueError("Audio format metadata is outside the PCM16 contract.")
        if self.sample_rate_hz <= 0 or self.channels <= 0 or self.sample_width_bytes != 2 or self.frame_count <= 0:
            raise ValueError("Audio format metadata contains invalid dimensions.")
        if _finite(self.duration_seconds, "duration_seconds") <= 0:
            raise ValueError("duration_seconds must be positive.")


@dataclass(frozen=True, slots=True)
class AudioQualityMetrics:
    peak_amplitude: float
    rms_amplitude: float
    active_window_ratio: float
    silence_window_ratio: float
    clipping_ratio: float
    dc_offset: float
    zero_crossing_rate: float

    def __post_init__(self) -> None:
        for name in ("peak_amplitude", "rms_amplitude", "active_window_ratio", "silence_window_ratio", "clipping_ratio", "dc_offset", "zero_crossing_rate"):
            _unit(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class AudioInspectionResult:
    format: AudioFormatMetadata
    metrics: AudioQualityMetrics
    signal_present: bool
    technical_quality_status: TechnicalQualityStatus
    reason_codes: tuple[str, ...]
    speech_presence_status: SpeechPresenceStatus = SpeechPresenceStatus.NOT_EVALUATED
    inspection_version: str = "phase15.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.reason_codes, tuple):
            raise ValueError("reason_codes must be immutable.")
        if self.speech_presence_status is not SpeechPresenceStatus.NOT_EVALUATED:
            raise ValueError("Phase 15 does not evaluate speech presence.")
        if any(not isinstance(code, str) or not code for code in self.reason_codes):
            raise ValueError("reason_codes must contain safe strings.")
