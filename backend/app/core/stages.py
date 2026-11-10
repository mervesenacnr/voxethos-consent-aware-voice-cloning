"""Stages supported by the current transparent audio-research workflow."""

from enum import StrEnum


class PipelineStage(StrEnum):
    VOICE_INPUT = "voice_input"
    VALIDATION = "validation"
    AUDIO_FEATURE_EXTRACTION = "audio_feature_extraction"
    RESEARCH_CAPABILITIES = "research_capabilities"
    COMPLETED = "completed"
    FAILED = "failed"


RESEARCH_PIPELINE_EXECUTION_ORDER: tuple[PipelineStage, ...] = (
    PipelineStage.VOICE_INPUT,
    PipelineStage.VALIDATION,
    PipelineStage.AUDIO_FEATURE_EXTRACTION,
    PipelineStage.RESEARCH_CAPABILITIES,
)
PIPELINE_EXECUTION_ORDER = RESEARCH_PIPELINE_EXECUTION_ORDER
