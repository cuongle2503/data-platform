"""Tests for World Bank indicators pipeline."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import polars as pl

from idp.ingestion.world_bank.pipeline import WorldBankIndicatorsPipeline
from idp.common.config import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """Create test settings."""
    return Settings()


@pytest.fixture
def pipeline(mock_settings: Settings) -> WorldBankIndicatorsPipeline:
    """Create a pipeline with mocked dependencies."""
    p = WorldBankIndicatorsPipeline(settings=mock_settings)
    return p


@pytest.mark.asyncio
async def test_fetch_indicator_data_basic():
    """Test basic indicator fetch with mocked HTTP client."""
    # Arrange
    mock_http = AsyncMock()
    mock_response = [
        {"page": 1, "pages": 1, "per_page": 1000, "total": 1},
        [
            {
                "countryiso3code": "VNM",
                "country": {"value": "Vietnam"},
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                "date": "2023",
                "value": 429.0,
            }
        ],
    ]
    mock_http.get.return_value = mock_response

    pipeline = WorldBankIndicatorsPipeline(
        settings=mock_settings, http_client=mock_http
    )

    # Act
    result = await pipeline.fetch_indicator(
        country_code="VN", indicator_code="NY.GDP.MKTP.CD"
    )

    # Assert
    assert len(result) == 1
    assert result[0]["country_code"] == "VNM"
    assert result[0]["indicator_code"] == "NY.GDP.MKTP.CD"
    assert result[0]["year"] == 2023
    assert result[0]["value"] == 429.0
    mock_http.get.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_indicator_with_year_range():
    """Test indicator fetch with start/end year."""
    # Arrange
    mock_http = AsyncMock()
    mock_response = [
        {"page": 1, "pages": 1, "per_page": 1000, "total": 2},
        [
            {"countryiso3code": "VNM", "country": {"value": "Vietnam"},
             "indicator": {"id": "SP.POP.TOTL", "value": "Population, total"},
             "date": "2022", "value": 99.0},
            {"countryiso3code": "VNM", "country": {"value": "Vietnam"},
             "indicator": {"id": "SP.POP.TOTL", "value": "Population, total"},
             "date": "2023", "value": 100.0},
        ],
    ]
    mock_http.get.return_value = mock_response

    pipeline = WorldBankIndicatorsPipeline(
        settings=mock_settings, http_client=mock_http
    )

    # Act
    result = await pipeline.fetch_indicator(
        country_code="VN", indicator_code="SP.POP.TOTL",
        start_year=2022, end_year=2023,
    )

    # Assert
    assert len(result) == 2
    assert result[0]["year"] == 2022
    assert result[1]["year"] == 2023


@pytest.mark.asyncio
async def test_fetch_indicator_handles_null_value():
    """Test indicator fetch when value is null."""
    # Arrange
    mock_http = AsyncMock()
    mock_response = [
        {"page": 1, "pages": 1, "per_page": 1000, "total": 1},
        [
            {"countryiso3code": "VNM", "country": {"value": "Vietnam"},
             "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP"},
             "date": "2023", "value": None},
        ],
    ]
    mock_http.get.return_value = mock_response

    pipeline = WorldBankIndicatorsPipeline(
        settings=mock_settings, http_client=mock_http
    )

    # Act
    result = await pipeline.fetch_indicator(
        country_code="VN", indicator_code="NY.GDP.MKTP.CD"
    )

    # Assert
    assert len(result) == 1
    assert result[0]["value"] is None


@pytest.mark.asyncio
async def test_fetch_indicator_handles_pagination():
    """Test indicator fetch with multiple pages."""
    # Arrange
    mock_http = AsyncMock()
    # First page
    mock_http.get.side_effect = [
        [
            {"page": 1, "pages": 2, "per_page": 100, "total": 200},
            [
                {"countryiso3code": "VNM", "country": {"value": "Vietnam"},
                 "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP"},
                 "date": "2023", "value": 100.0},
            ],
        ],
        [
            {"page": 2, "pages": 2, "per_page": 100, "total": 200},
            [
                {"countryiso3code": "VNM", "country": {"value": "Vietnam"},
                 "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP"},
                 "date": "2022", "value": 95.0},
            ],
        ],
    ]

    pipeline = WorldBankIndicatorsPipeline(
        settings=mock_settings, http_client=mock_http
    )

    # Act
    result = await pipeline.fetch_indicator(
        country_code="VN", indicator_code="NY.GDP.MKTP.CD"
    )

    # Assert
    assert len(result) == 2
    assert mock_http.get.call_count == 2


@pytest.mark.asyncio
async def test_fetch_indicator_returns_empty_on_error():
    """Test indicator fetch returns empty list on error."""
    # Arrange
    mock_http = AsyncMock()
    mock_http.get.side_effect = Exception("API error")

    pipeline = WorldBankIndicatorsPipeline(
        settings=mock_settings, http_client=mock_http
    )

    # Act
    result = await pipeline.fetch_indicator(
        country_code="VN", indicator_code="NY.GDP.MKTP.CD"
    )

    # Assert
    assert result == []


def test_normalize_record():
    """Test normalization of a World Bank API record."""
    # Arrange
    pipeline = WorldBankIndicatorsPipeline(settings=Settings())

    record = {
        "countryiso3code": "VNM",
        "country": {"value": "Vietnam"},
        "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
        "date": "2023",
        "value": 429.0,
    }

    # Act
    result = pipeline.normalize_record(record)

    # Assert
    assert result["country_code"] == "VNM"
    assert result["country_name"] == "Vietnam"
    assert result["indicator_code"] == "NY.GDP.MKTP.CD"
    assert result["indicator_name"] == "GDP (current US$)"
    assert result["year"] == 2023
    assert result["value"] == 429.0
    assert "ingested_at" in result
    assert result["source"] == "world_bank_api"


def test_normalize_record_none_value():
    """Test normalization when value is None."""
    # Arrange
    pipeline = WorldBankIndicatorsPipeline(settings=Settings())
    record = {
        "countryiso3code": "VNM",
        "country": {"value": "Vietnam"},
        "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP"},
        "date": "2023",
        "value": None,
    }

    # Act
    result = pipeline.normalize_record(record)

    # Assert
    assert result["value"] is None
