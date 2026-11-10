"""Honest API schema and OpenAPI tests."""
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.research import ResearchAnalysisResponse


def test_openapi_exposes_analysis_and_capabilities_routes():
    schema = TestClient(app).get("/openapi.json").json()
    assert "/api/v1/analyze" in schema["paths"]
    assert "/api/v1/capabilities" in schema["paths"]
    assert "ResearchAnalysisResponse" in schema["components"]["schemas"]
    assert "CapabilityCatalogResponse" in schema["components"]["schemas"]


def test_analysis_schema_has_no_prediction_or_embedding_fields():
    properties = ResearchAnalysisResponse.model_json_schema()["properties"]
    assert "prosody" in properties and "capabilities" in properties
    assert "model_plan" in properties
    assert "prediction" not in properties and "embedding" not in properties
