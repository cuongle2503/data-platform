"""Tests for World Bank documents metadata pipeline."""

from unittest.mock import AsyncMock, patch

import pytest

from idp.common.config import Settings
from idp.ingestion.world_bank.docs_pipeline import WorldBankDocsPipeline


@pytest.fixture
def mock_settings() -> Settings:
    """Create test settings."""
    return Settings()


@pytest.mark.asyncio
async def test_fetch_metadata_basic(mock_settings: Settings):
    """Test basic document metadata fetch with mocked HTTP client."""
    # Arrange
    mock_http = AsyncMock()
    mock_response = {
        "rows": 1,
        "os": 0,
        "total": 1,
        "documents": {
            "D001": {
                "id": "001",
                "display_title": "Vietnam Economic Report 2024",
                "docna": {"0": {"docna": "Vietnam Economic Report 2024"}},
                "docdt": "2024-05-15T00:00:00Z",
                "docty": "Economic Report",
                "pdfurl": "https://example.com/report.pdf",
                "txturl": "https://example.com/report.txt",
                "count": "Viet Nam",
                "theme": "Economic Development,Trade",
                "lang": "English",
            }
        },
    }
    mock_http.get.return_value = mock_response

    pipeline = WorldBankDocsPipeline(settings=mock_settings, http_client=mock_http)

    # Act
    result = await pipeline.fetch_metadata(country_code="VN", max_pages=1)

    # Assert
    assert len(result) == 1
    assert result[0]["doc_id"] == "001"
    assert result[0]["title"] == "Vietnam Economic Report 2024"
    assert result[0]["doc_type"] == "Economic Report"
    assert result[0]["countries"] == ["Viet Nam"]
    assert result[0]["topics"] == ["Economic Development", "Trade"]
    assert result[0]["language"] == "English"
    mock_http.get.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_metadata_with_date_range(mock_settings: Settings):
    """Test document metadata fetch with date filters."""
    # Arrange
    mock_http = AsyncMock()
    mock_response = {
        "rows": 2,
        "os": 0,
        "total": 2,
        "documents": {
            "D001": {
                "id": "001",
                "display_title": "Report 1",
                "docdt": "2024-01-15T00:00:00Z",
                "count": "Viet Nam",
            },
            "D002": {
                "id": "002",
                "display_title": "Report 2",
                "docdt": "2024-06-20T00:00:00Z",
                "count": "Viet Nam",
            },
        },
    }
    mock_http.get.return_value = mock_response

    pipeline = WorldBankDocsPipeline(settings=mock_settings, http_client=mock_http)

    # Act
    result = await pipeline.fetch_metadata(
        country_code="VN",
        start_date="2024-01-01",
        end_date="2024-12-31",
        max_pages=1,
    )

    # Assert
    assert len(result) == 2


@pytest.mark.asyncio
async def test_fetch_metadata_handles_empty_response(mock_settings: Settings):
    """Test handling of empty documents response."""
    # Arrange
    mock_http = AsyncMock()
    mock_response = {"rows": 0, "os": 0, "total": 0, "documents": {}}
    mock_http.get.return_value = mock_response

    pipeline = WorldBankDocsPipeline(settings=mock_settings, http_client=mock_http)

    # Act
    result = await pipeline.fetch_metadata(country_code="VN", max_pages=1)

    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_fetch_metadata_returns_empty_on_error(mock_settings: Settings):
    """Test that fetch_metadata returns empty list on error."""
    # Arrange
    mock_http = AsyncMock()
    mock_http.get.side_effect = Exception("API error")

    pipeline = WorldBankDocsPipeline(settings=mock_settings, http_client=mock_http)

    # Act
    result = await pipeline.fetch_metadata(country_code="VN", max_pages=1)

    # Assert
    assert result == []


def test_normalize_doc_record(mock_settings: Settings):
    """Test normalization of a WDS API document record."""
    # Arrange
    pipeline = WorldBankDocsPipeline(settings=mock_settings)

    record = {
        "id": "12345",
        "display_title": "Test Document",
        "docna": {"0": {"docna": "Full Document Title"}},
        "docdt": "2024-05-15T00:00:00Z",
        "docty": "Report",
        "pdfurl": "https://example.com/doc.pdf",
        "txturl": "https://example.com/doc.txt",
        "count": "Vietnam",
        "theme": "Agriculture,Climate Change,Water Resources",
        "lang": "English",
        "abstract": "This is a test abstract",
    }

    # Act
    result = pipeline.normalize_doc_record(record)

    # Assert
    assert result["doc_id"] == "12345"
    assert result["title"] == "Full Document Title"
    assert result["abstract"] == "This is a test abstract"
    assert result["display_date"] == "2024-05-15T00:00:00Z"
    assert result["doc_type"] == "Report"
    assert result["pdf_url"] == "https://example.com/doc.pdf"
    assert result["txt_url"] == "https://example.com/doc.txt"
    assert result["countries"] == ["Vietnam"]
    assert result["topics"] == ["Agriculture", "Climate Change", "Water Resources"]
    assert result["language"] == "English"
    assert "ingested_at" in result
    assert result["source"] == "world_bank_wds_api"


def test_normalize_doc_record_fallback_to_display_title(mock_settings: Settings):
    """Test normalization falls back to display_title when docna is missing."""
    # Arrange
    pipeline = WorldBankDocsPipeline(settings=mock_settings)

    record = {
        "id": "12345",
        "display_title": "Fallback Title",
        "count": "Vietnam",
    }

    # Act
    result = pipeline.normalize_doc_record(record)

    # Assert
    assert result["title"] == "Fallback Title"


def test_normalize_doc_record_handles_empty_topics(mock_settings: Settings):
    """Test normalization handles missing or empty topics."""
    # Arrange
    pipeline = WorldBankDocsPipeline(settings=mock_settings)

    record = {
        "id": "12345",
        "display_title": "Test",
        "count": "Vietnam",
        "theme": "",
    }

    # Act
    result = pipeline.normalize_doc_record(record)

    # Assert
    assert result["topics"] == []


@pytest.mark.asyncio
async def test_docs_pipeline_run(mock_settings: Settings):
    """Test full pipeline run for documents."""
    mock_http = AsyncMock()
    pipeline = WorldBankDocsPipeline(settings=mock_settings, http_client=mock_http)

    with patch.object(pipeline, "fetch_metadata", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [{"doc_id": "1", "title": "Test 1"}]

        result = await pipeline.run(countries=["VNM"], max_pages_per_country=1)

        assert len(result) == 1
        assert result[0]["doc_id"] == "1"
        mock_fetch.assert_called_once_with(
            country_code="VNM",
            topic=None,
            start_date=None,
            end_date=None,
            max_pages=1,
        )


@pytest.mark.asyncio
async def test_docs_pipeline_run_multiple_countries(mock_settings: Settings):
    """Test pipeline run across multiple countries."""
    mock_http = AsyncMock()
    pipeline = WorldBankDocsPipeline(settings=mock_settings, http_client=mock_http)

    with patch.object(pipeline, "fetch_metadata", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [{"doc_id": "1", "title": "Test 1"}]

        result = await pipeline.run(countries=["VNM", "CHN"])

        assert len(result) == 2
        assert mock_fetch.call_count == 2
