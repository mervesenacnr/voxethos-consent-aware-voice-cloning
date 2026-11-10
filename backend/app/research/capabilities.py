"""Public capability register; statuses distinguish implementation from plans."""

from app.schemas.research import CapabilityResponse


CAPABILITIES: dict[str, CapabilityResponse] = {
    "audio_validation": CapabilityResponse(status="IMPLEMENTED", description="PCM16 WAV parsing, bounded upload checks, signal-quality measurements, and format validation."),
    "speech_activity": CapabilityResponse(status="IMPLEMENTED_HEURISTIC", description="Deterministic energy/zero-crossing activity estimate; not speech recognition or a trained VAD."),
    "prosody": CapabilityResponse(status="EXPERIMENTAL_DSP", description="Signal-derived RMS and autocorrelation F0 estimates; requires validation on consented Turkish speech."),
    "turkish_asr": CapabilityResponse(status="NOT_IMPLEMENTED", description="No speech-to-text model is loaded or called."),
    "emotion_recognition": CapabilityResponse(status="NOT_IMPLEMENTED", description="No emotion labels or scores are produced."),
    "speaker_representation": CapabilityResponse(status="NOT_IMPLEMENTED", description="No speaker embedding, identity matching, or diarization is performed."),
    "privacy_evaluation": CapabilityResponse(status="NOT_IMPLEMENTED", description="No formal privacy attack, re-identification, or membership-inference evaluation is implemented."),
    "consent_management": CapabilityResponse(status="REQUEST_ACKNOWLEDGEMENT_ONLY", description="A per-request client attestation is required; identity, speaker consent, and legal rights are not verified or persistently recorded."),
    "voxedge": CapabilityResponse(status="PLANNED_NOT_LOADED", description="VoxEdge is the planned ML model family; no weights, inference, score, or prediction are present in this prototype."),
    "expressive_voice_generation": CapabilityResponse(status="NOT_IMPLEMENTED", description="No voice cloning or speech generation endpoint is available."),
}


def capability_snapshot() -> dict[str, CapabilityResponse]:
    """Return a copy so callers cannot mutate the shared capability register."""
    return {name: status.model_copy(deep=True) for name, status in CAPABILITIES.items()}
