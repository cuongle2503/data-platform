"""E2E test for document embeddings generation with mock Gemini client.

Requires running MinIO and PostgreSQL instances. Skip if unavailable.
"""

import logging
import os
from unittest.mock import MagicMock

import polars as pl
import psycopg2
import pytest

from idp.common.minio_client import MinioClient
from idp.storage.generate_doc_embeddings import generate_doc_embeddings

logger = logging.getLogger(__name__)

DB_URL = os.environ.get("DATABASE_URL", "")
SAMPLE_CHUNKS = pl.DataFrame(
    {
        "chunk_id": ["test_doc_001_0001", "test_doc_001_0002", "test_doc_002_0001"],
        "doc_id": ["test_doc_001", "test_doc_001", "test_doc_002"],
        "text": [
            "This is the first chunk of test document 001.",
            "This is the second chunk of test document 001.",
            "This is the first chunk of test document 002.",
        ],
        "chunk_index": [0, 1, 0],
        "total_chunks": [2, 2, 1],
        "char_count": [45, 46, 45],
        "source": ["test", "test", "test"],
    }
)


@pytest.fixture
def db_conn():
    """Connect to PostgreSQL, skip if unavailable."""
    if not DB_URL:
        pytest.skip("DATABASE_URL not set — skipping E2E doc embeddings test")
    conn = psycopg2.connect(DB_URL)
    yield conn
    conn.close()


@pytest.fixture
def minio_client():
    """Create a MinIO client, skip if credentials missing."""
    endpoint = os.environ.get("MINIO_ENDPOINT", "")
    if not endpoint:
        pytest.skip("MINIO_ENDPOINT not set — skipping E2E doc embeddings test")
    return MinioClient(
        endpoint=endpoint,
        access_key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin"),
    )


@pytest.mark.slow
@pytest.mark.integration
def test_doc_embeddings_idempotency(
    db_conn: psycopg2.extensions.connection,
    minio_client: MinioClient,
    mock_gemini_client: MagicMock,
) -> None:
    """Generate doc embeddings via mock Gemini, verify idempotency and vector search."""
    cur = db_conn.cursor()

    # Upload test chunks to MinIO
    test_path = "world_bank/docs/chunks/test_chunks.parquet"
    minio_client.upload_dataframe(SAMPLE_CHUNKS, test_path)
    logger.info("Uploaded %d test chunks to MinIO", len(SAMPLE_CHUNKS))

    # Clean slate
    cur.execute("DELETE FROM embeddings.economic_embeddings WHERE ref_type = 'world_bank_report'")
    db_conn.commit()

    # First run
    created = generate_doc_embeddings(db_conn, mock_gemini_client, minio_client, batch_size=2)
    assert created == 3, f"Expected 3 embeddings created, got {created}"

    # Verify records exist
    cur.execute(
        "SELECT COUNT(*) FROM embeddings.economic_embeddings WHERE ref_type = 'world_bank_report'"
    )
    count = cur.fetchone()
    assert count is not None and count[0] == 3, f"Expected 3 doc embeddings, got {count}"

    # Second run — idempotent
    created_again = generate_doc_embeddings(db_conn, mock_gemini_client, minio_client, batch_size=2)
    assert created_again == 0, f"Expected 0 on second run, got {created_again}"

    # Vector search works
    cur.execute(
        """
        SELECT ref_id, 1 - (embedding <=> %s::vector) as similarity
        FROM embeddings.economic_embeddings
        WHERE ref_type = 'world_bank_report'
        ORDER BY embedding <=> %s::vector
        LIMIT 1
    """,
        ([0.1] * 768, [0.1] * 768),
    )
    result = cur.fetchone()
    assert result is not None, "Vector search should return a result"
    logger.info("Search successful: %s similarity=%.4f", result[0], result[1])

    # Cleanup test data
    cur.execute("DELETE FROM embeddings.economic_embeddings WHERE ref_type = 'world_bank_report'")
    db_conn.commit()
