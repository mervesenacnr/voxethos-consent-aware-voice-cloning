"""Dependency providers for the VoxEthos request-scoped research API."""

from functools import lru_cache

from app.api.dependencies import get_pipeline_engine
from app.research.service import ResearchAnalysisService
from app.services.upload_service import UploadService


@lru_cache(maxsize=1)
def get_upload_service() -> UploadService:
    return UploadService()


@lru_cache(maxsize=1)
def get_research_analysis_service() -> ResearchAnalysisService:
    return ResearchAnalysisService(engine=get_pipeline_engine())
