"""Process-scoped pipeline provider without retained request timelines."""

from functools import lru_cache

from app.core.engine import PipelineEngine


@lru_cache(maxsize=1)
def get_pipeline_engine() -> PipelineEngine:
    """Return the shared stateless engine; request events stay request-scoped."""
    return PipelineEngine()
