"""Tests for Gemini RAG client."""

from unittest.mock import Mock, patch

import pytest

from idp.intelligence.gemini_client import RAGClient


class TestRAGClient:
    """Test RAG client interaction with Gemini."""

    @patch("idp.intelligence.gemini_client.genai")
    @patch("idp.intelligence.gemini_client.get_settings")
    def test_generate_answer(self, mock_settings, mock_genai):
        """Should generate answer using context."""
        # Arrange
        mock_settings.return_value.gemini.api_key = "test_key"
        mock_model = Mock()
        mock_model.generate_content.return_value.text = "Mocked answer [IND:NY.GDP]"
        mock_genai.GenerativeModel.return_value = mock_model

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

    @patch("idp.intelligence.gemini_client.get_settings")
    def test_client_requires_api_key(self, mock_settings):
        """Should raise error if API key is missing."""
        # Arrange
        mock_settings.return_value.gemini.api_key = None

        # Act & Assert
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            RAGClient()
