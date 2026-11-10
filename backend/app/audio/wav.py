"""Authoritative standard-library PCM16 WAV inspector."""

from io import BytesIO
import wave
from typing import Protocol

import numpy as np

from app.audio.config import AudioInspectionConfig
from app.audio.errors import (
    AudioResourceLimitError,
    EmptyWaveError,
    MalformedWaveError,
    NoMeasurableAudioSignalError,
    UnsupportedAudioContainerError,
    UnsupportedAudioEncodingError,
    AudioMetricCalculationError,
)
from app.audio.models import AudioFormatMetadata, AudioInspectionResult, TechnicalQualityStatus
from app.audio.quality import calculate_quality_metrics


class AudioInspectionPolicy(Protocol):
    def inspect(self, payload: bytes) -> AudioInspectionResult:
        """Inspect one bounded upload and return immutable technical evidence."""
        ...


class Pcm16WavInspector:
    """Inspect RIFF/WAVE uncompressed little-endian PCM16 bytes exactly once."""

    def __init__(self, config: AudioInspectionConfig) -> None:
        self.config = config

    def inspect(self, payload: bytes) -> AudioInspectionResult:
        result, _ = self._inspect(payload, None)
        return result

    def inspect_with_samples(self, payload: bytes, analyzer) -> tuple[AudioInspectionResult, object]:
        """Inspect once and consume transient decoded samples after technical validation."""
        return self._inspect(payload, analyzer)

    def _inspect(self, payload: bytes, analyzer) -> tuple[AudioInspectionResult, object]:
        if not isinstance(payload, bytes) or not payload:
            raise EmptyWaveError("Audio payload is empty.")
        if len(payload) > self.config.maximum_input_bytes:
            raise AudioResourceLimitError("Audio payload exceeds the configured input limit.")
        if payload[:4] != b"RIFF" or payload[8:12] != b"WAVE":
            raise UnsupportedAudioContainerError("Only RIFF/WAVE audio is supported.")
        if payload[12:16] == b"fmt " and len(payload) >= 22 and int.from_bytes(payload[20:22], "little") != 1:
            raise UnsupportedAudioEncodingError("Only uncompressed PCM audio is supported.")
        try:
            with wave.open(BytesIO(payload), "rb") as handle:
                if handle.getcomptype() != "NONE":
                    raise UnsupportedAudioEncodingError("Only uncompressed PCM audio is supported.")
                channels = handle.getnchannels()
                sample_width = handle.getsampwidth()
                rate = handle.getframerate()
                frames = handle.getnframes()
                if sample_width != 2:
                    raise UnsupportedAudioEncodingError("Only PCM16 audio is supported.")
                if channels <= 0 or channels > self.config.maximum_channels:
                    raise UnsupportedAudioEncodingError("Audio channel count is outside the supported limit.")
                if rate < self.config.minimum_sample_rate_hz or rate > self.config.maximum_sample_rate_hz:
                    raise AudioResourceLimitError("Audio sample rate is outside the configured range.")
                if frames <= 0:
                    raise EmptyWaveError("WAV contains no audio frames.")
                duration = frames / rate
                if frames > self.config.maximum_decoded_frames or duration > self.config.maximum_duration_seconds:
                    raise AudioResourceLimitError("Audio duration exceeds the configured limit.")
                raw = handle.readframes(frames)
                expected = frames * channels * sample_width
                if len(raw) != expected:
                    raise MalformedWaveError("WAV frame payload is truncated.")
        except (UnsupportedAudioContainerError, UnsupportedAudioEncodingError, AudioResourceLimitError, EmptyWaveError, MalformedWaveError):
            raise
        except (EOFError, RuntimeError, ValueError, wave.Error) as exc:
            raise MalformedWaveError("WAV content is malformed.") from exc
        try:
            interleaved = np.frombuffer(raw, dtype="<i2")
            if interleaved.size != frames * channels:
                raise MalformedWaveError("WAV frame payload is malformed.")
            frame_values = interleaved.reshape(frames, channels).astype(np.float32) / 32768.0
            samples = frame_values.mean(axis=1, dtype=np.float32) if channels == 2 else frame_values[:, 0]
            metrics = calculate_quality_metrics(samples, rate, self.config)
        except (MalformedWaveError, AudioMetricCalculationError):
            raise
        except Exception as exc:
            raise MalformedWaveError("PCM16 samples could not be decoded.") from exc
        signal_present = metrics.rms_amplitude > self.config.silence_rms_threshold and metrics.active_window_ratio >= self.config.minimum_active_window_ratio
        reasons: list[str] = []
        if metrics.clipping_ratio > self.config.maximum_acceptable_clipping_ratio:
            reasons.append("EXCESSIVE_CLIPPING")
        if metrics.dc_offset > self.config.maximum_acceptable_dc_offset:
            reasons.append("EXCESSIVE_DC_OFFSET")
        if signal_present and metrics.active_window_ratio < max(self.config.minimum_active_window_ratio, 0.5):
            reasons.append("LOW_ACTIVE_AUDIO_RATIO")
        status = TechnicalQualityStatus.DEGRADED if reasons else TechnicalQualityStatus.ACCEPTABLE
        result = AudioInspectionResult(
            format=AudioFormatMetadata("RIFF/WAVE", "PCM16_LE", rate, channels, 2, frames, duration),
            metrics=metrics,
            signal_present=signal_present,
            technical_quality_status=status,
            reason_codes=tuple(reasons),
        )
        if not signal_present:
            raise NoMeasurableAudioSignalError("Audio does not contain a measurable signal.")
        speech_result = None if analyzer is None else analyzer(samples, rate)
        return result, speech_result
