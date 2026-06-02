"""Unit tests for document embeddings generation."""

from unittest.mock import MagicMock, Mock, patch

import polars as pl
import pytest

from idp.storage.generate_doc_embeddings import (
    _process_chunk_batch,
    build_chunk_text,
    generate_doc_embeddings,
    get_existing_chunk_ref_ids,
    run,
)


def test_build_chunk_text_with_full_data():
    # Arrange
    row = {
        "chunk_id": "doc123_0001",
        "doc_id": "doc123",
        "text": "This is the content of the chunk.",
        "chunk_index": 0,
        "total_chunks": 5,
    }

    # Act
    result = build_chunk_text(row)

    # Assert
    assert "Document ID: doc123" in result
    assert "Chunk: 1/5" in result
    assert "Content: This is the content of the chunk." in result


def test_build_chunk_text_with_missing_fields():
    # Arrange
    row = {
        "text": "Some text",
    }

    # Act
    result = build_chunk_text(row)

    # Assert
    assert "Document ID: unknown" in result
    assert "Chunk: 1/1" in result
    assert "Content: Some text" in result


def test_get_existing_chunk_ref_ids_returns_set():
    # Arrange
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("doc123_0001",),
        ("doc456_0002",),
    ]

    # Act
    result = get_existing_chunk_ref_ids(mock_cursor)

    # Assert
    assert result == {"doc123_0001", "doc456_0002"}
    mock_cursor.execute.assert_called_once()


def test_get_existing_chunk_ref_ids_returns_empty_set():
    # Arrange
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []

    # Act
    result = get_existing_chunk_ref_ids(mock_cursor)

    # Assert
    assert result == set()


def test_generate_doc_embeddings_no_files():
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor

    mock_client = MagicMock()
    mock_minio = MagicMock()
    mock_minio.list_objects.return_value = []

    # Act
    result = generate_doc_embeddings(mock_conn, mock_client, mock_minio)

    # Assert
    assert result == 0


def test_generate_doc_embeddings_with_chunks():
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []  # No existing embeddings
    mock_conn.cursor.return_value = mock_cursor

    mock_client = MagicMock()
    mock_client.generate_embeddings_batch.return_value = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]

    mock_minio = MagicMock()
    mock_minio.list_objects.return_value = ["world_bank/docs/chunks/file1.parquet"]

    # Create mock dataframe
    df = pl.DataFrame(
        {
            "chunk_id": ["doc1_0001", "doc1_0002"],
            "doc_id": ["doc1", "doc1"],
            "text": ["First chunk text", "Second chunk text"],
            "chunk_index": [0, 1],
            "total_chunks": [2, 2],
            "char_count": [16, 17],
            "source": ["world_bank_wds_api", "world_bank_wds_api"],
        }
    )
    mock_minio.read_dataframe.return_value = df

    # Act
    result = generate_doc_embeddings(mock_conn, mock_client, mock_minio, batch_size=5)

    # Assert
    assert result == 2
    assert mock_cursor.execute.call_count >= 2  # At least 2 inserts
    mock_conn.commit.assert_called()


def test_generate_doc_embeddings_skips_existing():
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Existing embedding for doc1_0001
    mock_cursor.fetchall.return_value = [("doc1_0001",)]
    mock_conn.cursor.return_value = mock_cursor

    mock_client = MagicMock()
    mock_client.generate_embeddings_batch.return_value = [[0.1, 0.2, 0.3]]

    mock_minio = MagicMock()
    mock_minio.list_objects.return_value = ["world_bank/docs/chunks/file1.parquet"]

    df = pl.DataFrame(
        {
            "chunk_id": ["doc1_0001", "doc1_0002"],
            "doc_id": ["doc1", "doc1"],
            "text": ["First chunk", "Second chunk"],
            "chunk_index": [0, 1],
            "total_chunks": [2, 2],
            "char_count": [11, 12],
            "source": ["world_bank_wds_api", "world_bank_wds_api"],
        }
    )
    mock_minio.read_dataframe.return_value = df

    # Act
    result = generate_doc_embeddings(mock_conn, mock_client, mock_minio, batch_size=5)

    # Assert
    assert result == 1  # Only doc1_0002 should be embedded
    # Should only call generate_embeddings_batch once with 1 text
    mock_client.generate_embeddings_batch.assert_called_once()
    call_args = mock_client.generate_embeddings_batch.call_args[0][0]
    assert len(call_args) == 1


def test_generate_doc_embeddings_handles_read_error():
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor

    mock_client = MagicMock()
    mock_minio = MagicMock()
    mock_minio.list_objects.return_value = ["world_bank/docs/chunks/bad_file.parquet"]
    mock_minio.read_dataframe.side_effect = Exception("Read error")

    # Act
    result = generate_doc_embeddings(mock_conn, mock_client, mock_minio)

    # Assert
    assert result == 0  # Should handle error gracefully


def test_process_chunk_batch_success():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    client = MagicMock()
    client.generate_embeddings_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]

    created = _process_chunk_batch(conn, client, ["text1", "text2"], ["ref1", "ref2"])

    assert created == 2
    assert cur.execute.call_count == 2
    conn.commit.assert_called_once()


def test_process_chunk_batch_api_failure():
    conn = MagicMock()
    client = MagicMock()
    client.generate_embeddings_batch.side_effect = Exception("API Error")

    created = _process_chunk_batch(conn, client, ["text1"], ["ref1"])

    assert created == 0


def test_process_chunk_batch_db_failure():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.execute.side_effect = Exception("DB Error")

    client = MagicMock()
    client.generate_embeddings_batch.return_value = [[0.1, 0.2]]

    created = _process_chunk_batch(conn, client, ["text1"], ["ref1"])

    assert created == 0
    conn.commit.assert_called_once()


@patch("os.environ.get")
@patch("idp.storage.generate_doc_embeddings.GeminiEmbeddingsClient")
@patch("idp.storage.generate_doc_embeddings.MinioClient")
@patch("idp.storage.generate_doc_embeddings.psycopg2.connect")
@patch("idp.storage.generate_doc_embeddings.generate_doc_embeddings")
def test_run_success(mock_gen, mock_connect, mock_minio, mock_client, mock_env):
    mock_env.return_value = "postgres://url"

    run()

    mock_connect.assert_called_once()
    mock_gen.assert_called_once()


@patch("os.environ.get")
def test_run_no_db_url(mock_env):
    mock_env.return_value = None

    run()  # Should return early and not raise
