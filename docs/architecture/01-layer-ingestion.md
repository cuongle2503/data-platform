# Layer 1 — Ingestion & Raw Storage

## Objectives

Layer 1 is responsible for connecting to upstream sources, extracting data with minimal transformation, and writing raw, append-only Parquet files into the Bronze zone in MinIO. Business logic and heavy validation are intentionally deferred to later layers.

## World Bank Open Data

**World Bank Open Data** provides structured macroeconomic indicators:

- **API base**: `https://api.worldbank.org/v2`
- **Authentication**: none (public API)
- **Rate limit**: around 30 req/s (undocumented; be conservative)
- **License**: Creative Commons Attribution 4.0 (CC BY 4.0)
- **Indicators of interest**: 32 curated indicators across GDP, inflation, trade, debt, population, education, infrastructure, environment, and economic structure
- **Countries of interest**: 10 countries (Vietnam as primary; Thailand, Indonesia, Philippines, Malaysia, Singapore, China, USA, Japan, Korea for comparison and context)

## Bronze Schema for World Bank Indicators

Raw World Bank data is stored in the `bronze` MinIO bucket as Parquet:

- **Storage path pattern**: `s3://bronze/world_bank/indicators/year={YYYY}/data.parquet`
- **Logical Bronze table**: `raw_world_bank_indicators`

| Column         | Type      | Source | Description                     |
|----------------|-----------|--------|---------------------------------|
| `country_code` | STRING    | API    | ISO 3-letter country code      |
| `country_name` | STRING    | API    | Full country name              |
| `indicator_code` | STRING  | API    | World Bank indicator ID        |
| `indicator_name` | STRING  | API    | Indicator name                 |
| `year`         | INT       | API    | Observation year               |
| `value`        | FLOAT     | API    | Indicator value (nullable)     |
| `_ingested_at` | TIMESTAMP | System | Ingestion timestamp            |
| `_source`      | STRING    | System | Always `"world_bank"`         |

This schema mirrors the World Bank series structure and ensures consistency across layers.

## World Bank Documents (WDS)

World Bank Documents supply unstructured text for RAG:

- **API base**: `https://search.worldbank.org/api/v2/wds`
- **Authentication**: none
- **License**: CC BY 4.0

### Metadata Bronze Table: `raw_world_bank_docs`

| Column         | Type      | Description                     |
|----------------|-----------|---------------------------------|
| `doc_id`       | STRING    | Unique document identifier      |
| `title`        | STRING    | Document title                  |
| `abstract`     | TEXT      | Document abstract/summary       |
| `display_date` | STRING    | Publication date                |
| `doc_type`     | STRING    | Document type (report, etc.)    |
| `pdf_url`      | STRING    | URL to PDF                      |
| `countries`    | STRING[]  | Related countries               |
| `topics`       | STRING[]  | Related topics                  |
| `language`     | STRING    | Document language               |
| `_ingested_at` | TIMESTAMP | Ingestion timestamp             |
| `_source`      | STRING    | Always `"world_bank_docs"`     |

### Text Chunk Bronze Table: `raw_world_bank_docs_chunks`

| Column         | Type      | Description                     |
|----------------|-----------|---------------------------------|
| `doc_id`       | STRING    | Parent document ID              |
| `chunk_id`     | STRING    | Unique chunk identifier         |
| `chunk_index`  | INT       | Chunk sequence number           |
| `text`         | TEXT      | Chunk text (~1500 chars)        |
| `country_code` | STRING    | Denormalized from parent        |
| `country_name` | STRING    | Denormalized from parent        |
| `doc_type`     | STRING    | Denormalized from parent        |
| `display_date` | STRING    | Denormalized from parent        |
| `_ingested_at` | TIMESTAMP | Ingestion timestamp             |
| `_source`      | STRING    | Always `"world_bank_docs"`     |

Text is retrieved from the `/text/` endpoint and chunked with overlap, avoiding local PDF parsing and improving text quality.

## Implementation Notes

- Use Python connectors with `requests` or `httpx` for API calls
- Implement exponential backoff for rate limiting
- Store raw responses as Parquet using `pyarrow` or `polars`
- MinIO credentials managed via environment variables
- Idempotent ingestion: check for existing data before fetching
- Log all ingestion runs with timestamps and record counts
