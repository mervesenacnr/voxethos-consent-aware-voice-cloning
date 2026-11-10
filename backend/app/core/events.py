"""Immutable events emitted by the pipeline execution engine."""

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Mapping

from app.core.stages import PipelineStage
from app.core.status import PipelineStatus


@dataclass(frozen=True, slots=True)
class PipelineEvent:
    """Immutable record of one pipeline stage transition."""

    stage: PipelineStage
    status: PipelineStatus
    timestamp: datetime
    message: str
    duration_ms: int = 0
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Freeze metadata values at event construction time."""
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
