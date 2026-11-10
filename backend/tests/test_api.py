"""Public API contract tests for the VoxEthos research prototype."""

from fastapi.testclient import TestClient

from audio_test_utils import make_non_silent_pcm16_wav as valid_wav
from app.main import app

client = TestClient(app)


def test_health_identifies_voxethos() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "VoxEthos"}


def test_analyze_requires_request_scoped_consent() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"audio": ("sample.wav", valid_wav(), "audio/wav")},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CONSENT_REQUIRED"


def test_analyze_returns_measured_features_not_model_predictions() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"audio": ("sample.wav", valid_wav(), "audio/wav")},
        data={"consent_acknowledged": "true"},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["project"] == "VoxEthos"
    assert result["prosody"]["status"] == "EXPERIMENTAL_DSP"
    assert result["model_plan"] == {
        "name": "VoxEdge",
        "status": "PLANNED_NOT_LOADED",
        "inference_performed": False,
    }
    assert "prediction" not in result and "spoof_probability" not in result
    assert result["privacy"]["raw_audio_persisted_by_application"] is False
