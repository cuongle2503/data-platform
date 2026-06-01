import pytest
from unittest.mock import MagicMock
from idp.storage.repository import StorageRepository
from idp.storage.embeddings_client import GeminiEmbeddingsClient

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

def test_client_empty_batch():
    with pytest.MonkeyPatch.context() as m:
        m.setenv("GEMINI_API_KEY", "test-key")
        client = GeminiEmbeddingsClient()
        assert client.generate_embeddings_batch([]) == []
