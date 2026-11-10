"""Immutable envelopes for canonical pipeline events."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Mapping

from app.core.events import PipelineEvent


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    """Associate one canonical PipelineEvent with deterministic execution identity."""

    session_id: str
    event: PipelineEvent
    published_at: datetime
    sequence_number: int
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate identity and freeze metadata at construction time."""
        if not self.session_id:
            raise ValueError("Event envelope requires a session ID.")
        if self.published_at.tzinfo is None or self.published_at.utcoffset() != timedelta(0):
            raise ValueError("Event envelope published_at must be timezone-aware UTC.")
        if self.sequence_number < 0:
            raise ValueError("Event envelope sequence number cannot be negative.")
        object.__setattr__(self, "published_at", self.published_at.astimezone(timezone.utc))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
