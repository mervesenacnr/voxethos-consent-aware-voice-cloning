"""Health endpoint regression tests for the backend skeleton."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_typed_platform_status() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "VoxEthos"}


def test_openapi_schema_loads() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/health" in response.json()["paths"]
    assert "/api/v1/analyze" in response.json()["paths"]
