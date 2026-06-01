# Phase 2: Transformation (Silver & Gold)

**Duration**: 4-6 days  
**Goal**: Clean, standardize, and model raw data using DuckDB and dbt-core into Silver (staging) and Gold (marts) layers.

---

## Prerequisites Checklist
- [ ] Phase 1 completed (Ingestion working)
- [ ] Sample data exists in MinIO Bronze bucket
- [ ] DuckDB installed
- [ ] `dbt-core` and `dbt-duckdb` installed
- [ ] Target PostgreSQL database running

---

## Task List

### 2.1 dbt Project Setup

**Priority**: CRITICAL  
**Estimated Time**: 2 hours

- [ ] Initialize dbt project:
  ```bash
  cd dbt
  dbt init idp
  ```

- [ ] Configure `dbt/profiles.yml`:
  - Setup DuckDB profile pointing to `../data/gold.duckdb`
  - Configure MinIO extensions (httpfs) for DuckDB

- [ ] Configure `dbt_project.yml`:
  - Define model paths, tests, seeds
  - Set default materializations (view for Silver, table for Gold)

- [ ] Create directory structure:
  - `models/staging/world_bank/`
  - `models/gold/`
  - `seeds/`

### 2.2 DuckDB MinIO Integration

**Priority**: HIGH  
**Estimated Time**: 2 hours

- [ ] Create setup script `dbt/macros/setup_s3.sql`:
  - Load `httpfs` extension
  - Set s3 endpoint, access key, secret key from env vars
  - Configure path style for MinIO

- [ ] Define sources in `dbt/models/staging/world_bank/sources.yml`:
  - Define `bronze` source pointing to `s3://bronze/world_bank/indicators/*/*.parquet`

### 2.3 Silver Models (Staging)

**Priority**: HIGH  
**Estimated Time**: 6 hours

- [ ] Create `stg_world_bank__indicators.sql`:
  - Read from Bronze source
  - Clean country codes, indicator codes (UPPER, TRIM)
  - Cast types (value to DOUBLE, year to INTEGER)
  - Deduplicate on `(country_code, indicator_code, year)` using `row_number()`

- [ ] Create `stg_world_bank__indicators.yml`:
  - Document columns
  - Add tests: `not_null` on keys, `unique` on composite key `(country_code, indicator_code, year)`

- [ ] Create `stg_world_bank__docs.sql` (if doc metadata ingested):
  - Clean and standardize document metadata

### 2.4 Dimension Models (Gold)

**Priority**: CRITICAL  
**Estimated Time**: 8 hours

- [ ] Create seeds:
  - `seed_countries.csv` (country_code, country_name, region, income_group, is_asean, is_primary)
  - `seed_indicators.csv` (indicator_code, indicator_name, source_system, category, unit, frequency, description)

- [ ] Create `dim_countries.sql`:
  - Build dimension from seed
  - Generate surrogate key `country_key`

- [ ] Create `dim_indicators.sql`:
  - Build dimension from seed
  - Generate surrogate key `indicator_key`

- [ ] Create `dim_dates.sql`:
  - Generate date dimension from 1950 to 2030
  - Include year, quarter, month, day attributes

- [ ] Document and test dimensions:
  - Add `not_null` and `unique` tests to all surrogate and natural keys

### 2.5 Fact Model (Gold)

**Priority**: CRITICAL  
**Estimated Time**: 6 hours

- [ ] Create `fact_economic_indicators.sql`:
  - Join `stg_world_bank__indicators` with `dim_countries`, `dim_indicators`, and `dim_dates`
  - Select surrogate keys, value, source_system
  - Add load timestamp

- [ ] Create `schema.yml` for Gold models:
  - Add relationship tests (FKs point to valid PKs in dims)
  - Add unique combination test on `(indicator_key, country_key, date_key, source_system)`

- [ ] Run full dbt build:
  ```bash
  dbt run
  dbt test
  ```

### 2.6 Export to PostgreSQL

**Priority**: HIGH  
**Estimated Time**: 4 hours

- [ ] Create `src/transformation/exporter.py`:
  - Implement DuckDB to PostgreSQL export logic
  - Connect to DuckDB (`gold.duckdb`)
  - Connect to PostgreSQL (`idp` database)
  - Read Gold tables, TRUNCATE PostgreSQL tables, insert data
  - Handle schema creation (`gold`) if not exists

- [ ] Write integration test for exporter:
  - Mock DuckDB and PostgreSQL connections
  - Verify data transfer

### 2.7 Verification & Testing

**Priority**: CRITICAL  
**Estimated Time**: 2 hours

- [ ] Verify DuckDB database created with correct schema
- [ ] Ensure all `dbt test` assertions pass
- [ ] Verify data successfully exported to PostgreSQL
- [ ] Check logs for export process

---

## Success Criteria

✅ DuckDB successfully reads Parquet from MinIO Bronze  
✅ dbt models compile and run successfully  
✅ Data quality tests pass (no nulls, no duplicates, valid FKs)  
✅ Gold models contain correct joined data  
✅ Exporter script successfully loads Gold tables into PostgreSQL  

---

## Next Phase

→ [PHASE-3-STORAGE.md](PHASE-3-STORAGE.md) — Storage & Serving (PostgreSQL + pgvector)