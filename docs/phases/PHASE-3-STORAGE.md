# Phase 3: Storage & Serving (Gold + Embeddings)

**Duration**: 2-4 days  
**Goal**: Finalize PostgreSQL schema design, optimize indexes, configure pgvector for embeddings, and generate embeddings for data.

---

## Prerequisites Checklist
- [x] Phase 2 completed (Gold tables populated in PostgreSQL)
- [x] PostgreSQL 16 with pgvector running
- [x] Gemini API key configured
- [x] Sample Gold data available in PostgreSQL

---

## Task List

### 3.1 Database Schema & Index Optimization

**Priority**: HIGH  
**Estimated Time**: 4 hours

- [x] Review and refine `scripts/init-db.sql`:
  - Ensure schemas (`gold`, `embeddings`) exist
  - Add detailed DDL for Gold tables with correct constraints (PK, FK)

- [x] Create optimization script `scripts/optimize_postgres.sql`:
  - Add composite index on `gold.fact_economic_indicators(indicator_key, country_key, date_key, source)`
  - Add foreign key constraints explicitly if not created by exporter
  - Create views for common API access patterns (e.g., latest values per country)

- [x] Apply optimizations to running database

### 3.2 Embeddings Schema Setup

**Priority**: CRITICAL  
**Estimated Time**: 2 hours

- [x] Create DDL for `embeddings.economic_embeddings` table:
  - Columns: id (SERIAL), ref_type (VARCHAR), ref_id (VARCHAR), embedding (VECTOR(768)), metadata (JSONB)
  - Create HNSW index: `CREATE INDEX ON embeddings.economic_embeddings USING hnsw (embedding vector_cosine_ops);`

- [x] Apply schema to database

### 3.3 Gemini Embeddings Client

**Priority**: HIGH  
**Estimated Time**: 4 hours

- [x] Create `src/storage/embeddings_client.py`:
  - Implement wrapper for Google Generative AI API (`text-embedding-004`)
  - Add batching support (API limits)
  - Implement retry logic for rate limits

- [x] Write unit tests mocking Gemini API response

### 3.4 Indicator Embeddings Generation

**Priority**: CRITICAL  
**Estimated Time**: 6 hours

- [x] Create `src/storage/generate_indicator_embeddings.py`:
  - Query `gold.dim_indicators` for all indicators
  - Construct rich text representation for embedding (e.g., "Indicator: GDP (current US$). Category: gdp. Description: ...")
  - Call Gemini Embeddings API
  - Store results in `embeddings.economic_embeddings` with `ref_type='economic_indicator'` and `ref_id=indicator_code`

- [x] Implement Idempotency:
  - Check existing embeddings, only process new or updated indicators

- [x] Write integration test for generation process

### 3.5 Document Embeddings Generation

**Priority**: MEDIUM (Deferred if docs text not ingested in Phase 1)  
**Estimated Time**: 4 hours

- [ ] Create `src/storage/generate_doc_embeddings.py`:
  - Query `raw_world_bank_docs_chunks` from Bronze/Silver
  - Call Gemini Embeddings API
  - Store results in `embeddings.economic_embeddings` with `ref_type='world_bank_report'`
  *(Note: Deferred as chunking isn't implemented yet)*

### 3.6 Storage Access Layer (Repository)

**Priority**: HIGH  
**Estimated Time**: 6 hours

- [x] Create `src/storage/repository.py`:
  - Implement Repository pattern for API layer to use
  - `get_countries()`, `get_country(code)`
  - `get_indicators()`, `get_indicator(code)`
  - `get_timeseries(country, indicators, years)`
  - `search_indicators_lexical(query)`
  - `search_indicators_semantic(query_embedding)`

- [x] Write integration tests for repository against test database

### 3.7 Verification & Testing

**Priority**: CRITICAL  
**Estimated Time**: 2 hours

- [x] Verify `economic_embeddings` table populated
- [x] Test vector similarity search manually in `psql`
- [x] Ensure >80% coverage for `src/storage/` (Achieved >92%)
- [x] Lint & Format code

---

## Success Criteria

✅ PostgreSQL schemas optimized with indexes  
✅ `pgvector` extension working and HNSW index created  
✅ Gemini Embeddings client functional  
✅ Indicator descriptions successfully embedded and stored in database  
✅ Repository access layer implemented and tested  

---

## Next Phase

→ [PHASE-4-INTELLIGENCE.md](PHASE-4-INTELLIGENCE.md) — Intelligence (FastAPI + Gemini RAG)
