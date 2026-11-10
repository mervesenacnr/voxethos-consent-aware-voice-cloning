"""Framework-independent pipeline execution engine."""

from datetime import datetime, timezone
from time import perf_counter
from typing import Mapping

from app.core.context import PipelineContext
from app.core.events import PipelineEvent
from app.core.pipeline import PipelineExecutor, PipelineResult, StageHandler
from app.core.stages import PIPELINE_EXECUTION_ORDER, PipelineStage
from app.core.status import PipelineStatus
from app.eventing.envelope import EventEnvelope
from app.eventing.interfaces import EventPublisher


class PipelineEngine(PipelineExecutor):
    """Execute ordered handlers and optionally publish canonical pipeline events."""

    def __init__(self, publisher: EventPublisher | None = None) -> None:
        """Configure an optional observational event publisher."""
        self._publisher = publisher

    async def execute(
        self,
        context: PipelineContext,
        handlers: Mapping[PipelineStage, StageHandler],
        execution_order: tuple[PipelineStage, ...] = PIPELINE_EXECUTION_ORDER,
    ) -> PipelineResult:
        """Run a selected ordered workflow and return deterministic execution state."""
        context.status = PipelineStatus.READY
        context.status = PipelineStatus.RUNNING
        sequence_number = 0
        for stage in execution_order:
            context.current_stage = stage
            started = perf_counter()
            sequence_number = await self._emit(
                context, stage, PipelineStatus.RUNNING, f"{stage.value} started", sequence_number,
            )
            handler = handlers.get(stage)
            if handler is None:
                return await self._fail(context, stage, f"No handler registered for {stage.value}.", started, sequence_number)
            try:
                await handler(context)
            except Exception as exc:  # pragma: no cover - exact exception is covered through failure tests
                return await self._fail(context, stage, str(exc) or exc.__class__.__name__, started, sequence_number)
            sequence_number = await self._emit(
                context,
                stage,
                PipelineStatus.COMPLETED,
                f"{stage.value} completed",
                sequence_number,
                duration_ms=max(0, int((perf_counter() - started) * 1000)),
            )
        context.current_stage = PipelineStage.COMPLETED
        context.status = PipelineStatus.COMPLETED
        await self._emit(context, PipelineStage.COMPLETED, PipelineStatus.COMPLETED, "Pipeline completed", sequence_number)
        return PipelineResult(context=context, events=tuple(context.timeline))

    async def _emit(
        self,
        context: PipelineContext,
        stage: PipelineStage,
        status: PipelineStatus,
        message: str,
        sequence_number: int,
        duration_ms: int = 0,
        metadata: Mapping[str, object] | None = None,
    ) -> int:
        """Create one canonical event, retain it, and publish the same event."""
        event = PipelineEvent(
            stage=stage,
            status=status,
            timestamp=datetime.now(timezone.utc),
            message=message,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
        context.timeline.append(event)
        if self._publisher is not None:
            envelope = EventEnvelope(
                session_id=context.session_id,
                event=event,
                published_at=datetime.now(timezone.utc),
                sequence_number=sequence_number,
            )
            try:
                await self._publisher.publish(envelope)
            except Exception:
                # Event delivery is observational and must not alter pipeline execution.
                pass
        return sequence_number + 1

    async def _fail(
        self,
        context: PipelineContext,
        stage: PipelineStage,
        message: str,
        started: float,
        sequence_number: int,
    ) -> PipelineResult:
        """Mark execution failed, publish terminal events, and stop further stages."""
        context.status = PipelineStatus.FAILED
        context.current_stage = PipelineStage.FAILED
        context.errors.append(message)
        sequence_number = await self._emit(
            context,
            stage,
            PipelineStatus.FAILED,
            message,
            sequence_number,
            duration_ms=max(0, int((perf_counter() - started) * 1000)),
        )
        await self._emit(context, PipelineStage.FAILED, PipelineStatus.FAILED, "Pipeline failed", sequence_number)
        return PipelineResult(context=context, events=tuple(context.timeline))
