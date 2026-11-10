"""Immutable engineering limits for the Phase 15 audio boundary."""

from dataclasses import dataclass
import math
import numbers

from app.audio.errors import AudioConfigurationError


def _finite_number(value: object, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise AudioConfigurationError(f"{name} must be finite and numeric.")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise AudioConfigurationError(f"{name} must be finite and positive." if positive else f"{name} must be finite.")
    return result


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, numbers.Integral) or int(value) <= 0:
        raise AudioConfigurationError(f"{name} must be a positive integer.")
    return int(value)


@dataclass(frozen=True, slots=True, repr=False)
class AudioInspectionConfig:
    """Process-scoped technical audio limits, not calibrated speech thresholds."""

    maximum_input_bytes: int = 10 * 1024 * 1024
    minimum_sample_rate_hz: int = 8_000
    maximum_sample_rate_hz: int = 96_000
    maximum_channels: int = 2
    maximum_duration_seconds: float = 30.0
    maximum_decoded_frames: int = 2_880_000
    analysis_window_ms: int = 20
    silence_rms_threshold: float = 0.01
    minimum_active_window_ratio: float = 0.10
    clipping_amplitude_threshold: float = 0.99
    maximum_acceptable_clipping_ratio: float = 0.01
    maximum_acceptable_dc_offset: float = 0.05
    metric_chunk_size: int = 1_000_000

    def __post_init__(self) -> None:
        int_fields = (
            (self.maximum_input_bytes, "maximum_input_bytes"),
            (self.minimum_sample_rate_hz, "minimum_sample_rate_hz"),
            (self.maximum_sample_rate_hz, "maximum_sample_rate_hz"),
            (self.maximum_channels, "maximum_channels"),
            (self.maximum_decoded_frames, "maximum_decoded_frames"),
            (self.analysis_window_ms, "analysis_window_ms"),
            (self.metric_chunk_size, "metric_chunk_size"),
        )
        for value, name in int_fields:
            _positive_int(value, name)
        _finite_number(self.maximum_duration_seconds, "maximum_duration_seconds", positive=True)
        bounded = (
            (self.silence_rms_threshold, "silence_rms_threshold", False),
            (self.minimum_active_window_ratio, "minimum_active_window_ratio", False),
            (self.clipping_amplitude_threshold, "clipping_amplitude_threshold", False),
            (self.maximum_acceptable_clipping_ratio, "maximum_acceptable_clipping_ratio", False),
            (self.maximum_acceptable_dc_offset, "maximum_acceptable_dc_offset", False),
        )
        for value, name, _ in bounded:
            number = _finite_number(value, name)
            if not 0.0 <= number <= 1.0:
                raise AudioConfigurationError(f"{name} must be between zero and one.")
        if not 0.0 < self.clipping_amplitude_threshold <= 1.0:
            raise AudioConfigurationError("clipping_amplitude_threshold must be greater than zero.")
        if self.minimum_sample_rate_hz > self.maximum_sample_rate_hz:
            raise AudioConfigurationError("minimum_sample_rate_hz cannot exceed maximum_sample_rate_hz.")
        if self.maximum_channels > 2:
            raise AudioConfigurationError("maximum_channels cannot exceed two.")
        if self.maximum_decoded_frames < self.maximum_sample_rate_hz * self.maximum_duration_seconds:
            raise AudioConfigurationError("maximum_decoded_frames is smaller than the configured duration limit.")
        if self.analysis_window_ms > 60_000:
            raise AudioConfigurationError("analysis_window_ms is unreasonably large.")

    def __repr__(self) -> str:
        return (
            "AudioInspectionConfig("
            f"maximum_input_bytes={self.maximum_input_bytes}, "
            f"sample_rate={self.minimum_sample_rate_hz}-{self.maximum_sample_rate_hz}, "
            f"maximum_channels={self.maximum_channels}, "
            f"maximum_duration_seconds={self.maximum_duration_seconds})"
        )
