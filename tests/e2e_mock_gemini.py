"""E2E test for indicator embeddings generation with mocked Gemini client.

Requires a running PostgreSQL instance with pgvector. Skip if unavailable.
"""

import logging
import os
from unittest.mock import MagicMock

import psycopg2
import pytest

from idp.storage.generate_indicator_embeddings import generate_indicator_embeddings

logger = logging.getLogger(__name__)

DB_URL = os.environ.get("DATABASE_URL", "")


@pytest.fixture
def db_conn():
    """Connect to PostgreSQL. Skip test if unavailable."""
    if not DB_URL:
        pytest.skip("DATABASE_URL not set — skipping E2E embedding test")

    conn = psycopg2.connect(DB_URL)
    yield conn
    conn.close()


@pytest.mark.slow
@pytest.mark.integration
def test_generate_indicator_embeddings_idempotency(
    db_conn: psycopg2.extensions.connection,
    mock_gemini_client: MagicMock,
) -> None:
    """Verify embedding generation is idempotent and creates searchable vectors."""
    cur = db_conn.cursor()

    # Clean slate
    cur.execute("DELETE FROM embeddings.economic_embeddings;")
    db_conn.commit()

    # First run should create embeddings
    created = generate_indicator_embeddings(db_conn, mock_gemini_client, batch_size=5)
    assert created > 0, f"Expected embeddings to be created, got {created}"
    logger.info("Created %d new embeddings", created)

    # Verify records exist
    cur.execute("SELECT COUNT(*) FROM embeddings.economic_embeddings")
    count_after = cur.fetchone()
    assert count_after is not None
    assert count_after[0] > 0, "Expected embeddings records in database"

    # Second run should be idempotent (create 0)
    created_again = generate_indicator_embeddings(db_conn, mock_gemini_client, batch_size=5)
    assert created_again == 0, f"Expected 0 new embeddings on re-run, got {created_again}"

    # Verify vector search works
    cur.execute(
        """
        SELECT ref_id, 1 - (embedding <=> %s::vector) as similarity
        FROM embeddings.economic_embeddings
        LIMIT 1
    """,
        ([0.1] * 768,),
    )
    result = cur.fetchone()
    assert result is not None, "Expected vector search to return a result"
    logger.info("Search successful: %s similarity=%.4f", result[0], result[1])
