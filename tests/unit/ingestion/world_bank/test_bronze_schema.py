"""Unit tests for World Bank bronze schema."""

from datetime import datetime

import pyarrow as pa

from idp.ingestion.world_bank.bronze_schema import (
    get_indicator_schema,
    validate_records,
)


def test_get_indicator_schema_returns_pyarrow_schema():
    """Test that get_indicator_schema returns a PaArrow schema."""
    # Act
    schema = get_indicator_schema()

    # Assert
    assert isinstance(schema, pa.Schema)


def test_indicator_schema_has_required_fields():
    """Test that the schema contains all required fields."""
    # Act
    schema = get_indicator_schema()

    # Assert
    field_names = [f.name for f in schema]
    assert "country_code" in field_names
    assert "country_name" in field_names
    assert "indicator_code" in field_names
    assert "indicator_name" in field_names
    assert "year" in field_names
    assert "value" in field_names
    assert "ingested_at" in field_names
    assert "source" in field_names


def test_validate_records_with_valid_data():
    """Test validation with correct records."""
    # Arrange
    records = [
        {
            "country_code": "VNM",
            "country_name": "Vietnam",
            "indicator_code": "NY.GDP.MKTP.CD",
            "indicator_name": "GDP (current US$)",
            "year": 2023,
            "value": 429.0,
            "ingested_at": datetime.now(),
            "source": "world_bank_api",
        }
    ]

    # Act
    result = validate_records(records)

    # Assert - should return the same number of records
    assert len(result) == 1
    assert result[0]["country_code"] == "VNM"


def test_validate_records_with_missing_field():
    """Test validation fails when a required field is missing."""
    # Arrange
    records = [
        {
            "country_code": "VNM",
            # missing country_name
            "indicator_code": "NY.GDP.MKTP.CD",
            "indicator_name": "GDP",
            "year": 2023,
            "value": 429.0,
            "ingested_at": datetime.now(),
            "source": "world_bank_api",
        }
    ]

    # Act
    result = validate_records(records)

    # Assert - invalid records are filtered out
    assert len(result) == 0


def test_validate_records_with_null_value():
    """Test validation allows null values."""
    # Arrange
    records = [
        {
            "country_code": "VNM",
            "country_name": "Vietnam",
            "indicator_code": "NY.GDP.MKTP.CD",
            "indicator_name": "GDP (current US$)",
            "year": 2023,
            "value": None,
            "ingested_at": datetime.now(),
            "source": "world_bank_api",
        }
    ]

    # Act
    result = validate_records(records)

    # Assert
    assert len(result) == 1
    assert result[0]["value"] is None


def test_validate_records_empty_list():
    """Test validation with an empty list."""
    # Act
    result = validate_records([])

    # Assert
    assert result == []
