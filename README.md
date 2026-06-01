# Intelligent Data Platform (IDP)

Intelligent Data Platform (IDP) for economic data with World Bank focus. Built on a single-node, cloud-ready 5-layer Medallion architecture.

## Architecture

1. **Bronze**: MinIO (Raw data)
2. **Silver/Gold**: DuckDB + dbt (Transformations)
3. **Serving**: PostgreSQL + pgvector (Data warehouse & Embeddings)
4. **Intelligence**: FastAPI + Gemini (AI workflows)
5. **Orchestration**: Apache Airflow 3.0

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker & Docker Compose
- `uv` package manager

### 2. Setup Environment

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your Gemini API key and other secrets
```

### 3. Start Infrastructure

```bash
# Start MinIO, PostgreSQL, and Airflow
docker compose up -d

# Verify services
./scripts/health_check.sh
```

### 4. Development Commands

```bash
uv run pytest              # Run tests
uv run ruff check .        # Lint code
uv run ruff format .       # Format code
uv run mypy .              # Type check
```

## Services

- MinIO Console: http://localhost:9001 (minioadmin / minioadmin)
- Airflow UI: http://localhost:8080 (admin / admin)
- PostgreSQL: `localhost:5432` (idp_user / changeme)
