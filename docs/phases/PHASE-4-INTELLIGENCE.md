# Phase 4: Intelligence (FastAPI & RAG)

**Duration**: 5-7 days  
**Goal**: Build the FastAPI backend providing REST endpoints for data access and WebSocket endpoints for Gemini-powered RAG chatbot.

---

## Prerequisites Checklist
- [ ] Phase 3 completed (Gold data & embeddings in PostgreSQL)
- [ ] `fastapi` and `uvicorn` installed
- [ ] Repository layer from Phase 3 working
- [ ] Gemini API key configured

---

## Task List

### 4.1 FastAPI App Setup & Core Models

**Priority**: CRITICAL  
**Estimated Time**: 3 hours  
**Status**: ✅ COMPLETED

- [x] Create `api/main.py`:
  - Setup FastAPI app with CORS middleware
  - Include API routers (`/api/v1`)
  - Add global exception handlers

- [x] Create `api/schemas/` (Pydantic DTOs):
  - `common.py`: ResponseEnvelope, PaginationMeta, ErrorDetail
  - `country.py`: CountryResponse
  - `indicator.py`: IndicatorResponse, TimeseriesData
  - `chat.py`: ChatRequest, ChatResponse, WebSocket messages

### 4.2 Standard REST Endpoints (Data API)

**Priority**: HIGH  
**Estimated Time**: 6 hours  
**Status**: ✅ COMPLETED

- [x] Create `api/routers/countries.py`:
  - `GET /countries`: List countries with pagination
  - `GET /countries/{code}`: Country details

- [x] Create `api/routers/indicators.py`:
  - `GET /indicators/catalog`: List indicators
  - `GET /indicators/{code}/metadata`: Indicator metadata

- [x] Create `api/routers/timeseries.py`:
  - `GET /timeseries`: Fetch timeseries data (filter by country, indicator, years)

- [x] Write integration tests via `FastAPI.TestClient` mocking Repository

### 4.3 Search API (Lexical + Semantic)

**Priority**: HIGH  
**Estimated Time**: 5 hours  
**Status**: ✅ COMPLETED

- [x] Create `api/routers/search.py`:
  - `GET /search/indicators`: Implement lexical + semantic search
  - Combine results from `repository.search_indicators_lexical` and `repository.search_indicators_semantic`
  - Rank and merge results

- [x] Write integration tests for search endpoints

### 4.4 RAG Engine Setup

**Priority**: CRITICAL  
**Estimated Time**: 8 hours  
**Status**: ✅ COMPLETED

- [x] Create `src/intelligence/query_parser.py`:
  - Implement `normalize_query(query)` to extract entities (country codes, years)

- [x] Create `src/intelligence/context_builder.py`:
  - Implement logic to fetch fact data based on search results
  - Format data as markdown tables for LLM consumption

- [x] Create `src/intelligence/gemini_client.py`:
  - Setup GenerativeModel (`gemini-2.5-pro`)
  - Define strict System Prompt restricting answers to provided context
  - Implement `generate_answer(query, context)` and `generate_answer_stream(query, context)`

### 4.5 Chatbot APIs (REST & WebSocket)

**Priority**: CRITICAL  
**Estimated Time**: 8 hours  
**Status**: ✅ COMPLETED

- [x] Create `api/routers/chat.py`:
  - Implement `POST /chat`: REST fallback for RAG pipeline
  - Implement `WS /chat`: WebSocket endpoint for streaming response

- [x] Build WebSocket Streaming Logic:
  - Normalize query -> Search -> Assemble Context -> Call Gemini (stream=True)
  - Yield tokens to WebSocket client
  - Extract and send citations (`IND:...`) format

- [x] Write tests for chat endpoints:
  - Mock Gemini API heavily to avoid external calls during tests

### 4.6 Verification & Testing

**Priority**: CRITICAL  
**Estimated Time**: 4 hours  
**Status**: ✅ COMPLETED

- [x] Run complete API test suite (32 tests pass)
- [x] Test API manually using Swagger UI (`/docs`)
- [x] Code style and linting (ruff format & ruff check)

---

## Success Criteria

✅ FastAPI application running and serving endpoints  
✅ Core REST APIs (countries, indicators, timeseries) returning correct data formats  
✅ Search API successfully combining lexical and vector search  
✅ RAG pipeline retrieving accurate context from database  
✅ Chat WebSocket streaming LLM responses with citations  

---

## Next Phase

→ [PHASE-5-ORCHESTRATION.md](PHASE-5-ORCHESTRATION.md) — Orchestration (Airflow)