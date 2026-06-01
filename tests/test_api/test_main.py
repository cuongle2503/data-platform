"""Unit tests for FastAPI main app."""

from fastapi.testclient import TestClient

from idp.api.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_cors_headers():
    """Test CORS headers are present (allow_origins='*' mirrors the Origin)."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    # When allow_origins=["*"], CORSMiddleware echoes the Origin back
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_validation_error_handler():
    """Test custom validation error handler."""
    # Create a temporary route that requires validation
    from pydantic import BaseModel

    class Item(BaseModel):
        name: str

    @app.post("/test-validation")
    def test_route(item: Item):
        return item

    # Try with missing required field
    response = client.post("/test-validation", json={})

    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_global_error_handler():
    """Test global unhandled exception handler."""

    # Create a temporary route that raises an exception
    @app.get("/test-error")
    def test_error():
        raise RuntimeError("Something went wrong")

    # TestClient raises the exception by default; we need to catch it
    # or use raise_server_exceptions=False
    test_client_no_raise = TestClient(app, raise_server_exceptions=False)
    response = test_client_no_raise.get("/test-error")

    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_ERROR"
