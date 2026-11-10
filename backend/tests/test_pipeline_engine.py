"""Ordered pipeline-engine tests retained for the research workflow."""
from datetime import datetime, timezone
from asyncio import run
from fastapi.testclient import TestClient
from app.core.context import PipelineContext
from app.core.engine import PipelineEngine
from app.core.stages import PIPELINE_EXECUTION_ORDER, PipelineStage
from app.core.status import PipelineStatus
from app.main import app
from audio_test_utils import make_non_silent_pcm16_wav


def context():
    return PipelineContext(session_id="test-request", created_at=datetime.now(timezone.utc))


async def mark(stage: PipelineStage, ctx: PipelineContext, calls: list[str]) -> None:
    calls.append(stage.value)
    ctx.metadata[stage.value] = "done"


def test_engine_runs_declared_research_stages_in_order():
    ctx = context()
    calls = []
    handlers = {stage: (lambda current, stage=stage: mark(stage, current, calls)) for stage in PIPELINE_EXECUTION_ORDER}
    result = run(PipelineEngine().execute(ctx, handlers))
    assert calls == [stage.value for stage in PIPELINE_EXECUTION_ORDER]
    assert result.status is PipelineStatus.COMPLETED
    assert ctx.current_stage is PipelineStage.COMPLETED


def test_engine_stops_after_a_failed_stage():
    ctx = context()
    calls = []
    async def fail(current: PipelineContext) -> None:
        calls.append("feature extraction")
        raise ValueError("failed")
    handlers = {stage: (lambda current, stage=stage: mark(stage, current, calls)) for stage in PIPELINE_EXECUTION_ORDER}
    handlers[PipelineStage.AUDIO_FEATURE_EXTRACTION] = fail
    result = run(PipelineEngine().execute(ctx, handlers))
    assert result.status is PipelineStatus.FAILED
    assert calls[-1] == "feature extraction"
    assert ctx.errors == ["failed"]


def test_http_analysis_returns_completed_pipeline_steps():
    response = TestClient(app).post("/api/v1/analyze", files={"audio": ("sample.wav", make_non_silent_pcm16_wav(), "audio/wav")}, data={"consent_acknowledged": "true"})
    assert response.status_code == 200
    body = response.json()
    assert [step["stage"] for step in body["pipeline"]] == [stage.value for stage in PIPELINE_EXECUTION_ORDER]
    assert all(step["status"] == "completed" for step in body["pipeline"])
