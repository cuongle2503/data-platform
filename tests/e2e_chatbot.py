"""End-to-end test for Phase 4 Intelligence Layer (Chatbot REST API).

Requires running PostgreSQL, Gemini API key, and populated data. Skip if unavailable.
"""

import logging
import os

import psycopg
import pytest
from fastapi.testclient import TestClient

from idp.api.main import create_app
from idp.intelligence.gemini_client import RAGClient
from idp.storage.embeddings_client import GeminiEmbeddingsClient
from idp.storage.repository import StorageRepository

logger = logging.getLogger(__name__)


@pytest.fixture
def repo():
    """Connect to real PostgreSQL and return a StorageRepository. Skip if unavailable."""
    db_host = os.environ.get("POSTGRES_HOST", "")
    if not db_host:
        pytest.skip("POSTGRES_HOST not set — skipping E2E chatbot test")

    conn = psycopg.connect(
        host=db_host,
        port=int(os.environ.get("POSTGRES_PORT", "5433")),
        dbname=os.environ.get("POSTGRES_DB", "idp"),
        user=os.environ.get("POSTGRES_USER", "idp_user"),
        password=os.environ.get("POSTGRES_PASSWORD", "changeme"),
    )
    repo = StorageRepository(conn)
    yield repo
    conn.close()


@pytest.fixture
def embeddings_client():
    """Create GeminiEmbeddingsClient, skip if API key missing."""
    from idp.common.config import get_settings

    if not get_settings().gemini.api_key:
        pytest.skip("GEMINI_API_KEY not set — skipping E2E embeddings client")
    return GeminiEmbeddingsClient()


@pytest.fixture
def rag_client():
    """Create RAGClient, skip if API key missing."""
    from idp.common.config import get_settings

    if not get_settings().gemini.api_key:
        pytest.skip("GEMINI_API_KEY not set — skipping E2E RAG client")
    return RAGClient()


@pytest.mark.slow
@pytest.mark.integration
def test_e2e_chatbot_rest(
    repo: StorageRepository,
    embeddings_client: GeminiEmbeddingsClient,
    rag_client: RAGClient,
) -> None:
    """Full RAG pipeline: semantic search → context build → LLM answer."""
    # Verify repository has data
    countries = repo.get_countries()
    indicators = repo.get_indicators()
    assert len(countries) > 0, "Expected at least one country in database"
    assert len(indicators) > 0, "Expected at least one indicator in database"
    logger.info("Repository: %d countries, %d indicators", len(countries), len(indicators))

    # Create app with all routers
    app = create_app(repo, embeddings_client, rag_client)
    client = TestClient(app)

    # Test chat endpoint
    query = "What is the GDP of Vietnam in 2023?"
    response = client.post("/api/v1/chat", json={"query": query, "max_indicators": 5})

    assert response.status_code == 200, f"Chat endpoint returned {response.status_code}"
    data = response.json()
    assert "data" in data, f"Response missing 'data' key: {data}"
    assert "answer" in data["data"], f"Response data missing 'answer': {data['data']}"
    answer = data["data"]["answer"]
    assert len(answer) > 0, "Expected non-empty answer from chat endpoint"
    logger.info("Chat answer: %s...", answer[:200])
