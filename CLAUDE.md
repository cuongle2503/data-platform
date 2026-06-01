# CLAUDE.md — Data Platform

Intelligent Data Platform (IDP) for economic data — World Bank focus, single-node first, cloud-ready.

## Architecture

**5-layer Medallion**: Bronze (MinIO) → Silver/Gold (DuckDB+dbt) → Serving (PostgreSQL+pgvector) → Intelligence (FastAPI+Gemini) → Orchestration (Airflow)

See `docs/README.md` for complete index.
- `docs/architecture/` — System design, 5-layer specs, API design, tech stack
- `docs/phases/` — Detailed step-by-step implementation plans (Start at PHASE-0-SETUP.md)

## Stack

- **Python** >=3.11, **uv** (package manager)
- **MinIO** (Bronze), **DuckDB+dbt** (transform), **PostgreSQL 16+pgvector** (Gold+embeddings)
- **FastAPI** (API), **Gemini** (LLM/embeddings), **Airflow 3.0** (orchestration)
- **ruff** (lint/format), **mypy** (types), **pytest** (tests)

## Commands

```bash
uv sync                    # Install deps
uv run pytest              # Run tests
uv run ruff check .        # Lint
uv run ruff format .       # Format
uv run mypy .              # Type check
cd dbt && dbt run && dbt test  # Transform + test
docker compose up -d       # Start services
```

## Code Style

- PEP 8, line length 100, type annotations required (mypy strict)
- `snake_case` (vars/funcs), `PascalCase` (classes), `UPPER_SNAKE_CASE` (constants)
- Frozen dataclasses for DTOs, context managers for resources
- Use `logging`, not `print()`

## Key Conventions

- **Idempotent pipelines**: safe to rerun, no duplicates
- **Parameterized queries**: never string interpolation
- **Secrets in env vars**: no hardcoded credentials
- **dbt models**: file name = model name, use `ref()` not table names
- **80% test coverage**: unit + integration + pipeline tests

## Environment / Proxy Config

**CRITICAL**: This environment requires proxy settings for external requests.
- **Localhost connections** (MinIO, Postgres, local services) **MUST NOT** pass through proxy (use `NO_PROXY=localhost,127.0.0.1,minio,postgres`).
- **External requests** (World Bank API, Gemini API, external packages) **MUST** pass through the proxy using `HTTP_PROXY` / `HTTPS_PROXY` environment variables.
- Always include these proxy variables in Docker containers and HTTP client configurations (`httpx.AsyncClient(proxies=...)`).

## Project Status (2026-06-01)

**Current**: Architecture docs complete, no code yet
**Next**: Implement Layer 1 (World Bank ingestion to MinIO Bronze)
