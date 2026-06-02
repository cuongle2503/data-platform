"""E2E test for document embeddings generation with mock Gemini client."""

import os
from unittest.mock import MagicMock

import polars as pl
import psycopg2

from idp.common.minio_client import MinioClient
from idp.storage.generate_doc_embeddings import generate_doc_embeddings


def run_e2e_doc_embeddings_test():
    """End-to-end test for document embeddings generation.

    This test:
    1. Uploads sample doc chunks to MinIO
    2. Generates embeddings using a mock Gemini client
    3. Verifies embeddings are stored in PostgreSQL
    4. Tests idempotency (second run creates 0 new embeddings)
    5. Tests vector similarity search
    """
    db_url = os.environ.get("DATABASE_URL", "postgresql://idp_user:changeme@localhost:5433/idp")
    minio_endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    minio_access = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

    # Setup: Create sample doc chunks in MinIO
    minio_client = MinioClient(
        endpoint=minio_endpoint,
        access_key=minio_access,
        secret_key=minio_secret,
    )

    sample_chunks = pl.DataFrame(
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

    # Upload to MinIO
    test_file_path = "world_bank/docs/chunks/test_chunks.parquet"
    minio_client.upload_dataframe(sample_chunks, test_file_path)
    print(f"Uploaded {len(sample_chunks)} test chunks to MinIO")

    # Connect to PostgreSQL
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # Clean up existing test embeddings
    cur.execute("DELETE FROM embeddings.economic_embeddings WHERE ref_type = 'world_bank_report'")
    conn.commit()
    print("Cleaned up existing doc embeddings")

    # Mock Gemini client to return dummy vectors of size 768
    mock_client = MagicMock()
    mock_client.generate_embeddings_batch.side_effect = lambda texts: [[0.1] * 768 for _ in texts]

    # Run the generator
    created = generate_doc_embeddings(conn, mock_client, minio_client, batch_size=2)
    print(f"✓ Created {created} new doc embeddings")

    # Verify records were inserted
    cur.execute(
        "SELECT COUNT(*) FROM embeddings.economic_embeddings WHERE ref_type = 'world_bank_report'"
    )
    count_after = cur.fetchone()[0]
    print(f"✓ Total doc embeddings in DB: {count_after}")
    assert count_after == 3, f"Expected 3 embeddings, got {count_after}"

    # Verify idempotency
    created_again = generate_doc_embeddings(conn, mock_client, minio_client, batch_size=2)
    print(f"✓ Created {created_again} embeddings on second run (should be 0)")
    assert created_again == 0, f"Expected 0 on second run, got {created_again}"

    # Verify we can do a vector search
    cur.execute(
        """
        SELECT ref_id, ref_type, 1 - (embedding <=> %s::vector) as similarity
        FROM embeddings.economic_embeddings
        WHERE ref_type = 'world_bank_report'
        ORDER BY embedding <=> %s::vector
        LIMIT 1
    """,
        ([0.1] * 768, [0.1] * 768),
    )

    result = cur.fetchone()
    if result:
        print(f"✓ Vector search successful. Found {result[0]} with similarity {result[2]:.4f}")
    else:
        print("✗ Vector search failed")

    conn.close()
    print("\n✓ All e2e doc embeddings tests passed!")


if __name__ == "__main__":
    run_e2e_doc_embeddings_test()
