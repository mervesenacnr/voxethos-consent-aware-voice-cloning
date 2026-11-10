"""Phase 8 internal event delivery and timeline observation tests."""

from audio_test_utils import make_non_silent_pcm16_wav
import asyncio
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_pipeline_engine
from app.core.context import PipelineContext
from app.core.engine import PipelineEngine
from app.core.events import PipelineEvent
from app.core.pipeline import StageHandler
from app.core.stages import PIPELINE_EXECUTION_ORDER, PipelineStage
from app.core.status import PipelineStatus
from app.eventing.envelope import EventEnvelope
from app.eventing.interfaces import DispatchResult, EventSubscriber
from app.eventing.memory_bus import InMemoryEventBus
from app.eventing.timeline_observer import TimelineObserver
from app.main import app


def envelope(session_id: str = "session-1", sequence_number: int = 0) -> EventEnvelope:
    """Build a canonical event envelope for eventing tests."""
    return EventEnvelope(
        session_id=session_id,
        event=PipelineEvent(
            stage=PipelineStage.VOICE_INPUT,
            status=PipelineStatus.RUNNING,
            timestamp=datetime.now(timezone.utc),
            message="voice_input started",
        ),
        published_at=datetime.now(timezone.utc),
        sequence_number=sequence_number,
        metadata={"source": "test"},
    )


class RecordingSubscriber:
    """Subscriber that records deterministic delivery order."""

    def __init__(self, name: str, calls: list[str]) -> None:
        self.name = name
        self.calls = calls

    async def on_event(self, event: EventEnvelope) -> None:
        """Record the subscriber name and sequence number."""
        self.calls.append(f"{self.name}:{event.sequence_number}")


class FailingSubscriber:
    """Subscriber used to verify isolated normal exceptions."""

    async def on_event(self, event: EventEnvelope) -> None:
        """Raise a sanitized failure containing no useful payload."""
        del event
        raise RuntimeError("prompt=secret raw_audio=secret")


class InterruptingSubscriber:
    """Subscriber used to verify BaseException propagation."""

    def __init__(self, error: BaseException) -> None:
        self.error = error

    async def on_event(self, event: EventEnvelope) -> None:
        """Raise the configured non-Exception control-flow error."""
        del event
        raise self.error


def test_event_envelope_and_metadata_are_immutable() -> None:
    event = envelope()
    with pytest.raises(AttributeError):
        event.session_id = "changed"
    with pytest.raises(TypeError):
        event.metadata["changed"] = "value"
    assert event.event is not None
    assert event.sequence_number == 0
    assert event.published_at.utcoffset().total_seconds() == 0


def test_bus_registration_delivery_order_and_duplicate_prevention() -> None:
    calls: list[str] = []
    first = RecordingSubscriber("first", calls)
    second = RecordingSubscriber("second", calls)
    bus = InMemoryEventBus()
    bus.register(first)
    bus.register(second)
    bus.register(first)
    result = asyncio.run(bus.publish(envelope(sequence_number=4)))
    assert calls == ["first:4", "second:4"]
    assert result == DispatchResult(successful_deliveries=2, failed_deliveries=0)
    assert bus.subscriber_count == 2


def test_bus_unregistration_is_deterministic() -> None:
    calls: list[str] = []
    subscriber = RecordingSubscriber("one", calls)
    bus = InMemoryEventBus()
    bus.register(subscriber)
    assert bus.unregister(subscriber) is True
    assert bus.unregister(subscriber) is False
    result = asyncio.run(bus.publish(envelope()))
    assert calls == []
    assert result.successful_deliveries == 0


def test_failing_subscriber_does_not_block_later_delivery() -> None:
    calls: list[str] = []
    bus = InMemoryEventBus()
    bus.register(FailingSubscriber())
    bus.register(RecordingSubscriber("later", calls))
    result = asyncio.run(bus.publish(envelope()))
    assert calls == ["later:0"]
    assert result.successful_deliveries == 1
    assert result.failed_deliveries == 1
    assert len(result.failure_summaries) == 1
    assert "RuntimeError" in result.failure_summaries[0]
    assert "secret" not in result.failure_summaries[0]


@pytest.mark.parametrize("error", [KeyboardInterrupt(), SystemExit(2)])
def test_control_flow_exceptions_are_not_swallowed(error: BaseException) -> None:
    bus = InMemoryEventBus()
    bus.register(InterruptingSubscriber(error))
    with pytest.raises(type(error)):
        asyncio.run(bus.publish(envelope()))


def test_timeline_observer_groups_and_orders_immutable_envelopes() -> None:
    observer = TimelineObserver()
    first = envelope("session-a", 2)
    second = envelope("session-a", 3)
    other = envelope("session-b", 0)
    asyncio.run(observer.on_event(first))
    asyncio.run(observer.on_event(second))
    asyncio.run(observer.on_event(other))
    timeline = observer.events_for("session-a")
    assert isinstance(timeline, tuple)
    assert [item.sequence_number for item in timeline] == [2, 3]
    assert observer.events_for("unknown") == ()
    assert b"raw" not in repr(timeline).encode()
    assert "prompt" not in repr(timeline)


def engine_handlers() -> dict[PipelineStage, StageHandler]:
    """Build no-op handlers for engine publication tests."""
    async def handle(context: PipelineContext) -> None:
        """Mutate only typed test metadata."""
        context.metadata[context.current_stage.value] = "done"

    return {stage: handle for stage in PIPELINE_EXECUTION_ORDER}


def test_engine_works_without_publisher_and_publishes_canonical_events() -> None:
    context_without = PipelineContext(session_id="without", created_at=datetime.now(timezone.utc))
    direct = asyncio.run(PipelineEngine().execute(context_without, engine_handlers()))
    observer = TimelineObserver()
    bus = InMemoryEventBus()
    bus.register(observer)
    context_with = PipelineContext(session_id="with", created_at=datetime.now(timezone.utc))
    published = asyncio.run(PipelineEngine(publisher=bus).execute(context_with, engine_handlers()))
    observed = observer.events_for("with")
    assert len(observed) == len(published.events) == len(direct.events)
    assert [item.sequence_number for item in observed] == list(range(len(observed)))
    assert [(item.stage, item.status, item.message) for item in published.events] == [
        (item.stage, item.status, item.message) for item in direct.events
    ]
    assert all(item.event is published.events[index] for index, item in enumerate(observed))


def test_pipeline_engine_provider_is_a_singleton() -> None:
    assert get_pipeline_engine() is get_pipeline_engine()


def test_public_api_is_request_scoped_and_does_not_return_demo_scores() -> None:
    response = TestClient(app).post(
        "/api/v1/analyze",
        files={"audio": ("sample.wav", make_non_silent_pcm16_wav(), "audio/wav")},
        data={"consent_acknowledged": "true"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["project"] == "VoxEthos"
    assert body["privacy"]["raw_audio_persisted_by_application"] is False
    assert "prediction" not in body and "similarity" not in body
