from __future__ import annotations

from io import BytesIO
import wave

import numpy as np
from fastapi.testclient import TestClient

from app.api.dependencies import get_pipeline_engine
from app.main import app
from app.research.consent import ConsentManager
from app.research.prosody import ProsodyAnalyzer
from app.core.errors import AppError


def tone_samples(frequency_hz: float = 180.0, duration_seconds: float = 1.6, sample_rate_hz: int = 16_000) -> np.ndarray:
    time = np.arange(int(duration_seconds * sample_rate_hz), dtype=np.float32) / sample_rate_hz
    envelope = np.ones_like(time)
    envelope[int(0.55 * sample_rate_hz):int(0.75 * sample_rate_hz)] = 0.0
    signal = 0.20 * np.sin(2.0 * np.pi * frequency_hz * time) + 0.04 * np.sin(4.0 * np.pi * frequency_hz * time)
    return (signal * envelope).astype(np.float32)


def wav_bytes(samples: np.ndarray, sample_rate_hz: int = 16_000) -> bytes:
    pcm = np.clip(samples * 32767.0, -32768, 32767).astype("<i2")
    stream = BytesIO()
    with wave.open(stream, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate_hz)
        audio.writeframes(pcm.tobytes())
    return stream.getvalue()


def test_prosody_estimator_measures_pitch_from_signal_not_a_fixture() -> None:
    samples = tone_samples()
    result = ProsodyAnalyzer().analyze(samples, 16_000)

    assert result.status == "EXPERIMENTAL_DSP"
    assert result.median_f0_hz is not None
    assert abs(result.median_f0_hz - 180.0) < 8.0
    assert result.voiced_frame_count > 0
    assert result.energy_track
    assert all(np.isfinite(point.rms) for point in result.energy_track)
    assert result.pause_count_estimate >= 1


def test_unvoiced_signal_does_not_invent_pitch() -> None:
    result = ProsodyAnalyzer().analyze(np.zeros(16_000, dtype=np.float32), 16_000)
    assert result.median_f0_hz is None
    assert result.voiced_frame_count == 0


def test_consent_manager_requires_explicit_per_request_acknowledgement() -> None:
    manager = ConsentManager()
    try:
        manager.require_acknowledgement(False)
    except AppError as error:
        assert error.code == "CONSENT_REQUIRED"
        assert error.status_code == 403
    else:
        raise AssertionError("missing consent must be rejected")

    acknowledgement = manager.require_acknowledgement(True)
    assert acknowledgement.acknowledged is True
    assert acknowledgement.identity_or_rights_verified is False
    assert acknowledgement.persistent_record_created is False


def test_api_requires_consent_before_accepting_audio() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/analyze",
        files={"audio": ("voice.wav", wav_bytes(tone_samples()), "audio/wav")},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CONSENT_REQUIRED"


def test_api_returns_measured_features_and_marks_unfinished_ml() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/analyze",
        data={"consent_acknowledged": "true"},
        files={"audio": ("voice.wav", wav_bytes(tone_samples()), "audio/wav")},
    )
    assert response.status_code == 200, response.text
    result = response.json()

    assert result["project"] == "VoxEthos"
    assert result["audio_validation"]["encoding"] == "PCM16_LE"
    assert result["prosody"]["median_f0_hz"] is not None
    assert abs(result["prosody"]["median_f0_hz"] - 180.0) < 8.0
    assert result["model_plan"] == {"name": "VoxEdge", "status": "PLANNED_NOT_LOADED", "inference_performed": False}
    assert result["capabilities"]["emotion_recognition"]["status"] == "NOT_IMPLEMENTED"
    assert result["capabilities"]["speaker_representation"]["status"] == "NOT_IMPLEMENTED"
    assert result["capabilities"]["privacy_evaluation"]["status"] == "NOT_IMPLEMENTED"
    assert result["privacy"]["raw_audio_persisted_by_application"] is False
    assert result["consent"]["identity_or_rights_verified"] is False
    assert "spoof_probability" not in result
    assert "prediction" not in result


def test_research_api_does_not_retain_request_timeline() -> None:
    response = TestClient(app).post(
        "/api/v1/analyze",
        data={"consent_acknowledged": "true"},
        files={"audio": ("voice.wav", wav_bytes(tone_samples()), "audio/wav")},
    )

    assert response.status_code == 200
    analysis_id = response.json()["analysis_id"]
    assert analysis_id.startswith("ve_")
    assert get_pipeline_engine()._publisher is None



def test_capabilities_endpoint_describes_real_and_planned_work() -> None:
    response = TestClient(app).get("/api/v1/capabilities")
    assert response.status_code == 200
    capabilities = response.json()["capabilities"]
    assert capabilities["audio_validation"]["status"] == "IMPLEMENTED"
    assert capabilities["prosody"]["status"] == "EXPERIMENTAL_DSP"
    assert capabilities["voxedge"]["status"] == "PLANNED_NOT_LOADED"
