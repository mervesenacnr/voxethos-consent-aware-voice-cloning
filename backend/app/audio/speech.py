"""Deterministic, bounded signal-activity estimation for validated PCM16."""

from dataclasses import dataclass
import math
from enum import StrEnum
from typing import Protocol

import numpy as np

from app.audio.errors import (
    SpeechAnalysisResourceError,
    SpeechConfigurationError,
    SpeechMetricCalculationError,
)


class SpeechStatus(StrEnum):
    ACTIVITY_PRESENT = "ACTIVITY_PRESENT"
    INSUFFICIENT_ACTIVITY = "INSUFFICIENT_ACTIVITY"
    NO_ACTIVITY = "NO_ACTIVITY"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass(frozen=True, slots=True)
class SpeechSegment:
    start_seconds: float
    end_seconds: float
    duration_seconds: float

    def __post_init__(self) -> None:
        values = (self.start_seconds, self.end_seconds, self.duration_seconds)
        if any(not math.isfinite(float(value)) for value in values):
            raise SpeechConfigurationError("Speech segment values must be finite.")
        if self.start_seconds < 0 or self.end_seconds <= self.start_seconds or self.duration_seconds <= 0:
            raise SpeechConfigurationError("Speech segment bounds must be positive and ordered.")
        if abs((self.end_seconds - self.start_seconds) - self.duration_seconds) > 1e-6:
            raise SpeechConfigurationError("Speech segment duration must match its bounds.")


@dataclass(frozen=True, slots=True)
class SpeechInspectionResult:
    status: SpeechStatus
    total_frame_count: int
    active_frame_count: int
    speech_active_ratio: float
    estimated_speech_duration_seconds: float
    segments: tuple[SpeechSegment, ...]
    reason_codes: tuple[str, ...]
    analyzer_version: str = "activity_heuristic_v1"

    def __post_init__(self) -> None:
        if self.total_frame_count < 0 or self.active_frame_count < 0 or self.active_frame_count > self.total_frame_count:
            raise SpeechConfigurationError("Speech frame counts are invalid.")
        for value in (self.speech_active_ratio, self.estimated_speech_duration_seconds):
            if not math.isfinite(float(value)) or value < 0:
                raise SpeechConfigurationError("Speech result metrics must be finite and non-negative.")
        if self.speech_active_ratio > 1.0:
            raise SpeechConfigurationError("Speech-active ratio must be bounded to one.")
        if not isinstance(self.segments, tuple) or not isinstance(self.reason_codes, tuple):
            raise SpeechConfigurationError("Speech result collections must be immutable.")
        if any(not isinstance(code, str) or not code for code in self.reason_codes):
            raise SpeechConfigurationError("Speech reason codes must be non-empty strings.")
        previous_end = -1.0
        for segment in self.segments:
            if segment.start_seconds < previous_end:
                raise SpeechConfigurationError("Speech segments must be ordered and non-overlapping.")
            previous_end = segment.end_seconds

    @classmethod
    def not_evaluated(cls) -> "SpeechInspectionResult":
        return cls(SpeechStatus.NOT_EVALUATED, 0, 0, 0.0, 0.0, (), ("ACTIVITY_NOT_EVALUATED",))


@dataclass(frozen=True, slots=True, repr=False)
class SpeechAnalysisConfig:
    """Conservative engineering thresholds, not a trained speech classifier."""

    frame_duration_ms: int = 20
    frame_hop_ms: int = 10
    minimum_rms: float = 0.015
    maximum_rms: float = 0.95
    minimum_zero_crossing_rate: float = 0.005
    maximum_zero_crossing_rate: float = 0.35
    minimum_consecutive_active_frames: int = 3
    maximum_inactive_gap_frames: int = 2
    minimum_segment_duration_seconds: float = 0.05
    minimum_total_speech_duration_seconds: float = 0.08
    minimum_speech_active_ratio: float = 0.15
    maximum_frame_count: int = 3_000
    maximum_returned_segments: int = 32
    maximum_sample_count: int = 2_880_000
    peak_ceiling: float = 0.98

    def __post_init__(self) -> None:
        integers = ("frame_duration_ms", "frame_hop_ms", "minimum_consecutive_active_frames", "maximum_inactive_gap_frames", "maximum_frame_count", "maximum_returned_segments", "maximum_sample_count")
        for name in integers:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise SpeechConfigurationError(f"{name} must be a positive integer.")
        if self.frame_hop_ms > self.frame_duration_ms:
            raise SpeechConfigurationError("frame_hop_ms cannot exceed frame_duration_ms.")
        numbers = ("minimum_rms", "maximum_rms", "minimum_zero_crossing_rate", "maximum_zero_crossing_rate", "minimum_speech_active_ratio", "peak_ceiling")
        for name in numbers:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise SpeechConfigurationError(f"{name} must be finite and numeric.")
            if not 0.0 <= float(value) <= 1.0:
                raise SpeechConfigurationError(f"{name} must be between zero and one.")
        for name in ("minimum_segment_duration_seconds", "minimum_total_speech_duration_seconds"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value <= 0:
                raise SpeechConfigurationError(f"{name} must be finite and positive.")
        if self.minimum_rms >= self.maximum_rms:
            raise SpeechConfigurationError("minimum_rms must be lower than maximum_rms.")
        if self.minimum_zero_crossing_rate >= self.maximum_zero_crossing_rate:
            raise SpeechConfigurationError("The zero-crossing-rate range is invalid.")
        if self.maximum_returned_segments > self.maximum_frame_count:
            raise SpeechConfigurationError("maximum_returned_segments is unreasonably large.")
        if self.maximum_sample_count < self.frame_duration_ms * 8:
            raise SpeechConfigurationError("maximum_sample_count is too small for a speech frame.")

    def __repr__(self) -> str:
        return f"SpeechAnalysisConfig(frame={self.frame_duration_ms}ms, hop={self.frame_hop_ms}ms, max_frames={self.maximum_frame_count})"


class SpeechAnalysisPolicy(Protocol):
    def analyze(self, samples: np.ndarray, sample_rate_hz: int) -> SpeechInspectionResult:
        """Estimate speech-like activity from already-decoded PCM16 samples."""
        ...


class DeterministicSpeechAnalyzer:
    """Estimate speech-like activity; this is not human-speech recognition."""

    def __init__(self, config: SpeechAnalysisConfig) -> None:
        self.config = config

    def analyze(self, samples: np.ndarray, sample_rate_hz: int) -> SpeechInspectionResult:
        try:
            values = np.asarray(samples, dtype=np.float32)
            if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
                raise SpeechMetricCalculationError("Speech samples are not finite one-dimensional values.")
            if sample_rate_hz <= 0 or values.size > self.config.maximum_sample_count:
                raise SpeechAnalysisResourceError("Speech analysis input exceeds the configured resource limit.")
            frame_length = max(1, round(sample_rate_hz * self.config.frame_duration_ms / 1000))
            hop_length = max(1, round(sample_rate_hz * self.config.frame_hop_ms / 1000))
            frame_count = 1 + max(0, (values.size - frame_length) // hop_length)
            if frame_count > self.config.maximum_frame_count:
                raise SpeechAnalysisResourceError("Speech analysis frame count exceeds the configured limit.")
            active: list[bool] = []
            for start in range(0, values.size - frame_length + 1, hop_length):
                frame = values[start:start + frame_length]
                rms = float(np.sqrt(np.mean(np.square(frame), dtype=np.float64)))
                peak = float(np.max(np.abs(frame)))
                crossings = int(np.count_nonzero((frame[:-1] < 0) & (frame[1:] >= 0)) + np.count_nonzero((frame[:-1] >= 0) & (frame[1:] < 0)))
                zcr = crossings / max(1, frame.size - 1)
                active.append(self.config.minimum_rms <= rms <= self.config.maximum_rms and zcr >= self.config.minimum_zero_crossing_rate and zcr <= self.config.maximum_zero_crossing_rate and peak <= self.config.peak_ceiling)
            active_count = sum(active)
            ratio = active_count / frame_count if frame_count else 0.0
            segments = self._segments(active, hop_length, frame_length, sample_rate_hz)
            total_duration = sum(segment.duration_seconds for segment in segments)
            reasons: list[str] = []
            if active_count == 0:
                status = SpeechStatus.NO_ACTIVITY
                reasons.append("NO_ACTIVITY_LIKE_SIGNAL")
            elif not segments:
                status = SpeechStatus.INSUFFICIENT_ACTIVITY
                reasons.append("ACTIVITY_SEGMENTS_TOO_SHORT")
            elif total_duration < self.config.minimum_total_speech_duration_seconds:
                status = SpeechStatus.INSUFFICIENT_ACTIVITY
                reasons.append("ACTIVITY_BELOW_MINIMUM_DURATION")
            elif ratio < self.config.minimum_speech_active_ratio:
                status = SpeechStatus.INSUFFICIENT_ACTIVITY
                reasons.append("ACTIVITY_BELOW_MINIMUM_RATIO")
            else:
                status = SpeechStatus.ACTIVITY_PRESENT
            return SpeechInspectionResult(status, frame_count, active_count, min(1.0, ratio), total_duration, tuple(segments[:self.config.maximum_returned_segments]), tuple(reasons))
        except (SpeechAnalysisResourceError, SpeechMetricCalculationError):
            raise
        except (TypeError, ValueError, FloatingPointError, OverflowError) as exc:
            raise SpeechMetricCalculationError("Speech-like activity metrics could not be calculated.") from exc

    def _segments(self, active: list[bool], hop: int, frame_length: int, sample_rate_hz: int) -> list[SpeechSegment]:
        runs: list[tuple[int, int]] = []
        index = 0
        while index < len(active):
            if not active[index]:
                index += 1
                continue
            start = index
            end = index
            gap = 0
            cursor = index + 1
            while cursor < len(active):
                if active[cursor]:
                    end = cursor; gap = 0
                else:
                    gap += 1
                    if gap > self.config.maximum_inactive_gap_frames:
                        break
                cursor += 1
            if end - start + 1 >= self.config.minimum_consecutive_active_frames:
                runs.append((start, end))
            index = max(cursor, end + 1)
        segments: list[SpeechSegment] = []
        for start, end in runs:
            start_seconds = start * hop / sample_rate_hz
            end_seconds = (end * hop + frame_length) / sample_rate_hz
            duration = end_seconds - start_seconds
            if duration >= self.config.minimum_segment_duration_seconds:
                segments.append(SpeechSegment(start_seconds, end_seconds, duration))
        return segments
