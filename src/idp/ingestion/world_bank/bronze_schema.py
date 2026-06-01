"""Bronze schema definitions for World Bank data."""

import logging
from typing import Any

import pyarrow as pa

logger = logging.getLogger(__name__)

# Required fields for valid records
INDICATOR_SCHEMA_FIELDS = [
    "country_code",
    "country_name",
    "indicator_code",
    "indicator_name",
    "year",
    "value",
    "ingested_at",
    "source",
]


def get_indicator_schema() -> pa.Schema:
    """Get the PyArrow schema for World Bank indicator data.

    Returns:
        PyArrow schema defining the Bronze zone structure.
    """
    return pa.schema(
        [
            pa.field("country_code", pa.string(), nullable=False),
            pa.field("country_name", pa.string(), nullable=False),
            pa.field("indicator_code", pa.string(), nullable=False),
            pa.field("indicator_name", pa.string(), nullable=False),
            pa.field("year", pa.int32(), nullable=False),
            pa.field("value", pa.float64(), nullable=True),
            pa.field("ingested_at", pa.timestamp("ms"), nullable=False),
            pa.field("source", pa.string(), nullable=False),
        ]
    )


def validate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate records against the required schema fields.

    Invalid records are logged and filtered out.

    Args:
        records: List of normalized indicator records.

    Returns:
        List of valid records.
    """
    valid_records = []

    for record in records:
        is_valid = True

        # Check all required fields are present
        for field in INDICATOR_SCHEMA_FIELDS:
            if field not in record:
                logger.warning(f"Record missing required field '{field}': {record}")
                is_valid = False
                break

        if is_valid:
            valid_records.append(record)

    return valid_records
