"""Core execution architecture for the platform pipeline."""

from .context import PipelineContext
from .engine import PipelineEngine
from .events import PipelineEvent
from .pipeline import PipelineExecutor, PipelineResult
from .stages import PIPELINE_EXECUTION_ORDER, PipelineStage
from .status import PipelineStatus

__all__ = [
    "PIPELINE_EXECUTION_ORDER", "PipelineContext", "PipelineEngine", "PipelineEvent",
    "PipelineExecutor", "PipelineResult", "PipelineStage", "PipelineStatus",
]
