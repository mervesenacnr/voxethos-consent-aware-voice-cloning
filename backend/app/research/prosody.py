"""Bounded, deterministic signal features; experimental and not a trained model."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True, slots=True)
class ProsodyPoint:
    time_seconds: float
    rms: float
    f0_hz: float | None


@dataclass(frozen=True, slots=True)
class ProsodySummary:
    status: str
    estimator: str
    median_f0_hz: float | None
    p10_f0_hz: float | None
    p90_f0_hz: float | None
    voiced_frame_count: int
    total_frame_count: int
    voiced_frame_ratio: float
    pause_count_estimate: int
    energy_track: tuple[ProsodyPoint, ...]
    limitation: str


@dataclass(frozen=True, slots=True)
class ProsodyConfig:
    frame_duration_ms: int = 40
    hop_duration_ms: int = 10
    minimum_f0_hz: float = 70.0
    maximum_f0_hz: float = 400.0
    minimum_rms: float = 0.01
    minimum_correlation: float = 0.30
    minimum_pause_duration_seconds: float = 0.12
    maximum_frames: int = 3_000
    maximum_track_points: int = 120
    maximum_samples: int = 2_880_000

    def __post_init__(self) -> None:
        if self.frame_duration_ms <= self.hop_duration_ms or self.hop_duration_ms <= 0:
            raise ValueError("Prosody frame and hop durations are invalid.")
        if not (0 < self.minimum_f0_hz < self.maximum_f0_hz):
            raise ValueError("Prosody fundamental-frequency bounds are invalid.")
        if not (0 < self.minimum_rms < 1 and 0 < self.minimum_correlation < 1):
            raise ValueError("Prosody thresholds must be between zero and one.")
        if min(self.maximum_frames, self.maximum_track_points, self.maximum_samples) <= 0:
            raise ValueError("Prosody resource limits must be positive.")


class ProsodyAnalyzer:
    """Estimate pitch and amplitude features from validated mono PCM samples."""

    def __init__(self, config: ProsodyConfig | None = None) -> None:
        self.config = config or ProsodyConfig()

    def analyze(self, samples: np.ndarray, sample_rate_hz: int) -> ProsodySummary:
        try:
            values = np.asarray(samples, dtype=np.float32)
            if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
                raise ValueError("Prosody samples must be finite, non-empty mono audio.")
            if isinstance(sample_rate_hz, bool) or sample_rate_hz <= 0 or values.size > self.config.maximum_samples:
                raise ValueError("Prosody input exceeds the configured resource limit.")
            frame_length = max(1, round(sample_rate_hz * self.config.frame_duration_ms / 1000))
            hop_length = max(1, round(sample_rate_hz * self.config.hop_duration_ms / 1000))
            if values.size < frame_length:
                return self._empty()
            frame_count = min(1 + (values.size - frame_length) // hop_length, self.config.maximum_frames)
            window = np.hanning(frame_length).astype(np.float32)
            fft_size = 1 << (2 * frame_length - 1).bit_length()
            min_lag = max(1, int(sample_rate_hz / self.config.maximum_f0_hz))
            max_lag = min(frame_length - 2, int(sample_rate_hz / self.config.minimum_f0_hz))
            if min_lag >= max_lag:
                return self._empty()

            pitches: list[float] = []
            frame_rms: list[float] = []
            frame_pitch: list[float | None] = []
            frame_active: list[bool] = []
            for frame_index in range(frame_count):
                start = frame_index * hop_length
                frame = values[start:start + frame_length]
                rms = float(np.sqrt(np.mean(np.square(frame, dtype=np.float64))))
                frame_rms.append(rms)
                frame_active.append(rms >= self.config.minimum_rms)
                if rms < self.config.minimum_rms:
                    frame_pitch.append(None)
                    continue
                centered = (frame - float(np.mean(frame, dtype=np.float64))) * window
                spectrum = np.fft.rfft(centered, n=fft_size)
                autocorrelation = np.fft.irfft(spectrum * np.conjugate(spectrum), n=fft_size)[:frame_length]
                zero_lag = float(autocorrelation[0])
                if not math.isfinite(zero_lag) or zero_lag <= 0:
                    frame_pitch.append(None)
                    continue
                search = autocorrelation[min_lag:max_lag + 1]
                relative_index = int(np.argmax(search))
                lag = min_lag + relative_index
                confidence = float(autocorrelation[lag] / zero_lag)
                if confidence < self.config.minimum_correlation:
                    frame_pitch.append(None)
                    continue
                # Parabolic interpolation improves the period estimate between integer lags.
                if 1 <= lag < frame_length - 1:
                    left, center, right = (float(autocorrelation[lag - 1]), float(autocorrelation[lag]), float(autocorrelation[lag + 1]))
                    curvature = left - 2.0 * center + right
                    offset = 0.5 * (left - right) / curvature if abs(curvature) > 1e-12 else 0.0
                    offset = max(-0.5, min(0.5, offset))
                else:
                    offset = 0.0
                pitch = float(sample_rate_hz / (lag + offset))
                if self.config.minimum_f0_hz <= pitch <= self.config.maximum_f0_hz and math.isfinite(pitch):
                    pitches.append(pitch)
                    frame_pitch.append(pitch)
                else:
                    frame_pitch.append(None)

            if pitches:
                pitch_values = np.asarray(pitches, dtype=np.float64)
                median_f0 = float(np.median(pitch_values))
                p10_f0 = float(np.percentile(pitch_values, 10))
                p90_f0 = float(np.percentile(pitch_values, 90))
            else:
                median_f0 = p10_f0 = p90_f0 = None
            voiced_count = len(pitches)
            point_indices = np.unique(np.linspace(0, frame_count - 1, min(frame_count, self.config.maximum_track_points), dtype=int))
            track = tuple(
                ProsodyPoint(
                    time_seconds=float(index * hop_length / sample_rate_hz),
                    rms=float(max(0.0, min(1.0, frame_rms[index]))),
                    f0_hz=frame_pitch[index],
                )
                for index in point_indices
            )
            return ProsodySummary(
                status="EXPERIMENTAL_DSP",
                estimator="windowed_autocorrelation_v1",
                median_f0_hz=median_f0,
                p10_f0_hz=p10_f0,
                p90_f0_hz=p90_f0,
                voiced_frame_count=voiced_count,
                total_frame_count=frame_count,
                voiced_frame_ratio=float(voiced_count / frame_count) if frame_count else 0.0,
                pause_count_estimate=self._count_internal_pauses(frame_active, sample_rate_hz, hop_length),
                energy_track=track,
                limitation="Experimental signal-only F0 and RMS estimates; not validated for Turkish speech, emotion, speaker identity, or clinical/forensic use.",
            )
        except (TypeError, ValueError, FloatingPointError, OverflowError) as exc:
            raise ValueError("Prosody features could not be calculated from this audio.") from exc

    def _count_internal_pauses(self, active: list[bool], sample_rate_hz: int, hop_length: int) -> int:
        minimum_frames = max(1, math.ceil(self.config.minimum_pause_duration_seconds * sample_rate_hz / hop_length))
        count = 0
        index = 0
        while index < len(active):
            if active[index]:
                index += 1
                continue
            start = index
            while index < len(active) and not active[index]:
                index += 1
            end = index
            if start > 0 and end < len(active) and end - start >= minimum_frames:
                count += 1
        return count

    def _empty(self) -> ProsodySummary:
        return ProsodySummary(
            status="EXPERIMENTAL_DSP",
            estimator="windowed_autocorrelation_v1",
            median_f0_hz=None,
            p10_f0_hz=None,
            p90_f0_hz=None,
            voiced_frame_count=0,
            total_frame_count=0,
            voiced_frame_ratio=0.0,
            pause_count_estimate=0,
            energy_track=(),
            limitation="Experimental signal-only F0 and RMS estimates; not validated for Turkish speech, emotion, speaker identity, or clinical/forensic use.",
        )
