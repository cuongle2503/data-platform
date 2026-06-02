"""Tests for chat router."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from idp.api.main import app


@pytest.fixture
def mock_rag_components():
    """Mock RAG components for chat endpoint."""
    with (
        patch("idp.api.routers.chat.normalize_query") as m_norm,
        patch("idp.api.routers.chat.extract_entities") as m_extract,
        patch("idp.api.routers.chat.build_context") as m_build,
    ):
        m_norm.return_value = "normalized query"
        m_extract.return_value = {"country_codes": ["VNM"], "years": [2023]}
        m_build.return_value = "Mocked Context"

        yield m_norm, m_extract, m_build


@pytest.fixture
def mock_dependencies():
    """Mock repository and RAG client."""
    mock_repo = Mock()
    mock_repo.search_indicators_lexical.return_value = [{"indicator_code": "TEST.1"}]
    mock_repo.get_indicator.return_value = {"indicator_code": "TEST.1", "indicator_name": "Test"}
    mock_repo.get_timeseries.return_value = [{"value": 100}]

    mock_rag = Mock()
    mock_rag.generate_answer.return_value = "Here is the answer [IND:TEST.1]"
    mock_rag.generate_answer_stream.return_value = ["Here is", " the answer", " [IND:TEST.1]"]

    return mock_repo, mock_rag


class TestChatRouter:
    """Integration tests for chat endpoints."""

    @pytest.fixture(autouse=True)
    def setup_router(self, mock_dependencies, mock_rag_components):
        """Register mock router before each test; remove after."""
        from idp.api.routers.chat import create_router

        mock_repo, mock_rag = mock_dependencies
        router = create_router(mock_repo, mock_rag)
        app.include_router(router, prefix="/api/v1")
        yield
        app.router.routes[:] = [
            r for r in app.router.routes if r.name not in ("chat_rest", "chat_websocket")
        ]

    def test_chat_rest(self, mock_dependencies, mock_rag_components):
        """Should return generated answer and citations."""
        # Act
        response = TestClient(app).post(
            "/api/v1/chat",
            json={"query": "What is the test?"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["answer"] == "Here is the answer [IND:TEST.1]"
        assert "TEST.1" in data["sources"]

    def test_chat_websocket(self, mock_dependencies, mock_rag_components):
        """Should stream tokens and citations via WebSocket."""
        client = TestClient(app)

        with client.websocket_connect("/api/v1/chat/ws") as websocket:
            # Send query
            websocket.send_json({"query": "Test query"})

            # Receive tokens
            msgs = []
            while True:
                data = websocket.receive_json()
                if "error" in data:
                    pytest.fail(f"WebSocket error: {data['error']}")
                msgs.append(data)
                # Break when we have 3 tokens and 1 citation (mocked)
                if len(msgs) >= 4:
                    break

        # Should contain token messages and a citation message
        token_msgs = [m for m in msgs if "token" in m]
        citation_msgs = [m for m in msgs if "indicator_code" in m]

        assert len(token_msgs) == 3
        assert len(citation_msgs) == 1
        assert citation_msgs[0]["indicator_code"] == "TEST.1"
