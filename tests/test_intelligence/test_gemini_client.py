"""Tests for Gemini RAG client."""

import os
from unittest.mock import Mock, patch

import pytest

from idp.intelligence.gemini_client import RAGClient


@pytest.fixture
def mock_genai():
    """Mock the genai module."""
    with patch("idp.intelligence.gemini_client.genai") as mock:
        mock_model = Mock()
        mock_model.generate_content.return_value.text = "Mocked answer [IND:NY.GDP]"
        mock.GenerativeModel.return_value = mock_model
        yield mock


class TestRAGClient:
    """Test RAG client interaction with Gemini."""

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    def test_generate_answer(self, mock_genai):
        """Should generate answer using context."""
        # Arrange
        client = RAGClient()
        query = "What is the GDP?"
        context = "NY.GDP is 100"

        # Act
        answer = client.generate_answer(query, context)

        # Assert
        assert answer == "Mocked answer [IND:NY.GDP]"
        mock_genai.GenerativeModel.return_value.generate_content.assert_called_once()
        call_args = mock_genai.GenerativeModel.return_value.generate_content.call_args[0][0]
        assert query in call_args
        assert context in call_args

    @patch.dict(os.environ, clear=True)
    def test_client_requires_api_key(self):
        """Should raise error if API key is missing."""
        # Arrange, Act & Assert
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            RAGClient()
