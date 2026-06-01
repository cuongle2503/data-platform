import os
from unittest.mock import patch

import pytest

from idp.storage.embeddings_client import GeminiEmbeddingsClient


@pytest.fixture
def embeddings_client():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
        return GeminiEmbeddingsClient()


def test_embeddings_client_initialization(embeddings_client):
    assert embeddings_client.model_name == "models/text-embedding-004"


@patch("idp.storage.embeddings_client.genai.embed_content")
def test_generate_embedding_single(mock_embed, embeddings_client):
    # Arrange
    mock_response = {"embedding": [0.1, 0.2, 0.3]}
    mock_embed.return_value = mock_response

    # Act
    result = embeddings_client.generate_embedding("Test text")

    # Assert
    assert result == [0.1, 0.2, 0.3]
    mock_embed.assert_called_once_with(
        model="models/text-embedding-004", content="Test text", task_type="retrieval_document"
    )


@patch("idp.storage.embeddings_client.genai.embed_content")
def test_generate_embeddings_batch(mock_embed, embeddings_client):
    # Arrange
    mock_response = {"embedding": [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]}
    mock_embed.return_value = mock_response

    # Act
    texts = ["Text 1", "Text 2", "Text 3"]
    result = embeddings_client.generate_embeddings_batch(texts)

    # Assert
    assert result == [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
    mock_embed.assert_called_once()


def test_client_fails_without_api_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is required"):
            GeminiEmbeddingsClient()
