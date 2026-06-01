"""Generate embeddings for World Bank document text chunks.

Reads document chunks from MinIO Bronze layer, generates embeddings via
Gemini API, and stores them in PostgreSQL embeddings.economic_embeddings.

Data flow:
    MinIO (bronze/world_bank/docs/chunks/*.parquet)
    -> Gemini Embeddings API
    -> PostgreSQL (embeddings.economic_embeddings, ref_type='world_bank_report')
"""

import logging
import os
from typing import Any

import psycopg2

from idp.common.minio_client import MinioClient
from idp.storage.embeddings_client import GeminiEmbeddingsClient

logger = logging.getLogger(__name__)

DOC_CHUNKS_PREFIX = "world_bank/docs/chunks/"


def build_chunk_text(row: dict[str, Any]) -> str:
    """Build a text representation of a document chunk for embedding.

    Args:
        row: A document chunk record with keys:
            chunk_id, doc_id, text, chunk_index, total_chunks.

    Returns:
        Rich text string suitable for embedding.
    """
    parts = [
        f"Document ID: {row.get('doc_id', 'unknown')}",
        f"Chunk: {row.get('chunk_index', 0) + 1}/{row.get('total_chunks', 1)}",
        f"Content: {row.get('text', '')}",
    ]
    return "\n".join(parts)


def get_existing_chunk_ref_ids(cursor: Any) -> set[str]:
    """Get set of already-embedded chunk_ids for idempotency.

    Args:
        cursor: Database cursor.

    Returns:
        Set of chunk_ids already in embeddings table with
        ref_type='world_bank_report'.
    """
    cursor.execute(
        "SELECT ref_id FROM embeddings.economic_embeddings "
        "WHERE ref_type = 'world_bank_report'"
    )
    return {row[0] for row in cursor.fetchall()}


def generate_doc_embeddings(
    conn: Any,
    client: GeminiEmbeddingsClient,
    minio_client: MinioClient,
    batch_size: int = 5,
) -> int:
    """Generate embeddings for all document chunks, idempotently.

    Reads chunks from MinIO Bronze and inserts embeddings into PostgreSQL.

    Args:
        conn: PostgreSQL database connection.
        client: Gemini embeddings client.
        minio_client: MinIO client for reading chunk parquet files.
        batch_size: Number of chunks to embed per API call.

    Returns:
        Number of new embeddings created.
    """
    cur = conn.cursor()

    existing = get_existing_chunk_ref_ids(cur)
    logger.info(f"Found {len(existing)} existing doc chunk embeddings")

    # List all chunk parquet files in MinIO
    chunk_files = minio_client.list_objects(prefix=DOC_CHUNKS_PREFIX)
    logger.info(f"Found {len(chunk_files)} chunk files in MinIO {DOC_CHUNKS_PREFIX!r}")

    if not chunk_files:
        logger.warning("No chunk files found in MinIO; nothing to embed")
        return 0

    batch_texts: list[str] = []
    batch_refs: list[str] = []
    created = 0

    for file_path in chunk_files:
        try:
            df = minio_client.read_dataframe(file_path)
        except Exception as e:
            logger.error(f"Failed to read chunk file {file_path}: {e}")
            continue

        records = df.to_dicts()
        logger.info(f"Read {len(records)} chunks from {file_path}")

        for record in records:
            chunk_id = record.get("chunk_id", "")
            if not chunk_id or chunk_id in existing:
                continue

            text = build_chunk_text(record)
            batch_texts.append(text)
            batch_refs.append(chunk_id)

            if len(batch_texts) >= batch_size:
                created += _process_chunk_batch(
                    conn, client, batch_texts, batch_refs
                )
                batch_texts = []
                batch_refs = []

    # Process remaining batch
    if batch_texts:
        created += _process_chunk_batch(conn, client, batch_texts, batch_refs)

    logger.info(f"Generated {created} new doc chunk embeddings total")
    return created


def _process_chunk_batch(
    conn: Any,
    client: GeminiEmbeddingsClient,
    texts: list[str],
    ref_ids: list[str],
) -> int:
    """Generate embeddings for a batch and insert into PostgreSQL.

    Args:
        conn: PostgreSQL connection.
        client: Embeddings client.
        texts: List of text content to embed.
        ref_ids: List of chunk IDs (used as ref_id).

    Returns:
        Number of embeddings inserted.
    """
    try:
        embeddings = client.generate_embeddings_batch(texts)
    except Exception as e:
        logger.error(f"Failed to generate embeddings for batch: {e}")
        return 0

    cur = conn.cursor()
    created = 0
    for ref_id, embedding in zip(ref_ids, embeddings):
        try:
            cur.execute(
                """
                INSERT INTO embeddings.economic_embeddings
                    (ref_type, ref_id, embedding, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (ref_type, ref_id) DO UPDATE
                SET embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
                """,
                (
                    "world_bank_report",
                    ref_id,
                    embedding,
                    '{"source": "gemini-text-embedding-004"}',
                ),
            )
            created += 1
        except Exception as e:
            logger.error(f"Failed to insert embedding for chunk {ref_id}: {e}")

    conn.commit()
    logger.info(f"Inserted {created} doc chunk embeddings")
    return created


def run() -> None:
    """Main entry point for document embeddings generation pipeline."""
    logging.basicConfig(level=logging.INFO)

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable is required")
        return

    minio_endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    minio_access = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

    client = GeminiEmbeddingsClient()
    minio_client = MinioClient(
        endpoint=minio_endpoint,
        access_key=minio_access,
        secret_key=minio_secret,
    )

    conn = psycopg2.connect(db_url)
    try:
        created = generate_doc_embeddings(conn, client, minio_client)
        logger.info(f"Generated {created} new doc chunk embeddings")
    finally:
        conn.close()
