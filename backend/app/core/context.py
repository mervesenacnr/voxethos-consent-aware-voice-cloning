"""Minimal per-request context for bounded research analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from app.audio.models import AudioInspectionResult
from app.audio.speech import SpeechInspectionResult
from app.core.events import PipelineEvent
from app.core.stages import PipelineStage
from app.core.status import PipelineStatus
from app.research.prosody import ProsodySummary
from app.schemas.audio import AudioMetadata


@dataclass(slots=True)
class PipelineContext:
    """Ephemeral state passed between pipeline stages; raw data is never logged."""

    session_id: str
    created_at: datetime
    current_stage: PipelineStage = PipelineStage.VOICE_INPUT
    status: PipelineStatus = PipelineStatus.CREATED
    raw_payload: bytes | None = field(default=None, repr=False)
    audio_content_type: str | None = None
    audio_inspection: AudioInspectionResult | None = None
    speech_inspection: SpeechInspectionResult | None = None
    uploaded_audio: AudioMetadata | None = None
    decoded_samples: np.ndarray | None = field(default=None, repr=False)
    research_features: ProsodySummary | None = field(default=None, repr=False)
    metadata: dict[str, object] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    timeline: list[PipelineEvent] = field(default_factory=list)
