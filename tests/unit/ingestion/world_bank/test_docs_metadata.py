"""Unit tests for World Bank docs metadata module."""

from unittest.mock import AsyncMock

import pytest

from idp.common.exceptions import IngestionError
from idp.ingestion.world_bank.docs_metadata import (
    fetch_all_docs_metadata,
    fetch_docs_metadata,
)


@pytest.mark.asyncio
async def test_fetch_docs_metadata_calls_correct_url():
    """Test that fetch_docs_metadata calls the WDS API with correct params."""
    # Arrange
    mock_http = AsyncMock()
    mock_response = {
        "rows": 1,
        "os": 0,
        "page": 1,
        "total": 1,
        "documents": {},
        "facets": {},
    }
    mock_http.get.return_value = mock_response

    # Act
    result = await fetch_docs_metadata(
        http_client=mock_http,
        country_code="VN",
        rows=100,
        page=1,
    )

    # Assert
    assert result == mock_response
    call_args = mock_http.get.call_args
    assert call_args[1]["params"]["countcode"] == "VN"


@pytest.mark.asyncio
async def test_fetch_docs_metadata_with_date_range():
    """Test fetch_docs_metadata with start and end date filters."""
    # Arrange
    mock_http = AsyncMock()
    mock_response = {"rows": 0, "os": 0, "total": 0, "documents": {}}
    mock_http.get.return_value = mock_response

    # Act
    result = await fetch_docs_metadata(
        http_client=mock_http,
        country_code="VN",
        start_date="2024-01-01",
        end_date="2024-12-31",
    )

    # Assert
    assert result == mock_response
    call_args = mock_http.get.call_args
    params = call_args[1]["params"]
    assert "docdt" in params
    assert "2024-01-01" in str(params["docdt"])
    assert "2024-12-31" in str(params["docdt"])


@pytest.mark.asyncio
async def test_fetch_docs_metadata_handles_api_error():
    """Test that API errors are caught and re-raised as IngestionError."""
    # Arrange
    mock_http = AsyncMock()
    mock_http.get.side_effect = Exception("Connection refused")

    # Act & Assert
    with pytest.raises(IngestionError, match="Failed to fetch documents metadata"):
        await fetch_docs_metadata(
            http_client=mock_http,
            country_code="VN",
        )


@pytest.mark.asyncio
async def test_fetch_docs_metadata_handles_invalid_response():
    """Test handling of malformed API response (not a dict)."""
    # Arrange
    mock_http = AsyncMock()
    mock_http.get.return_value = []  # Not the expected dict

    # Act & Assert
    with pytest.raises(IngestionError, match="Unexpected WDS API response format"):
        await fetch_docs_metadata(
            http_client=mock_http,
            country_code="VN",
        )


@pytest.mark.asyncio
async def test_fetch_docs_metadata_handles_missing_documents():
    """Test handling of response without 'documents' field."""
    # Arrange
    mock_http = AsyncMock()
    mock_http.get.return_value = {"rows": 0, "total": 0}  # No 'documents' key

    # Act & Assert
    with pytest.raises(IngestionError, match="missing 'documents'"):
        await fetch_docs_metadata(
            http_client=mock_http,
            country_code="VN",
        )


@pytest.mark.asyncio
async def test_fetch_all_docs_metadata_single_page():
    """Test fetching all docs across pages."""
    # Arrange
    mock_http = AsyncMock()
    mock_http.get.return_value = {
        "rows": 2,
        "os": 0,
        "total": 2,
        "documents": {
            "D001": {"id": "001", "display_title": "Report 1", "count": "Viet Nam"},
            "D002": {"id": "002", "display_title": "Report 2", "count": "Viet Nam"},
        },
    }

    # Act
    result = await fetch_all_docs_metadata(
        http_client=mock_http,
        country_code="VN",
    )

    # Assert
    assert len(result) == 2
    assert mock_http.get.call_count == 1


@pytest.mark.asyncio
async def test_fetch_all_docs_metadata_respects_max_pages():
    """Test that max_pages parameter limits fetching."""
    # Arrange
    mock_http = AsyncMock()
    mock_http.get.return_value = {
        "rows": 100,
        "os": 0,
        "total": 500,
        "documents": {"D001": {"id": "001", "display_title": "Test"}, "count": "Viet Nam"},
    }

    # Act
    docs = await fetch_all_docs_metadata(
        http_client=mock_http,
        country_code="VN",
        max_pages=2,
    )

    # Assert
    assert mock_http.get.call_count == 2
    assert len(docs) > 0
