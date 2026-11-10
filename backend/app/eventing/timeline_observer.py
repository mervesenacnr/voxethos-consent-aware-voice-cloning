"""Deterministic in-memory timeline observer."""

from threading import RLock
from typing import MutableMapping

from app.eventing.envelope import EventEnvelope


class TimelineObserver:
    """Group immutable event envelopes by session and preserve publication order."""

    def __init__(self) -> None:
        """Initialize an empty process-local timeline registry."""
        self._timelines: MutableMapping[str, list[EventEnvelope]] = {}
        self._lock = RLock()

    async def on_event(self, envelope: EventEnvelope) -> None:
        """Store an envelope without retaining PipelineContext or raw inputs."""
        with self._lock:
            self._timelines.setdefault(envelope.session_id, []).append(envelope)

    def events_for(self, session_id: str) -> tuple[EventEnvelope, ...]:
        """Return an immutable ordered timeline, or an empty tuple if unknown."""
        with self._lock:
            return tuple(self._timelines.get(session_id, ()))
