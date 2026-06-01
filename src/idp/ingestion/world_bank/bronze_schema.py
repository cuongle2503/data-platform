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


# Required fields for docs metadata
DOCS_METADATA_SCHEMA_FIELDS = [
    "doc_id",
    "title",
    "abstract",
    "display_date",
    "doc_type",
    "pdf_url",
    "txt_url",
    "countries",
    "topics",
    "language",
    "ingested_at",
    "source",
]


def get_docs_metadata_schema() -> pa.Schema:
    """Get the PyArrow schema for World Bank document metadata.

    Returns:
        PyArrow schema defining the Bronze zone structure.
    """
    return pa.schema(
        [
            pa.field("doc_id", pa.string(), nullable=False),
            pa.field("title", pa.string(), nullable=False),
            pa.field("abstract", pa.string(), nullable=True),
            pa.field("display_date", pa.string(), nullable=True),
            pa.field("doc_type", pa.string(), nullable=True),
            pa.field("pdf_url", pa.string(), nullable=True),
            pa.field("txt_url", pa.string(), nullable=True),
            pa.field("countries", pa.list_(pa.string()), nullable=True),
            pa.field("topics", pa.list_(pa.string()), nullable=True),
            pa.field("language", pa.string(), nullable=True),
            pa.field("ingested_at", pa.timestamp("ms"), nullable=False),
            pa.field("source", pa.string(), nullable=False),
        ]
    )


def validate_docs_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate document metadata records against the required schema fields.

    Invalid records are logged and filtered out.

    Args:
        records: List of normalized document metadata records.

    Returns:
        List of valid records.
    """
    valid_records = []

    for record in records:
        is_valid = True

        for field in DOCS_METADATA_SCHEMA_FIELDS:
            if field not in record:
                logger.warning(
                    f"Record missing required field '{field}': {record.get('doc_id', 'unknown')}"
                )
                is_valid = False
                break

        if is_valid:
            valid_records.append(record)

    return valid_records


# Required fields for docs text chunks
DOCS_CHUNKS_SCHEMA_FIELDS = [
    "chunk_id",
    "doc_id",
    "chunk_index",
    "total_chunks",
    "text",
    "char_count",
    "source",
]


def get_docs_chunks_schema() -> pa.Schema:
    """Get the PyArrow schema for World Bank document text chunks.

    Returns:
        PyArrow schema defining the Bronze zone structure.
    """
    return pa.schema(
        [
            pa.field("chunk_id", pa.string(), nullable=False),
            pa.field("doc_id", pa.string(), nullable=False),
            pa.field("chunk_index", pa.int32(), nullable=False),
            pa.field("total_chunks", pa.int32(), nullable=False),
            pa.field("text", pa.string(), nullable=False),
            pa.field("char_count", pa.int32(), nullable=False),
            pa.field("source", pa.string(), nullable=False),
        ]
    )


def validate_chunks_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate chunk records against the required schema fields.

    Invalid records are logged and filtered out.

    Args:
        records: List of normalized text chunk records.

    Returns:
        List of valid records.
    """
    valid_records = []

    for record in records:
        is_valid = True

        for field in DOCS_CHUNKS_SCHEMA_FIELDS:
            if field not in record:
                logger.warning(
                    f"Record missing required field '{field}': {record.get('chunk_id', 'unknown')}"
                )
                is_valid = False
                break

        if is_valid:
            valid_records.append(record)

    return valid_records
