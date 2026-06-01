# Phase 2: Transformation (Silver & Gold) — COMPLETE

**Duration**: 4-6 days
**Goal**: Clean, standardize, and model raw data using DuckDB and dbt-core into Silver (staging) and Gold (marts) layers.
**Status**: ✅ **DONE** — All tasks verified 2026-06-01

---

## Prerequisites Checklist
- [x] Phase 1 completed (Ingestion working)
- [x] Sample data exists in MinIO Bronze bucket
- [x] DuckDB installed
- [x] `dbt-core` and `dbt-duckdb` installed
- [x] Target PostgreSQL database running

---

## Task List

### 2.1 dbt Project Setup

**Priority**: CRITICAL
**Estimated Time**: 2 hours

- [x] Initialize dbt project at `dbt/idp/`:
  - Project name: `idp`, profile: `idp`
  - Staging: materialized as views
  - Gold: materialized as tables
  - Uses `dbt_utils` package (v1.3.0)

- [x] Configure `dbt/profiles.yml`:
  - DuckDB profile pointing to `../../data/gold.duckdb`
  - MinIO extensions (httpfs) for DuckDB
  - S3 credentials via env vars (`MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_ENDPOINT`)

- [x] Create directory structure:
  - `models/staging/world_bank/`
  - `models/gold/`
  - `seeds/`

### 2.2 DuckDB MinIO Integration

**Priority**: HIGH
**Estimated Time**: 2 hours

- [x] Create setup script `dbt/idp/macros/setup_s3.sql`:
  - Load `httpfs` extension
  - Set s3 endpoint, access key, secret key from env vars
  - Configure path style for MinIO

- [x] Define sources in `dbt/idp/models/staging/world_bank/sources.yml`:
  - Source `bronze` with table `world_bank_indicators`
  - External location: `read_parquet('s3://bronze/world_bank/indicators/*.parquet')`

### 2.3 Silver Models (Staging)

**Priority**: HIGH
**Estimated Time**: 6 hours

- [x] Create `stg_world_bank__indicators.sql`:
  - Read from Bronze source via `{{ source('bronze', 'world_bank_indicators') }}`
  - Clean country codes, indicator codes (UPPER, TRIM)
  - Cast types (value to DOUBLE, year to INTEGER)
  - Deduplicate on `(country_code, indicator_code, year)` using `row_number()`

- [x] Create `stg_world_bank__indicators.yml`:
  - Column documentation
  - Tests: `not_null` on `country_code`, `country_name`, `indicator_code`, `indicator_name`, `source`, `year`
  - Test: `unique_combination_of_columns` on `(country_code, indicator_code, year)`

### 2.4 Dimension Models (Gold)

**Priority**: CRITICAL
**Estimated Time**: 8 hours

- [x] Create seeds:
  - `seed_countries.csv` (20 countries — ASEAN and major economies)
  - `seed_indicators.csv` (33 WDI indicators)

- [x] Create `dim_countries.sql`:
  - Built from `seed_countries` with surrogate key `country_key` via `dbt_utils.generate_surrogate_key`

- [x] Create `dim_indicators.sql`:
  - Built from `seed_indicators` with surrogate key `indicator_key` via `dbt_utils.generate_surrogate_key`

- [x] Create `dim_dates.sql`:
  - Date dimension from 1950 to 2030 (81 years)
  - Includes year, decade, century attributes

- [x] Document and test dimensions in `models/gold/schema.yml`:
  - `not_null` and `unique` tests on `country_key`, `country_code`, `indicator_key`, `indicator_code`, `date_key`, `year`

### 2.5 Fact Model (Gold)

**Priority**: CRITICAL
**Estimated Time**: 6 hours

- [x] Create `fact_economic_indicators.sql`:
  - Join `stg_world_bank__indicators` with `dim_countries` (on `country_code`), `dim_indicators` (on `indicator_code`), `dim_dates` (on `year`)
  - Surrogate keys from dimensions, `value`, `source`, `loaded_at`

- [x] Create `schema.yml` for Gold models:
  - `not_null` tests on `indicator_key`, `country_key`, `date_key`, `source`
  - `unique_combination_of_columns` on `(indicator_key, country_key, date_key, source)`
  - Relationship tests (FKs → PKs) for `country_key`, `indicator_key`, `date_key`

- [x] dbt build results (2026-06-01):
  ```text
  Completed successfully — 34/34 PASS
  - 2 seeds loaded (seed_countries: 20, seed_indicators: 33)
  - 1 view model (stg_world_bank__indicators)
  - 4 table models (dim_dates: 81, dim_countries: 20, dim_indicators: 33, fact_economic_indicators: 192)
  - 27 data tests PASSED
  - 1 source defined
  ```

### 2.6 Export to PostgreSQL

**Priority**: HIGH
**Estimated Time**: 4 hours

- [x] Create `src/idp/transformation/exporter.py`:
  - DuckDB → PostgreSQL export via Polars DataFrames
  - Schema creation (`CREATE SCHEMA IF NOT EXISTS gold`)
  - Table-by-table: read from DuckDB, TRUNCATE PostgreSQL, COPY insert
  - Polars-to-PostgreSQL type mapping (`_polars_to_postgres_type`)
  - CLI entry via Typer

- [x] E2E export verified (2026-06-01):
  ```text
  dim_countries: 20 rows
  dim_indicators: 33 rows
  dim_dates: 81 rows
  fact_economic_indicators: 192 rows
  ```

- [x] Written unit tests at `tests/unit/transformation/test_exporter.py` (13/13 PASS):
  - `TestPolarsToPostgresType`: 8 tests covering all type mappings
  - `TestExportGoldToPostgres`: 5 tests — schema creation, empty tables, row counts, connection cleanup, custom schema naming

### 2.7 Verification & Testing

**Priority**: CRITICAL
**Estimated Time**: 2 hours

- [x] DuckDB database created with correct schema (`data/gold.duckdb`, 3.9 MB)
- [x] All `dbt test` assertions pass (27/27 data quality tests)
- [x] Data successfully exported to PostgreSQL (`gold.*` schema confirmed)
- [x] PostgreSQL tables verified:
  ```text
  Schema | Table                    | Type
  -------|--------------------------|------
  gold   | dim_countries            | table
  gold   | dim_dates                | table
  gold   | dim_indicators           | table
  gold   | fact_economic_indicators | table
  ```
- [x] Unit tests pass (13/13 in `tests/unit/transformation/`)

---

## Implementation Notes

### Key Files

| Purpose | Path |
|---------|------|
| dbt project config | `dbt/idp/dbt_project.yml` |
| dbt profile | `dbt/profiles.yml` (copied to `~/.dbt/`) |
| Silver staging model | `dbt/idp/models/staging/world_bank/stg_world_bank__indicators.sql` |
| Gold dimensions | `dbt/idp/models/gold/dim_countries.sql`, `dim_indicators.sql`, `dim_dates.sql` |
| Gold fact | `dbt/idp/models/gold/fact_economic_indicators.sql` |
| Gold schema tests | `dbt/idp/models/gold/schema.yml` |
| Seeds | `dbt/idp/seeds/seed_countries.csv`, `seed_indicators.csv` |
| S3/MiniO macro | `dbt/idp/macros/setup_s3.sql` |
| PostgreSQL exporter | `src/idp/transformation/exporter.py` |
| Exporter tests | `tests/unit/transformation/test_exporter.py` |

### Running dbt

```bash
cd dbt/idp
dbt deps          # install dbt_utils
dbt build         # run models + tests
dbt build --select staging  # staging only
dbt build --select gold     # gold only
dbt test           # run tests only
```

### Running Exporter

```bash
uv run python src/idp/transformation/exporter.py \
  --duckdb-path=data/gold.duckdb \
  --schema-name=gold
```

### Coverage Note

The transformation layer (`exporter.py`) has **91% coverage** (75/82 stmts). The overall project coverage is lower (17%) because Phase 1 ingestion code lacks tests — this is expected and addressed in Phase 1, not Phase 2.

---

## Success Criteria

✅ DuckDB successfully reads Parquet from MinIO Bronze
✅ dbt models compile and run successfully (34/34 PASS)
✅ Data quality tests pass (no nulls, no duplicates, valid FKs)
✅ Gold models contain correct joined data (192 fact rows across 20 countries, 33 indicators, 81 years)
✅ Exporter script successfully loads Gold tables into PostgreSQL

---

## Next Phase

→ [PHASE-3-STORAGE.md](PHASE-3-STORAGE.md) — Storage & Serving (PostgreSQL + pgvector)
