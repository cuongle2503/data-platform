"""Unit tests for World Bank indicators module."""

from unittest.mock import AsyncMock

import pytest

from idp.common.exceptions import IngestionError
from idp.ingestion.world_bank.indicators import (
    fetch_indicator_data,
    fetch_multiple_indicators,
)


@pytest.mark.asyncio
async def test_fetch_indicator_data_calls_correct_url():
    """Test that fetch_indicator_data calls the correct WB API URL."""
    # Arrange
    mock_http = AsyncMock()
    mock_response = [
        {"page": 1, "pages": 1, "per_page": 1000, "total": 0},
        [],
    ]
    mock_http.get.return_value = mock_response

    # Act
    result = await fetch_indicator_data(
        http_client=mock_http,
        country_code="VN",
        indicator_code="NY.GDP.MKTP.CD",
    )

    # Assert
    assert result == []
    # Verify the URL format
    call_args = mock_http.get.call_args
    assert "VN" in call_args[0][0]
    assert "NY.GDP.MKTP.CD" in call_args[0][0]


@pytest.mark.asyncio
async def test_fetch_indicator_data_with_years():
    """Test fetch_indicator_data with start and end year."""
    # Arrange
    mock_http = AsyncMock()
    mock_response = [
        {"page": 1, "pages": 1, "per_page": 1000, "total": 1},
        [
            {"countryiso3code": "VNM", "country": {"value": "Vietnam"},
             "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP"},
             "date": "2022", "value": 400.0},
        ],
    ]
    mock_http.get.return_value = mock_response

    # Act
    result = await fetch_indicator_data(
        http_client=mock_http,
        country_code="VN",
        indicator_code="NY.GDP.MKTP.CD",
        start_year=2022,
        end_year=2023,
    )

    # Assert
    assert len(result) == 1


@pytest.mark.asyncio
async def test_fetch_indicator_data_handles_api_error():
    """Test that API errors are caught and re-raised as IngestionError."""
    # Arrange
    mock_http = AsyncMock()
    mock_http.get.side_effect = Exception("Connection refused")

    # Act & Assert
    with pytest.raises(IngestionError, match="Failed to fetch indicator data"):
        await fetch_indicator_data(
            http_client=mock_http,
            country_code="VN",
            indicator_code="NY.GDP.MKTP.CD",
        )


@pytest.mark.asyncio
async def test_fetch_indicator_data_handles_invalid_response():
    """Test handling of malformed API response."""
    # Arrange
    mock_http = AsyncMock()
    mock_http.get.return_value = []  # Not the expected 2-element list

    # Act & Assert
    with pytest.raises(IngestionError, match="Unexpected API response format"):
        await fetch_indicator_data(
            http_client=mock_http,
            country_code="VN",
            indicator_code="NY.GDP.MKTP.CD",
        )


@pytest.mark.asyncio
async def test_fetch_multiple_indicators():
    """Test fetching multiple indicators concurrently."""
    # Arrange
    mock_http = AsyncMock()
    mock_response = [
        {"page": 1, "pages": 1, "per_page": 1000, "total": 1},
        [
            {"countryiso3code": "VNM", "country": {"value": "Vietnam"},
             "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP"},
             "date": "2023", "value": 429.0},
        ],
    ]
    mock_http.get.return_value = mock_response

    indicators = [
        {"code": "NY.GDP.MKTP.CD", "name": "GDP", "source": "WDI"},
        {"code": "SP.POP.TOTL", "name": "Population", "source": "WDI"},
    ]

    # Act
    result = await fetch_multiple_indicators(
        http_client=mock_http,
        country_code="VN",
        indicators=indicators,
    )

    # Assert
    assert len(result) == 2
    assert mock_http.get.call_count == 2


@pytest.mark.asyncio
async def test_fetch_multiple_indicators_handles_partial_failure():
    """Test that partial failures don't break the entire batch."""
    # Arrange
    mock_http = AsyncMock()
    success_response = [
        {"page": 1, "pages": 1, "per_page": 1000, "total": 1},
        [
            {"countryiso3code": "VNM", "country": {"value": "Vietnam"},
             "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP"},
             "date": "2023", "value": 429.0},
        ],
    ]
    mock_http.get.side_effect = [
        success_response,
        Exception("Indicator not available"),
    ]

    indicators = [
        {"code": "NY.GDP.MKTP.CD", "name": "GDP", "source": "WDI"},
        {"code": "UNKNOWN.XYZ", "name": "Unknown", "source": "WDI"},
    ]

    # Act
    result = await fetch_multiple_indicators(
        http_client=mock_http,
        country_code="VN",
        indicators=indicators,
    )

    # Assert - should have data from the successful call only
    assert len(result) >= 1
