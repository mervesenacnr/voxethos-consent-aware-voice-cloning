"""Consent-gated research audio routes."""

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.research_dependencies import get_research_analysis_service, get_upload_service
from app.core.errors import AppError
from app.research.capabilities import capability_snapshot
from app.research.consent import ConsentManager
from app.research.service import ResearchAnalysisService
from app.schemas.research import CapabilityCatalogResponse, ResearchAnalysisResponse
from app.services.upload_service import UploadService

router = APIRouter(prefix="/api/v1", tags=["research"])


@router.get("/capabilities", response_model=CapabilityCatalogResponse)
def capabilities() -> CapabilityCatalogResponse:
    """Describe implemented signal processing and unfinished research work."""
    return CapabilityCatalogResponse(capabilities=capability_snapshot())


@router.post("/analyze", response_model=ResearchAnalysisResponse)
async def analyze(
    audio: UploadFile = File(...),
    consent_acknowledged: bool = Form(False),
    upload_service: UploadService = Depends(get_upload_service),
    service: ResearchAnalysisService = Depends(get_research_analysis_service),
) -> ResearchAnalysisResponse:
    """Require an explicit per-request acknowledgement before reading audio."""
    consent = ConsentManager().require_acknowledgement(consent_acknowledged)
    payload, content_type = await upload_service.read_bounded_payload(audio)
    return await service.analyze(payload, content_type, consent)
