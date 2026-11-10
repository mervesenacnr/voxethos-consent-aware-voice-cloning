"""PCM16 WAV validation and quality-boundary tests."""

from __future__ import annotations

from io import BytesIO
import math
import wave

from typing import Any

import numpy as np
import pytest

from app.audio.config import AudioInspectionConfig
from app.audio.quality import calculate_quality_metrics
from app.audio.errors import (
    AudioConfigurationError,
    AudioResourceLimitError,
    EmptyWaveError,
    MalformedWaveError,
    NoMeasurableAudioSignalError,
    UnsupportedAudioContainerError,
    UnsupportedAudioEncodingError,
)
from app.audio.wav import Pcm16WavInspector


def make_wav(samples: np.ndarray, *, rate: int = 16_000, channels: int = 1, width: int = 2) -> bytes:
    values = np.asarray(samples, dtype=np.int16)
    buffer = BytesIO()
    with wave.open(buffer, "wb") as stream:
        stream.setnchannels(channels)
        stream.setsampwidth(width)
        stream.setframerate(rate)
        stream.writeframes(values.astype("<i2").tobytes())
    return buffer.getvalue()


def tone(frames: int = 16_000, amplitude: int = 7_000) -> np.ndarray:
    time = np.arange(frames, dtype=np.float32) / 16_000
    return (amplitude * np.sin(2 * np.pi * 180 * time)).astype(np.int16)


def inspector(config: AudioInspectionConfig | None = None) -> Pcm16WavInspector:
    return Pcm16WavInspector(config or AudioInspectionConfig())


@pytest.mark.parametrize("field,value", [("maximum_input_bytes", 0), ("maximum_channels", 0), ("maximum_duration_seconds", math.inf)])
def test_audio_limits_reject_invalid_configuration(field: str, value: Any) -> None:
    with pytest.raises(AudioConfigurationError):
        AudioInspectionConfig(**{field: value})


def test_valid_pcm16_mono_and_stereo_are_measured() -> None:
    mono = inspector().inspect(make_wav(tone()))
    stereo = np.column_stack((tone(), tone() // 2)).reshape(-1)
    stereo_result = inspector().inspect(make_wav(stereo, channels=2))
    assert mono.format.container == "RIFF/WAVE"
    assert mono.format.encoding == "PCM16_LE"
    assert mono.format.sample_rate_hz == 16_000
    assert mono.signal_present is True
    assert stereo_result.format.channels == 2
    assert stereo_result.signal_present is True


@pytest.mark.parametrize("payload", [b"not wave", b"RIFF", b"RIFFxxxxAVI "])
def test_invalid_container_or_signature_is_rejected(payload: bytes) -> None:
    with pytest.raises((UnsupportedAudioContainerError, MalformedWaveError)):
        inspector().inspect(payload)


def test_empty_and_truncated_wave_are_rejected() -> None:
    with pytest.raises(EmptyWaveError):
        inspector().inspect(b"")
    valid = make_wav(tone())
    with pytest.raises(MalformedWaveError):
        inspector().inspect(valid[:-3])


def test_non_pcm_encoding_is_rejected() -> None:
    payload = bytearray(make_wav(tone()))
    payload[20:22] = (6).to_bytes(2, "little")
    with pytest.raises(UnsupportedAudioEncodingError):
        inspector().inspect(bytes(payload))


def test_sample_rate_duration_and_size_limits_are_enforced() -> None:
    with pytest.raises(AudioResourceLimitError):
        inspector().inspect(make_wav(tone(), rate=192_000))
    small = AudioInspectionConfig(maximum_input_bytes=1024, maximum_decoded_frames=2_880_000)
    with pytest.raises(AudioResourceLimitError):
        Pcm16WavInspector(small).inspect(make_wav(tone()))


def test_silence_is_not_accepted_as_measurable_audio() -> None:
    with pytest.raises(NoMeasurableAudioSignalError):
        inspector().inspect(make_wav(np.zeros(16_000, dtype=np.int16)))


def test_quality_metrics_are_finite_and_bounded() -> None:
    values = tone()
    values[:80] = 32767
    result = inspector().inspect(make_wav(values))
    metrics = result.metrics
    assert math.isfinite(metrics.peak_amplitude)
    assert math.isfinite(metrics.rms_amplitude)
    assert 0 <= metrics.clipping_ratio <= 1
    assert 0 <= metrics.zero_crossing_rate <= 1


def test_quality_metrics_use_full_resolution_across_metric_chunk_boundaries() -> None:
    samples = np.full(1_000_001, 0.1, dtype=np.float32)
    samples[1] = 1.0
    samples[999_999] = -0.5
    samples[1_000_000] = 0.5

    metrics = calculate_quality_metrics(samples, 16_000, AudioInspectionConfig())

    assert metrics.peak_amplitude == pytest.approx(1.0)
    assert metrics.clipping_ratio == pytest.approx(1 / samples.size)
    assert metrics.zero_crossing_rate == pytest.approx(2 / (samples.size - 1))
