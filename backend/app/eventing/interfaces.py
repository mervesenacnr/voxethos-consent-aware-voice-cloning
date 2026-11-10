"""Framework-independent event delivery protocols and typed results."""

from dataclasses import dataclass
from typing import Protocol

from app.eventing.envelope import EventEnvelope


@dataclass(frozen=True, slots=True)
class DispatchResult:
    """Immutable summary of sequential subscriber deliveries."""

    successful_deliveries: int
    failed_deliveries: int
    failure_summaries: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate delivery counts and freeze failure summaries."""
        if self.successful_deliveries < 0 or self.failed_deliveries < 0:
            raise ValueError("Dispatch delivery counts cannot be negative.")
        object.__setattr__(self, "failure_summaries", tuple(self.failure_summaries))


class EventPublisher(Protocol):
    """Asynchronous boundary for publishing immutable event envelopes."""

    async def publish(self, envelope: EventEnvelope) -> DispatchResult:
        """Publish one envelope and return a typed delivery summary."""
        ...


class EventSubscriber(Protocol):
    """Asynchronous observer boundary for immutable event envelopes."""

    async def on_event(self, envelope: EventEnvelope) -> None:
        """Observe one envelope without receiving pipeline context."""
        ...
