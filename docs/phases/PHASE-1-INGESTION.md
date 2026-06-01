# Phase 1: Ingestion & Raw Storage (Bronze)

**Duration**: 3-5 days  
**Goal**: Build idempotent connectors to fetch data from World Bank APIs and store raw Parquet files in MinIO Bronze zone.

---

## Prerequisites Checklist
- [ ] Phase 0 completed (Infrastructure running)
- [ ] MinIO `bronze` bucket exists
- [ ] Environment variables configured (`MINIO_ENDPOINT`, etc.)
- [ ] Test data directory created

---

## Task List

### 1.1 Ingestion Core Utilities

**Priority**: CRITICAL  
**Estimated Time**: 4 hours

- [ ] Create `src/common/http_client.py`:
  - Implement robust HTTP client using `httpx`
  - Add retry mechanism with exponential backoff (max 3 retries)
  - Add rate limiting (World Bank limit ~30 req/s, target 10 req/s)
  - Write unit tests mocking HTTP responses

- [ ] Create `src/common/minio_client.py`:
  - Implement wrapper around `minio-py`
  - Add `upload_dataframe` method (pandas/polars to Parquet in MinIO)
  - Add `check_exists` method for idempotency
  - Write unit tests mocking MinIO

- [ ] Update `src/common/config.py`:
  - Add World Bank configuration (base URLs, default parameters)
  - Add indicator lists (32 key indicators)
  - Add country lists (10 focus countries)

### 1.2 World Bank Indicators Ingestion

**Priority**: HIGH  
**Estimated Time**: 8 hours

- [ ] Create `src/ingestion/world_bank/indicators.py`:
  - Implement `fetch_indicator_data(country_code, indicator_code, start_year, end_year)`
  - Handle World Bank API pagination (page, per_page parameters)
  - Parse JSON response into normalized format

- [ ] Create `src/ingestion/world_bank/bronze_schema.py`:
  - Define PyArrow schema matching docs (country_code, country_name, indicator_code, indicator_name, year, value, _ingested_at, _source)
  - Implement schema validation function

- [ ] Create `src/ingestion/world_bank/pipeline.py`:
  - Combine fetch and MinIO upload
  - Implement idempotency logic (check if year data already exists)
  - Format output path: `world_bank/indicators/year={YYYY}/data.parquet`

- [ ] Write Integration Tests:
  - Mock World Bank API, verify MinIO upload
  - Test pagination handling
  - Test schema validation failure

### 1.3 World Bank Documents Ingestion (Metadata)

**Priority**: MEDIUM  
**Estimated Time**: 6 hours

- [ ] Create `src/ingestion/world_bank/docs_metadata.py`:
  - Implement `fetch_docs_metadata(country_code, topic, start_date, end_date)`
  - Map World Bank WDS API response to Bronze schema (doc_id, title, abstract, display_date, doc_type, pdf_url, countries, topics, language)

- [ ] Define Document Metadata Schema:
  - Create PyArrow schema for metadata

- [ ] Implement Metadata Pipeline:
  - Fetch metadata, validate schema, upload to MinIO
  - Format output path: `world_bank/docs/metadata/year={YYYY}/data.parquet`

- [ ] Write Unit/Integration Tests for metadata fetching

### 1.4 World Bank Documents Text Extraction

**Priority**: LOW (Deferred to later if needed, focus on Indicators first)  
**Estimated Time**: 8 hours

- [ ] Create `src/ingestion/world_bank/docs_text.py`:
  - Implement `fetch_doc_text(doc_id)` using WDS `/text/` endpoint
  - Implement basic chunking strategy (~1500 chars with overlap)

- [ ] Define Text Chunk Schema:
  - Create PyArrow schema for chunks (doc_id, chunk_id, chunk_index, text, etc.)

- [ ] Implement Text Pipeline:
  - Fetch text for documents found in metadata, chunk, upload
  - Format output path: `world_bank/docs/chunks/year={YYYY}/data.parquet`

### 1.5 CLI Interface for Ingestion

**Priority**: MEDIUM  
**Estimated Time**: 3 hours

- [ ] Create `src/ingestion/cli.py`:
  - Implement simple CLI using `argparse` or `typer`
  - Commands: `ingest-indicators`, `ingest-docs-metadata`, `ingest-docs-text`
  - Arguments: `--start-year`, `--end-year`, `--countries`, `--indicators`

- [ ] Test CLI commands manually against live API (limited scope)

### 1.6 Verification & Testing

**Priority**: CRITICAL  
**Estimated Time**: 4 hours

- [ ] Run full test suite: `uv run pytest tests/unit/ingestion/`
- [ ] Check coverage: ensure >80% for `src/ingestion/`
- [ ] Security check: ensure no hardcoded API keys or URLs in code
- [ ] Lint & Format: run `ruff` and `mypy`

---

## Success Criteria

✅ MinIO client can upload Parquet files  
✅ World Bank Indicator data correctly fetched, validated against schema, and stored in MinIO  
✅ World Bank Document metadata fetched and stored in MinIO  
✅ Ingestion pipelines are idempotent (can be run multiple times safely)  
✅ Test coverage > 80% for ingestion module  
✅ CLI commands working  

---

## Next Phase

→ [PHASE-2-TRANSFORMATION.md](PHASE-2-TRANSFORMATION.md) — Transformation (Silver & Gold) with DuckDB + dbt