from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI

from idp.api.main import app as main_app


@pytest.fixture
def fresh_app() -> FastAPI:
    """Return a fresh FastAPI app with same exception handlers as main_app."""
    from fastapi.middleware.cors import CORSMiddleware

    new_app = FastAPI(
        title=main_app.title,
        version=main_app.version,
    )
    new_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for exc_type, handler in main_app.exception_handlers.items():
        new_app.add_exception_handler(exc_type, handler)
    return new_app


@pytest.fixture
def test_data_dir() -> Path:
    """Return the path to the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock environment variables for testing."""
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "test_key")
    monkeypatch.setenv("MINIO_SECRET_KEY", "test_secret")
    monkeypatch.setenv("MINIO_BUCKET_BRONZE", "bronze")

    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "idp_test")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")

    monkeypatch.setenv("DUCKDB_PATH", ":memory:")

    monkeypatch.setenv("GEMINI_API_KEY", "test_api_key")


@pytest.fixture
def mock_gemini_client() -> MagicMock:
    """Return a Gemini client mock producing dummy 768-dim vectors."""
    mock = MagicMock()
    mock.generate_embeddings_batch.side_effect = lambda texts: [[0.1] * 768 for _ in texts]
    return mock
