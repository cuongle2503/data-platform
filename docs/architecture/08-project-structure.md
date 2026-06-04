# Project Structure

The Intelligent Data Platform (IDP) uses a modern Python "src-layout" to prevent import errors and clarify the separation of concerns. The structure aligns with the 5-layer Medallion architecture.

## Root Directory

```
data-platform/
├── pyproject.toml          # Workspace config and dependencies (uv + PEP 621)
├── uv.lock                 # Lockfile for deterministic builds
├── .env                    # Environment variables (not committed)
├── CLAUDE.md               # Project instructions for Claude AI
├── docker-compose.yml      # Infrastructure setup (MinIO, PostgreSQL, Airflow)
├── README.md               # Quick start guide
├── docs/                   # Architecture and phase planning
├── dbt/                    # dbt-core project for Silver/Gold transformations
├── airflow/                # Airflow 2.10.3 DAGs and plugins
├── scripts/                # Utility scripts (init-db.sql, health checks)
├── tests/                  # Unit, integration, and pipeline tests
├── data/                   # Local storage mounts (bronze, silver, gold)
└── src/                    # Application source code
    └── idp/                # Main Python package
```

## Source Code Layout (`src/idp/`)

The `src/idp/` package is structured around the 5 layers:

```
src/idp/
├── __init__.py
├── main.py                 # CLI entry point (`idp` command)
│
├── ingestion/              # Layer 1: Data extraction & MinIO upload
│   ├── __init__.py
│   ├── clients/            # API clients (World Bank API, HTTP client)
│   ├── extractors/         # Extraction logic
│   └── loaders/            # Upload to MinIO (Bronze)
│
├── transformation/         # Layer 2: DuckDB + dbt orchestration
│   ├── __init__.py
│   ├── exporters.py        # DuckDB to PostgreSQL export logic
│   └── runners.py          # dbt command wrappers
│
├── storage/                # Layer 3: PostgreSQL & Repository Pattern
│   ├── __init__.py
│   ├── database.py         # DB connection & connection pooling
│   └── repositories/       # Data access objects (Repository pattern)
│
├── intelligence/           # Layer 4: RAG, Embeddings, Gemini integration
│   ├── __init__.py
│   ├── embeddings.py       # pgvector and Gemini embedding logic
│   ├── rag.py              # Retrieval-Augmented Generation pipeline
│   ├── vector_search.py    # Semantic and lexical search execution
│   └── prompts/            # System prompts for the LLM
│
├── api/                    # Layer 4 API: FastAPI
│   ├── __init__.py
│   ├── server.py           # FastAPI app initialization
│   ├── dependencies.py     # FastAPI dependencies (DB, services)
│   ├── routers/            # REST and WebSocket endpoints
│   └── schemas/            # Pydantic DTOs for request/response
│
└── common/                 # Cross-cutting concerns
    ├── __init__.py
    ├── config.py           # pydantic-settings (Env vars parsing)
    ├── exceptions.py       # Custom error types
    ├── logging.py          # Structured logging
    └── security.py         # Auth validation
```

## Architectural Patterns

### 1. Repository Pattern
We use the **Repository Pattern** to decouple the core logic from database queries:
- `api/routers/` handles HTTP requests and input validation via Pydantic schemas.
- `api/routers/` calls use cases or repository functions.
- `storage/repositories/` handles all SQL construction (using parameterized queries).
- Abstract Interfaces (Protocol) ensure we can test APIs with mock repositories.

### 2. Immutability & DTOs
- `api/schemas/` uses Pydantic models for data validation.
- Internal data transfer uses `@dataclass(frozen=True)`.

### 3. Configuration Management
- `pydantic-settings` is used in `src/idp/common/config.py` to validate and load configurations from `.env`.
- Secrets are NEVER hardcoded.

### 4. Dependency Management
- `uv` is the package manager.
- `pyproject.toml` handles dependencies.
- `hatchling` handles the build system for the `idp` package (`src/` layout).
