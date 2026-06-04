"""Batch indicator embeddings generation and insertion into pgvector."""

import logging
from typing import Any

import psycopg2

from idp.storage.embeddings_client import GeminiEmbeddingsClient

logger = logging.getLogger(__name__)


def build_indicator_text(row: dict[str, Any]) -> str:
    """Build a rich text representation for embedding."""
    parts = [
        f"Indicator: {row['indicator_name']}",
        f"Code: {row['indicator_code']}",
        f"Category: {row.get('category') or 'N/A'}",
        f"Unit: {row.get('unit') or 'N/A'}",
    ]
    if row.get("description"):
        parts.append(f"Description: {row['description']}")

    return "\n".join(parts)


def get_existing_ref_ids(cursor: Any, ref_type: str) -> set[str]:
    """Get set of already-embedded ref_ids for idempotency."""
    cursor.execute(
        "SELECT ref_id FROM embeddings.economic_embeddings WHERE ref_type = %s", (ref_type,)
    )
    return {row[0] for row in cursor.fetchall()}


def generate_indicator_embeddings(
    conn: Any, client: GeminiEmbeddingsClient, batch_size: int = 5
) -> int:
    """
    Generate embeddings for all indicators, idempotently.

    Returns number of new embeddings created.
    """
    cur = conn.cursor()

    existing = get_existing_ref_ids(cur, "economic_indicator")
    logger.info(f"Found {len(existing)} existing indicator embeddings")

    cur.execute("""
        SELECT indicator_code, indicator_name, category, unit, description
        FROM gold.dim_indicators
        ORDER BY indicator_code
    """)

    batch = []
    batch_refs = []
    created = 0

    for row in cur.fetchall():
        row_dict = {
            "indicator_code": row[0],
            "indicator_name": row[1],
            "category": row[2],
            "unit": row[3],
            "description": row[4],
        }

        if row_dict["indicator_code"] in existing:
            continue

        text = build_indicator_text(row_dict)
        batch.append(text)
        batch_refs.append(row_dict["indicator_code"])

        if len(batch) >= batch_size:
            created += _process_batch(conn, client, batch, batch_refs, "economic_indicator")
            batch = []
            batch_refs = []

    if batch:
        created += _process_batch(conn, client, batch, batch_refs, "economic_indicator")

    return created


def _process_batch(
    conn: Any,
    client: GeminiEmbeddingsClient,
    texts: list[str],
    ref_ids: list[str],
    ref_type: str,
) -> int:
    """Process a batch: generate embeddings and insert."""
    try:
        embeddings = client.generate_embeddings_batch(texts)
    except Exception as e:
        logger.error(f"Failed to generate embeddings for batch: {e}")
        return 0

    cur = conn.cursor()
    created = 0
    for ref_id, embedding in zip(ref_ids, embeddings, strict=True):
        try:
            cur.execute(
                """
                INSERT INTO embeddings.economic_embeddings (ref_type, ref_id, embedding, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (ref_type, ref_id) DO UPDATE
                SET embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata
            """,
                (ref_type, ref_id, embedding, '{"source": "gemini-text-embedding-004"}'),
            )
            created += 1
        except Exception as e:
            logger.error(f"Failed to insert embedding for {ref_id}: {e}")

    conn.commit()
    logger.info(f"Inserted {created} embeddings")
    return created


def run() -> None:
    """Main entry point for the embeddings generation pipeline."""
    logging.basicConfig(level=logging.INFO)

    from idp.common.config import get_settings

    db_url = get_settings().postgres.database_url

    client = GeminiEmbeddingsClient()

    conn = psycopg2.connect(db_url)
    try:
        created = generate_indicator_embeddings(conn, client)
        logger.info(f"Generated {created} new embeddings")
    finally:
        conn.close()
