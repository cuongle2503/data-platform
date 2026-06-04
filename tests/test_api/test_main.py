"""Unit tests for FastAPI main app."""

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from idp.api.main import app


@pytest.fixture(autouse=True)
def _cleanup_routes() -> Generator[None, None, None]:
    """No-op: tests use fresh_app fixture instead of polluting global app routes."""
    yield


def test_health_check() -> None:
    """Test health check endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_cors_headers() -> None:
    """Test CORS headers are present (allow_origins='*' mirrors the Origin)."""
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_validation_error_handler(
    fresh_app: FastAPI,
) -> None:
    """Test custom validation error handler — uses isolated app to avoid route pollution."""
    from pydantic import BaseModel

    class Item(BaseModel):
        name: str

    @fresh_app.post("/test-validation")
    def test_route(item: Item) -> dict[str, str]:
        return item.model_dump()

    client = TestClient(fresh_app)
    response = client.post("/test-validation", json={})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_global_error_handler(
    fresh_app: FastAPI,
) -> None:
    """Test global unhandled exception handler — uses isolated app."""

    @fresh_app.get("/test-error")
    def test_error() -> None:
        raise RuntimeError("Something went wrong")

    client = TestClient(fresh_app, raise_server_exceptions=False)
    response = client.get("/test-error")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_ERROR"
