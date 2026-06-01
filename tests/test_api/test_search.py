"""Tests for the Search API router."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from idp.api.main import app


@pytest.fixture
def mock_repo():
    """Create a mock repository for search."""
    mock = Mock()
    mock.search_indicators_lexical.return_value = [
        {
            "indicator_code": "TEST.1",
            "indicator_name": "Test Indicator 1",
            "description": "A lexical match",
            "category": "Test",
        }
    ]
    mock.search_indicators_semantic.return_value = [
        {
            "indicator_code": "TEST.2",
            "indicator_name": "Test Indicator 2",
            "similarity": 0.85,
            "category": "Test",
        },
        {
            "indicator_code": "TEST.1",  # Overlap with lexical
            "indicator_name": "Test Indicator 1",
            "similarity": 0.75,
            "category": "Test",
        },
    ]
    return mock


@pytest.fixture
def mock_embeddings_client():
    """Create a mock embeddings client."""
    mock = Mock()
    mock.generate_embedding.return_value = [0.1] * 768
    return mock


class TestSearchRouter:
    """Integration tests for search endpoints."""

    @pytest.fixture(autouse=True)
    def setup_router(self, mock_repo, mock_embeddings_client):
        """Register mock router before each test; remove after."""
        from idp.api.routers.search import create_router

        router = create_router(mock_repo, mock_embeddings_client)
        app.include_router(router, prefix="/api/v1")
        yield
        app.router.routes[:] = [
            r for r in app.router.routes if r.name not in ("search_indicators",)
        ]

    def test_search_indicators(self, mock_repo, mock_embeddings_client):
        """Should combine and deduplicate lexical and semantic results."""
        # Act
        response = TestClient(app).get("/api/v1/search/indicators?q=test&limit=10")

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]

        # Expected:
        # TEST.2 (from semantic)
        # TEST.1 (combined from both, higher rank/score typically wins but deduplicated)
        assert len(data) == 2

        codes = [item["indicator_code"] for item in data]
        assert "TEST.1" in codes
        assert "TEST.2" in codes

        # Verify calls
        mock_repo.search_indicators_lexical.assert_called_once_with("test")
        mock_embeddings_client.generate_embedding.assert_called_once_with(
            "test", task_type="retrieval_query"
        )
        mock_repo.search_indicators_semantic.assert_called_once()
