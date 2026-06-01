"""Unit tests for World Bank document text extraction module."""

from unittest.mock import AsyncMock, Mock

import pytest

from idp.ingestion.world_bank.docs_text import (
    chunk_text,
    fetch_and_chunk_doc,
    fetch_and_chunk_docs,
    fetch_doc_text,
    make_chunk_records,
)


def test_chunk_text_empty():
    """Test chunking handles empty text."""
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_small():
    """Test chunking with text smaller than chunk size."""
    text = "Short text"
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert chunks == ["Short text"]


def test_chunk_text_exact_size():
    """Test chunking with text exactly chunk size."""
    text = "A" * 100
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert chunks == [text]


def test_chunk_text_basic():
    """Test basic chunking behavior with overlap."""
    text = "1234567890"  # length 10
    chunks = chunk_text(text, chunk_size=6, overlap=2)
    assert len(chunks) == 2
    assert chunks[0] == "123456"
    assert chunks[1] == "567890"


def test_chunk_text_natural_boundaries():
    """Test that chunking prefers natural sentence boundaries."""
    text = "This is a sentence. And this is another sentence that continues."
    chunks = chunk_text(text, chunk_size=30, overlap=5)
    assert len(chunks) >= 2


@pytest.mark.asyncio
async def test_fetch_doc_text():
    """Test fetching document text."""
    mock_http = Mock()
    mock_response = Mock()
    mock_response.text = "Document text content"
    mock_response.raise_for_status = Mock()
    mock_http._client = Mock()
    mock_http._client.get = AsyncMock(return_value=mock_response)

    result = await fetch_doc_text(
        doc_id="doc_1", txt_url="http://example.com/doc.txt", http_client=mock_http
    )

    assert result == "Document text content"
    mock_http._client.get.assert_called_once_with("http://example.com/doc.txt")


@pytest.mark.asyncio
async def test_fetch_doc_text_empty():
    """Test fetching empty document text."""
    mock_http = Mock()
    mock_response = Mock()
    mock_response.text = "   "
    mock_response.raise_for_status = Mock()
    mock_http._client = Mock()
    mock_http._client.get = AsyncMock(return_value=mock_response)

    result = await fetch_doc_text(
        doc_id="doc_1", txt_url="http://example.com/doc.txt", http_client=mock_http
    )

    assert result == ""


@pytest.mark.asyncio
async def test_fetch_doc_text_error():
    """Test fetching document text with error."""
    mock_http = Mock()
    mock_http._client = Mock()
    mock_http._client.get = AsyncMock(side_effect=Exception("Network error"))

    result = await fetch_doc_text(
        doc_id="doc_1", txt_url="http://example.com/doc.txt", http_client=mock_http
    )

    assert result == ""


def test_make_chunk_records():
    """Test creating chunk records from text chunks."""
    chunks = ["chunk 1", "chunk 2"]
    records = make_chunk_records("doc_1", chunks)

    assert len(records) == 2
    assert records[0]["chunk_id"] == "doc_1_0000"
    assert records[0]["doc_id"] == "doc_1"
    assert records[0]["chunk_index"] == 0
    assert records[0]["total_chunks"] == 2
    assert records[0]["text"] == "chunk 1"
    assert records[0]["char_count"] == 7
    assert records[0]["source"] == "world_bank_wds_api"

    assert records[1]["chunk_id"] == "doc_1_0001"
    assert records[1]["chunk_index"] == 1


@pytest.mark.asyncio
async def test_fetch_and_chunk_doc():
    """Test full document fetch and chunk pipeline."""
    mock_http = Mock()
    mock_response = Mock()
    mock_response.text = "A" * 1000  # 1000 chars
    mock_response.raise_for_status = Mock()
    mock_http._client = Mock()
    mock_http._client.get = AsyncMock(return_value=mock_response)

    records = await fetch_and_chunk_doc(
        doc_id="doc_1",
        txt_url="http://example.com/doc.txt",
        http_client=mock_http,
        chunk_size=600,
        overlap=100,
    )

    assert len(records) == 2
    assert records[0]["char_count"] == 600
    assert records[1]["char_count"] == 500


@pytest.mark.asyncio
async def test_fetch_and_chunk_docs():
    """Test fetching and chunking multiple documents concurrently."""
    mock_http = Mock()
    mock_response = Mock()
    mock_response.text = "Test document content"
    mock_response.raise_for_status = Mock()
    mock_http._client = Mock()
    mock_http._client.get = AsyncMock(return_value=mock_response)

    docs = [
        {"doc_id": "doc_1", "txt_url": "url1"},
        {"doc_id": "doc_2", "txt_url": "url2"},
    ]

    records = await fetch_and_chunk_docs(
        http_client=mock_http,
        docs=docs,
        chunk_size=1000,
    )

    assert len(records) == 2
    assert records[0]["doc_id"] == "doc_1"
    assert records[1]["doc_id"] == "doc_2"
    assert mock_http._client.get.call_count == 2
