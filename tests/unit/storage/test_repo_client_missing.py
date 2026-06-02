from unittest.mock import MagicMock, patch

from idp.storage.embeddings_client import GeminiEmbeddingsClient
from idp.storage.repository import StorageRepository


def test_repo_get_country_not_found():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.fetchone.return_value = None

    repo = StorageRepository(conn)
    assert repo.get_country("UNKNOWN") is None


def test_repo_get_indicator_not_found():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.fetchone.return_value = None

    repo = StorageRepository(conn)
    assert repo.get_indicator("UNKNOWN") is None


@patch("idp.storage.embeddings_client.get_settings")
def test_client_empty_batch(mock_settings):
    mock_settings.return_value.gemini.api_key = "test-key"
    client = GeminiEmbeddingsClient()
    assert client.generate_embeddings_batch([]) == []
