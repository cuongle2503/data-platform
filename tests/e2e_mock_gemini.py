import os
from unittest.mock import MagicMock

import psycopg2

from idp.storage.generate_indicator_embeddings import (
    generate_indicator_embeddings,
)


def run_e2e_test():
    db_url = os.environ.get("DATABASE_URL", "postgresql://idp_user:changeme@localhost:5433/idp")
    conn = psycopg2.connect(db_url)

    # Check starting state
    cur = conn.cursor()
    cur.execute("DELETE FROM embeddings.economic_embeddings;")
    conn.commit()

    # Mock Gemini client to return dummy vectors of size 768
    mock_client = MagicMock()
    mock_client.generate_embeddings_batch.side_effect = lambda texts: [[0.1] * 768 for _ in texts]

    # Run the generator
    created = generate_indicator_embeddings(conn, mock_client, batch_size=5)
    print(f"Created {created} new embeddings")

    # Verify records were inserted
    cur.execute("SELECT COUNT(*) FROM embeddings.economic_embeddings")
    count_after = cur.fetchone()[0]
    print(f"Total embeddings in DB: {count_after}")

    # Verify idempotency
    created_again = generate_indicator_embeddings(conn, mock_client, batch_size=5)
    print(f"Created {created_again} embeddings on second run (should be 0)")

    # Verify we can do a vector search
    cur.execute(
        """
        SELECT ref_id, 1 - (embedding <=> %s::vector) as similarity
        FROM embeddings.economic_embeddings
        LIMIT 1
    """,
        ([0.1] * 768,),
    )

    result = cur.fetchone()
    if result:
        print(f"Search successful. Found {result[0]} with similarity {result[1]:.4f}")

    conn.close()


if __name__ == "__main__":
    run_e2e_test()
