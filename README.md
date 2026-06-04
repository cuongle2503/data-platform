# Intelligent Data Platform (IDP)

Intelligent Data Platform (IDP) for economic data with World Bank focus. Built on a single-node, cloud-ready 5-layer Medallion architecture.

## Architecture

1. **Bronze**: MinIO (Raw data from World Bank API)
2. **Silver/Gold**: DuckDB + dbt (Transformations & dimensional modeling)
3. **Serving**: PostgreSQL + pgvector (Data warehouse & Vector Embeddings)
4. **Intelligence**: FastAPI + Gemini (RAG Chatbot & timeseries API)
5. **Orchestration**: Apache Airflow 2.10.3 (End-to-end data pipeline)

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
# Edit .env with your Gemini API key and proxy settings if required
```

### 3. Start Infrastructure

The full stack (MinIO, PostgreSQL, Airflow, and FastAPI) runs via Docker Compose:

```bash
# Start all services in the background
docker compose up -d

# Check running containers
docker compose ps
```

### 4. Running the Pipeline

The IDP is fully orchestrated by Airflow. To populate data into the platform:

1. Navigate to the Airflow UI: http://localhost:8080 (admin / admin)
2. Turn on the `world_bank_pipeline` DAG toggle
3. Trigger the DAG manually by clicking the "Play" button -> "Trigger DAG"
4. Wait for all 5 tasks to complete: Ingest -> dbt run -> dbt test -> Export -> Embeddings

### 5. Accessing the Platform

Once the pipeline completes, the data is available for querying:

- **API Swagger Docs**: http://localhost:8000/docs
- **Chatbot Endpoint**: `POST http://localhost:8000/api/v1/chat`
- **Search Endpoint**: `GET http://localhost:8000/api/v1/search/indicators?q=GDP`

**Service Access:**
- MinIO Console: http://localhost:9001 (minioadmin / minioadmin)
- Airflow UI: http://localhost:8080 (admin / admin)
- PostgreSQL: `localhost:5433` (idp_user / changeme)

## Testing

### Unit & Integration Tests

```bash
uv run pytest                    # Run all tests
uv run pytest -m "not slow"      # Fast tests only
uv run pytest -m "unit"          # Unit tests
uv run pytest -m "integration"   # Integration tests
uv run pytest tests/e2e_pipeline.py  # E2E pipeline workflow test
```

### Code Quality

```bash
uv run ruff check .              # Lint
uv run ruff format .             # Format
uv run mypy .                    # Type check
```

## Monitoring & Alerting

The `world_bank_pipeline` DAG includes failure/success callbacks (`src/idp/orchestration/callbacks.py`).
Add email/Slack integrations by editing the TODO sections in the callback functions.

Airflow UI: http://localhost:8080 (admin / admin)

## Operations

See [docs/OPERATIONS.md](docs/OPERATIONS.md) for backup, restore, scaling, and troubleshooting instructions.