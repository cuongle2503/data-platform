"""World Bank Documents text extraction and chunking module."""

import asyncio
import logging
from typing import Any

from idp.common.http_client import HttpClient

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks.

    Args:
        text: The full text to chunk.
        chunk_size: Maximum characters per chunk.
        overlap: Number of overlapping characters between chunks.

    Returns:
        List of text chunks.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to break at a natural boundary (sentence or paragraph) if not at end
        if end < len(text):
            # Look for sentence endings (. ! ? followed by space/newline) near the end
            search_start = max(start + chunk_size // 2, start)
            best_break = end

            for sep in ["\n\n", "\n", ". ", "! ", "? ", ".", "!", "?"]:
                pos = text.rfind(sep, search_start, end)
                if pos > 0:
                    best_break = pos + len(sep)
                    break

            end = max(best_break, search_start)

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Next chunk starts with overlap
        start = end - overlap if end < len(text) else end

    return chunks


async def fetch_doc_text(doc_id: str, txt_url: str, http_client: HttpClient) -> str:
    """Fetch plain text content of a World Bank document.

    Uses the txt_url from the WDS metadata response.
    May follow redirects to documents1.worldbank.org.

    Args:
        doc_id: Document ID from WDS.
        txt_url: Full URL to the text version of the document.
        http_client: Configured HTTP client instance.

    Returns:
        Document text content as string.

    Raises:
        IngestionError: If the text cannot be fetched.
    """
    try:
        # Follow the redirect through the raw httpx client (no WDS base URL)
        response = await http_client._client.get(txt_url)
        response.raise_for_status()

        text = response.text

        if not text or not text.strip():
            logger.warning(f"Empty text content for doc {doc_id}")
            return ""

        logger.info(f"Fetched {len(text)} chars of text for doc {doc_id}")
        return text

    except Exception as e:
        logger.error(f"Failed to fetch text for doc {doc_id}: {e!s}")
        return ""


def make_chunk_records(
    doc_id: str,
    chunks: list[str],
    source: str = "world_bank_wds_api",
) -> list[dict[str, Any]]:
    """Create chunk records from a list of text chunks.

    Args:
        doc_id: Document ID.
        chunks: List of text chunks.
        source: Source label.

    Returns:
        List of record dicts with chunk metadata.
    """
    records = []
    for chunk_index, chunk_text in enumerate(chunks):
        chunk_id = f"{doc_id}_{chunk_index:04d}"
        records.append(
            {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "chunk_index": chunk_index,
                "total_chunks": len(chunks),
                "text": chunk_text,
                "char_count": len(chunk_text),
                "source": source,
            }
        )
    return records


async def fetch_and_chunk_doc(
    doc_id: str,
    txt_url: str,
    http_client: HttpClient,
    chunk_size: int = 1500,
    overlap: int = 150,
) -> list[dict[str, Any]]:
    """Fetch a document's text, chunk it, and return chunk records.

    Args:
        doc_id: Document ID.
        txt_url: URL to the text version.
        http_client: HTTP client for fetching.
        chunk_size: Max characters per chunk.
        overlap: Overlap between chunks.

    Returns:
        List of chunk record dicts.
    """
    if not txt_url:
        logger.warning(f"No txt_url for doc {doc_id}, skipping")
        return []

    text = await fetch_doc_text(doc_id=doc_id, txt_url=txt_url, http_client=http_client)

    if not text:
        return []

    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    records = make_chunk_records(doc_id=doc_id, chunks=chunks)

    logger.info(f"Chunked doc {doc_id}: {len(chunks)} chunks from {len(text)} chars")
    return records


async def fetch_and_chunk_docs(
    http_client: HttpClient,
    docs: list[dict[str, Any]],
    chunk_size: int = 1500,
    overlap: int = 150,
    concurrency: int = 5,
) -> list[dict[str, Any]]:
    """Fetch and chunk multiple documents concurrently.

    Args:
        http_client: HTTP client.
        docs: List of doc dicts, each must have 'doc_id' and 'txt_url'.
        chunk_size: Max chars per chunk.
        overlap: Overlap between chunks.
        concurrency: Max concurrent fetches.

    Returns:
        Combined list of all chunk records.
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def process_one(doc: dict[str, Any]) -> list[dict[str, Any]]:
        async with semaphore:
            doc_id = doc.get("doc_id", "")
            txt_url = doc.get("txt_url", "")
            return await fetch_and_chunk_doc(
                doc_id=doc_id,
                txt_url=txt_url,
                http_client=http_client,
                chunk_size=chunk_size,
                overlap=overlap,
            )

    tasks = [process_one(doc) for doc in docs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_records: list[dict[str, Any]] = []
    for i, result in enumerate(results):
        doc_id = docs[i].get("doc_id", f"index_{i}")
        if isinstance(result, Exception):
            logger.error(f"Failed to process doc {doc_id}: {result!s}")
        elif isinstance(result, list):
            all_records.extend(result)

    logger.info(f"Processed {len(docs)} docs → {len(all_records)} total chunks")
    return all_records
