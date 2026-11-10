"""Honest API contracts for the VoxEthos research prototype."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AudioValidationResponse(BaseModel):
    container: str
    encoding: str
    sample_rate_hz: int = Field(ge=1)
    channels: int = Field(ge=1)
    frame_count: int = Field(ge=1)
    duration_seconds: float = Field(gt=0)
    technical_quality_status: str
    signal_present: bool
    peak_amplitude: float = Field(ge=0, le=1)
    rms_amplitude: float = Field(ge=0, le=1)
    active_window_ratio: float = Field(ge=0, le=1)
    silence_window_ratio: float = Field(ge=0, le=1)
    clipping_ratio: float = Field(ge=0, le=1)
    dc_offset: float = Field(ge=0, le=1)
    zero_crossing_rate: float = Field(ge=0, le=1)
    reason_codes: list[str]


class SpeechSegmentResponse(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    duration_seconds: float = Field(gt=0)


class SpeechActivityResponse(BaseModel):
    status: Literal["ACTIVITY_PRESENT", "INSUFFICIENT_ACTIVITY", "NO_ACTIVITY", "NOT_EVALUATED"]
    estimator: Literal["energy_and_zero_crossing_heuristic"]
    total_frame_count: int = Field(ge=0)
    active_frame_count: int = Field(ge=0)
    active_ratio: float = Field(ge=0, le=1)
    estimated_duration_seconds: float = Field(ge=0)
    segments: list[SpeechSegmentResponse]
    limitation: str


class ProsodyPointResponse(BaseModel):
    time_seconds: float = Field(ge=0)
    rms: float = Field(ge=0, le=1)
    f0_hz: float | None = Field(default=None, gt=0)


class ProsodyResponse(BaseModel):
    status: Literal["EXPERIMENTAL_DSP"]
    estimator: Literal["windowed_autocorrelation_v1"]
    median_f0_hz: float | None = Field(default=None, gt=0)
    p10_f0_hz: float | None = Field(default=None, gt=0)
    p90_f0_hz: float | None = Field(default=None, gt=0)
    voiced_frame_count: int = Field(ge=0)
    total_frame_count: int = Field(ge=0)
    voiced_frame_ratio: float = Field(ge=0, le=1)
    pause_count_estimate: int = Field(ge=0)
    energy_track: list[ProsodyPointResponse]
    limitation: str


class CapabilityResponse(BaseModel):
    status: str
    description: str


class ModelPlanResponse(BaseModel):
    name: Literal["VoxEdge"] = "VoxEdge"
    status: Literal["PLANNED_NOT_LOADED"] = "PLANNED_NOT_LOADED"
    inference_performed: Literal[False] = False


class ConsentResponse(BaseModel):
    acknowledged: Literal[True] = True
    version: str
    scope: str
    acknowledged_at: datetime
    identity_or_rights_verified: Literal[False] = False
    persistent_record_created: Literal[False] = False
    limitation: str


class PrivacyResponse(BaseModel):
    raw_audio_persisted_by_application: Literal[False] = False
    processing_scope: Literal["REQUEST_SCOPED"] = "REQUEST_SCOPED"
    formal_privacy_evaluation: Literal["NOT_IMPLEMENTED"] = "NOT_IMPLEMENTED"
    limitation: str


class PipelineStepResponse(BaseModel):
    stage: str
    status: str
    duration_ms: int = Field(ge=0)


class ResearchAnalysisResponse(BaseModel):
    project: Literal["VoxEthos"] = "VoxEthos"
    analysis_id: str
    created_at: datetime
    processing_ms: int = Field(ge=0)
    audio_validation: AudioValidationResponse
    speech_activity: SpeechActivityResponse
    prosody: ProsodyResponse
    capabilities: dict[str, CapabilityResponse]
    model_plan: ModelPlanResponse = Field(default_factory=ModelPlanResponse)
    privacy: PrivacyResponse
    consent: ConsentResponse
    pipeline: list[PipelineStepResponse]


class CapabilityCatalogResponse(BaseModel):
    project: Literal["VoxEthos"] = "VoxEthos"
    capabilities: dict[str, CapabilityResponse]
