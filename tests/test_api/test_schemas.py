"""Unit tests for API schemas (Pydantic models)."""

import pytest
from pydantic import ValidationError

from idp.api.schemas.common import ErrorDetail, PaginationMeta, ResponseEnvelope
from idp.api.schemas.country import CountryResponse
from idp.api.schemas.indicator import IndicatorResponse, TimeseriesData


class TestCommonSchemas:
    """Test common response schemas."""

    def test_error_detail_creation(self):
        # Arrange & Act
        error = ErrorDetail(code="NOT_FOUND", message="Resource not found")

        # Assert
        assert error.code == "NOT_FOUND"
        assert error.message == "Resource not found"

    def test_pagination_meta_creation(self):
        # Arrange & Act
        pagination = PaginationMeta(page=1, page_size=20, total=100)

        # Assert
        assert pagination.page == 1
        assert pagination.page_size == 20
        assert pagination.total == 100

    def test_response_envelope_with_data(self):
        # Arrange & Act
        response = ResponseEnvelope(data={"key": "value"}, meta=None, error=None)

        # Assert
        assert response.data == {"key": "value"}
        assert response.meta is None
        assert response.error is None

    def test_response_envelope_with_error(self):
        # Arrange & Act
        error = ErrorDetail(code="VALIDATION_ERROR", message="Invalid input")
        response = ResponseEnvelope(data=None, meta=None, error=error)

        # Assert
        assert response.data is None
        assert response.error.code == "VALIDATION_ERROR"


class TestCountrySchema:
    """Test country response schema."""

    def test_country_response_creation(self):
        # Arrange & Act
        country = CountryResponse(
            country_code="VNM",
            country_name="Vietnam",
            region="East Asia & Pacific",
            income_group="Lower middle income",
            is_asean=True,
            is_primary=True,
        )

        # Assert
        assert country.country_code == "VNM"
        assert country.country_name == "Vietnam"
        assert country.is_asean is True

    def test_country_response_validation_fails_on_missing_fields(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            CountryResponse(country_code="VNM")  # Missing required fields


class TestIndicatorSchema:
    """Test indicator response schemas."""

    def test_indicator_response_creation(self):
        # Arrange & Act
        indicator = IndicatorResponse(
            indicator_code="NY.GDP.MKTP.CD",
            indicator_name="GDP (current US$)",
            category="Economic Policy & Debt",
            unit="current US$",
            description="GDP at purchaser's prices",
        )

        # Assert
        assert indicator.indicator_code == "NY.GDP.MKTP.CD"
        assert indicator.indicator_name == "GDP (current US$)"
        assert indicator.category == "Economic Policy & Debt"

    def test_timeseries_data_creation(self):
        # Arrange & Act
        timeseries = TimeseriesData(
            country_code="VNM",
            indicator_code="NY.GDP.MKTP.CD",
            year=2023,
            value=429.7,
            source="World Bank",
        )

        # Assert
        assert timeseries.country_code == "VNM"
        assert timeseries.year == 2023
        assert timeseries.value == 429.7

    def test_timeseries_data_validation_fails_on_invalid_year(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            TimeseriesData(
                country_code="VNM",
                indicator_code="NY.GDP.MKTP.CD",
                year=1899,  # Too old
                value=100.0,
                source="World Bank",
            )
