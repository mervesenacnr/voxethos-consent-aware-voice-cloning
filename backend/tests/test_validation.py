"""Consent, validation, and request-boundary tests for the research API."""

from fastapi.testclient import TestClient

from audio_test_utils import make_non_silent_pcm16_wav as valid_wav
from app.main import app

client = TestClient(app)


def consent() -> dict[str, str]:
    return {"consent_acknowledged": "true"}


def test_empty_audio_returns_structured_error() -> None:
    response = client.post("/api/v1/analyze", files={"audio": ("empty.wav", b"", "audio/wav")}, data=consent())
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_AUDIO"


def test_unsupported_audio_returns_structured_error() -> None:
    response = client.post("/api/v1/analyze", files={"audio": ("sample.txt", b"not audio", "text/plain")}, data=consent())
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_AUDIO"


def test_valid_audio_returns_measured_research_contract() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"audio": ("sample.wav", valid_wav(), "audio/wav")},
        data=consent(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["project"] == "VoxEthos"
    assert body["audio_validation"]["encoding"] == "PCM16_LE"
    assert body["prosody"]["status"] == "EXPERIMENTAL_DSP"
    assert body["model_plan"]["status"] == "PLANNED_NOT_LOADED"
    assert "prediction" not in body


def test_oversized_audio_returns_structured_error() -> None:
    oversized = b"0" * (10 * 1024 * 1024 + 1)
    response = client.post("/api/v1/analyze", files={"audio": ("large.wav", oversized, "audio/wav")}, data=consent())
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "AUDIO_TOO_LARGE"
