"""Deterministic technical quality metrics for normalized mono audio."""

import numpy as np

from app.audio.config import AudioInspectionConfig
from app.audio.errors import AudioMetricCalculationError
from app.audio.models import AudioQualityMetrics


def calculate_quality_metrics(samples: np.ndarray, sample_rate_hz: int, config: AudioInspectionConfig) -> AudioQualityMetrics:
    """Calculate exact full-resolution metrics in bounded chunks."""
    try:
        values = np.asarray(samples, dtype=np.float32)
        if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
            raise AudioMetricCalculationError("Audio samples are not finite.")
        if np.any(values > 1.0) or np.any(values < -1.0):
            raise AudioMetricCalculationError("Audio samples are outside the normalized range.")

        peak = 0.0
        square_sum = 0.0
        sample_sum = 0.0
        clipped_samples = 0
        crossings = 0
        previous_negative: bool | None = None
        chunk_size = config.metric_chunk_size
        for start in range(0, values.size, chunk_size):
            chunk = values[start:start + chunk_size]
            absolute = np.abs(chunk)
            peak = max(peak, float(np.max(absolute)))
            square_sum += float(np.sum(np.square(chunk, dtype=np.float64), dtype=np.float64))
            sample_sum += float(np.sum(chunk, dtype=np.float64))
            clipped_samples += int(np.count_nonzero(absolute >= config.clipping_amplitude_threshold))

            negative = chunk < 0
            if previous_negative is not None and bool(negative[0]) != previous_negative:
                crossings += 1
            if negative.size > 1:
                crossings += int(np.count_nonzero(negative[1:] != negative[:-1]))
            previous_negative = bool(negative[-1])

        rms = float(np.sqrt(square_sum / values.size))
        window_frames = max(1, int(round(sample_rate_hz * config.analysis_window_ms / 1000.0)))
        active = 0
        windows = 0
        for start in range(0, values.size, window_frames):
            window = values[start:start + window_frames]
            if window.size == 0:
                continue
            windows += 1
            window_rms = float(np.sqrt(np.mean(np.square(window), dtype=np.float64)))
            if window_rms > config.silence_rms_threshold:
                active += 1
        active_ratio = active / windows if windows else 0.0
        silence_ratio = 1.0 - active_ratio
        clipping = clipped_samples / values.size
        dc_offset = abs(sample_sum / values.size)
        zcr = crossings / max(1, values.size - 1)
        return AudioQualityMetrics(peak, rms, active_ratio, silence_ratio, clipping, min(1.0, dc_offset), min(1.0, zcr))
    except AudioMetricCalculationError:
        raise
    except (FloatingPointError, TypeError, ValueError, OverflowError) as exc:
        raise AudioMetricCalculationError("Audio metrics could not be calculated.") from exc
