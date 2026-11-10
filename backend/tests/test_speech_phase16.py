"""Deterministic activity-estimator tests; this is not ASR or a trained VAD."""
import numpy as np
from fastapi.testclient import TestClient

from app.audio.speech import DeterministicSpeechAnalyzer, SpeechAnalysisConfig
from app.main import app
from audio_test_utils import make_non_silent_pcm16_wav


def test_signal_activity_uses_threshold_status_not_a_speech_classification():
    t = np.arange(16_000, dtype=np.float32) / 16_000
    tone = (0.2 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    result = DeterministicSpeechAnalyzer(SpeechAnalysisConfig()).analyze(tone, 16_000)
    assert result.status.value == "ACTIVITY_PRESENT"
    assert result.active_frame_count > 0


def test_api_labels_unfinished_asr_and_activity_heuristic():
    response = TestClient(app).post(
        "/api/v1/analyze",
        files={"audio": ("synthetic.wav", make_non_silent_pcm16_wav(), "audio/wav")},
        data={"consent_acknowledged": "true"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["speech_activity"]["status"] == "ACTIVITY_PRESENT"
    assert body["speech_activity"]["estimator"] == "energy_and_zero_crossing_heuristic"
    assert body["capabilities"]["turkish_asr"]["status"] == "NOT_IMPLEMENTED"
    assert "prediction" not in body
