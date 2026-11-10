"""Sequential subscriber dispatch with isolated normal failures."""

from collections.abc import Sequence

from app.eventing.envelope import EventEnvelope
from app.eventing.interfaces import DispatchResult, EventSubscriber


async def dispatch_sequential(
    envelope: EventEnvelope,
    subscribers: Sequence[EventSubscriber],
) -> DispatchResult:
    """Deliver one envelope in registration order without swallowing BaseException."""
    successful = 0
    failures: list[str] = []
    for subscriber in subscribers:
        try:
            await subscriber.on_event(envelope)
        except Exception as exc:
            failures.append(f"{subscriber.__class__.__name__}: {exc.__class__.__name__}")
        else:
            successful += 1
    return DispatchResult(
        successful_deliveries=successful,
        failed_deliveries=len(failures),
        failure_summaries=tuple(failures),
    )
