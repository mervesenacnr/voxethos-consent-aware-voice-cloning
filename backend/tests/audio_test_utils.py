"""Deterministic valid PCM16 WAV helpers for boundary-facing tests."""

import io
import wave


def make_pcm16_wav(frames: int = 1_600, amplitude: int = 8_000, sample_rate: int = 16_000) -> bytes:
    """Return deterministic mono PCM16 WAV with speech-like periodic activity."""
    import math
    values = bytearray()
    for index in range(frames):
        envelope = 0.65 + 0.35 * math.sin(2 * math.pi * index / max(1, sample_rate // 3))
        sample = amplitude * envelope * math.sin(2 * math.pi * 220 * index / sample_rate)
        values.extend(int(sample).to_bytes(2, "little", signed=True))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(bytes(values))
    return buffer.getvalue()


def make_non_silent_pcm16_wav(frames: int = 1_600) -> bytes:
    """Return bounded deterministic speech-like PCM16 activity."""
    return make_pcm16_wav(frames=frames)


def make_silent_pcm16_wav(frames: int = 1_600, sample_rate: int = 16_000) -> bytes:
    """Return a bounded deterministic silent PCM16 WAV."""
    return make_pcm16_wav(frames=frames, amplitude=0, sample_rate=sample_rate)
