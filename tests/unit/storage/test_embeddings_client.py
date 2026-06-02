from unittest.mock import Mock, patch

import pytest

from idp.storage.embeddings_client import GeminiEmbeddingsClient


@pytest.fixture
def embeddings_client():
    with patch("idp.storage.embeddings_client.get_settings") as mock_settings:
        mock_settings.return_value.gemini.api_key = "fake_key"
        yield GeminiEmbeddingsClient()


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


@patch("idp.storage.embeddings_client.get_settings")
def test_client_fails_without_api_key(mock_settings):
    mock_settings.return_value.gemini.api_key = None
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiEmbeddingsClient()


@patch("idp.storage.embeddings_client.get_settings")
def test_can_pass_api_key_directly(mock_settings):
    """Constructor should prefer explicit api_key over config."""
    mock_settings.return_value.gemini.api_key = "from_env"
    client = GeminiEmbeddingsClient(api_key="explicit_key")
    assert client.api_key == "explicit_key"
    # Mock the genai calls to avoid side effects
    genai_mock = Mock()
    client._genai_model = genai_mock
