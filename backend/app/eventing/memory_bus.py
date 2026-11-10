"""Deterministic process-local event bus."""

from threading import RLock

from app.eventing.dispatch import dispatch_sequential
from app.eventing.envelope import EventEnvelope
from app.eventing.interfaces import DispatchResult, EventPublisher, EventSubscriber


class InMemoryEventBus(EventPublisher):
    """Publish envelopes sequentially to an idempotent subscriber registry."""

    def __init__(self) -> None:
        """Initialize an empty process-local subscriber registry."""
        self._subscribers: list[EventSubscriber] = []
        self._lock = RLock()

    def register(self, subscriber: EventSubscriber) -> None:
        """Register a subscriber once while preserving registration order."""
        with self._lock:
            if subscriber not in self._subscribers:
                self._subscribers.append(subscriber)

    def unregister(self, subscriber: EventSubscriber) -> bool:
        """Unregister a subscriber and report whether it was present."""
        with self._lock:
            if subscriber not in self._subscribers:
                return False
            self._subscribers.remove(subscriber)
            return True

    @property
    def subscriber_count(self) -> int:
        """Return the current subscriber count for diagnostics and tests."""
        with self._lock:
            return len(self._subscribers)

    async def publish(self, envelope: EventEnvelope) -> DispatchResult:
        """Deliver an envelope sequentially to a stable subscriber snapshot."""
        with self._lock:
            subscribers = tuple(self._subscribers)
        return await dispatch_sequential(envelope, subscribers)
