"""Reusable execution interfaces and results for the VoxEthos pipeline."""

from dataclasses import dataclass
from typing import Awaitable, Callable, Mapping, Protocol

from app.core.context import PipelineContext
from app.core.events import PipelineEvent
from app.core.stages import PIPELINE_EXECUTION_ORDER, PipelineStage
from app.core.status import PipelineStatus

StageHandler = Callable[[PipelineContext], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Immutable execution result exposing only ephemeral context and events."""

    context: PipelineContext
    events: tuple[PipelineEvent, ...]

    @property
    def status(self) -> PipelineStatus:
        return self.context.status

    @property
    def stages(self) -> tuple[str, ...]:
        completed = {event.stage for event in self.events if event.status == PipelineStatus.COMPLETED}
        return tuple(stage.value for stage in PIPELINE_EXECUTION_ORDER if stage in completed)


class PipelineExecutor(Protocol):
    """Protocol consumed by research services and future module adapters."""

    async def execute(
        self,
        context: PipelineContext,
        handlers: Mapping[PipelineStage, StageHandler],
        execution_order: tuple[PipelineStage, ...] = PIPELINE_EXECUTION_ORDER,
    ) -> PipelineResult:
        ...
