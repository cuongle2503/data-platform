# Phase 0: Project Setup & Infrastructure

**Duration**: 2-3 days  
**Goal**: Establish development environment, project structure, and core infrastructure services

---

## Prerequisites Checklist

- [x] Python 3.11+ installed
- [x] Docker & Docker Compose installed
- [x] `uv` package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [x] Git configured with user name and email
- [x] Access to server (16GB RAM, 512GB SSD)
- [x] Gemini API key obtained from Google AI Studio

---

## Task List

### 0.1 Project Structure Setup

**Priority**: CRITICAL  
**Estimated Time**: 2 hours

- [ ] Create project directory structure:
  ```
  data-platform/
  ├── src/
  │   ├── ingestion/
  │   ├── transformation/
  │   ├── storage/
  │   ├── intelligence/
  │   └── common/
  ├── dbt/
  ├── airflow/
  │   └── dags/
  ├── api/
  ├── tests/
  │   ├── unit/
  │   ├── integration/
  │   └── pipeline/
  ├── scripts/
  ├── data/
  │   ├── bronze/
  │   ├── silver/
  │   └── gold/
  ├── docs/
  └── docker/
  ```

- [ ] Initialize `pyproject.toml` with uv:
  ```bash
  uv init
  ```

- [ ] Configure `pyproject.toml` with core dependencies:
  - `fastapi[standard]>=0.115.0`
  - `uvicorn[standard]>=0.32.0`
  - `psycopg[binary]>=3.2.0`
  - `duckdb>=1.1.0`
  - `pyarrow>=18.0.0`
  - `polars>=1.15.0`
  - `httpx>=0.28.0`
  - `pydantic>=2.10.0`
  - `pydantic-settings>=2.6.0`
  - `google-generativeai>=0.8.0`
  - `pgvector>=0.3.0`
  - `apache-airflow>=3.0.0`
  - `minio>=7.2.0`

- [ ] Add dev dependencies:
  - `pytest>=8.3.0`
  - `pytest-asyncio>=0.24.0`
  - `pytest-cov>=6.0.0`
  - `ruff>=0.8.0`
  - `mypy>=1.13.0`
  - `pre-commit>=4.0.0`

- [ ] Run `uv sync` to install all dependencies

- [ ] Create `.gitignore`:
  ```
  __pycache__/
  *.py[cod]
  .venv/
  .env
  .env.local
  *.duckdb
  *.duckdb.wal
  data/bronze/*
  data/silver/*
  data/gold/*
  .pytest_cache/
  .coverage
  .mypy_cache/
  .ruff_cache/
  ```

### 0.2 Code Quality Tools Configuration

**Priority**: HIGH  
**Estimated Time**: 1 hour

- [ ] Create `ruff.toml`:
  ```toml
  line-length = 100
  target-version = "py311"
  
  [lint]
  select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
  ignore = ["E501"]
  
  [format]
  quote-style = "double"
  indent-style = "space"
  ```

- [ ] Create `mypy.ini`:
  ```ini
  [mypy]
  python_version = 3.11
  strict = True
  warn_return_any = True
  warn_unused_configs = True
  disallow_untyped_defs = True
  ```

- [ ] Create `.pre-commit-config.yaml`:
  ```yaml
  repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.8.0
      hooks:
        - id: ruff
          args: [--fix]
        - id: ruff-format
  ```

- [ ] Install pre-commit hooks: `pre-commit install`

- [ ] Test code quality tools:
  ```bash
  uv run ruff check .
  uv run ruff format .
  uv run mypy .
  ```

### 0.3 Environment Configuration

**Priority**: CRITICAL  
**Estimated Time**: 30 minutes

- [ ] Create `.env.example`:
  ```bash
  # MinIO (Bronze Layer)
  MINIO_ENDPOINT=localhost:9000
  MINIO_ACCESS_KEY=minioadmin
  MINIO_SECRET_KEY=minioadmin
  MINIO_SECURE=false
  MINIO_BUCKET_BRONZE=bronze
  
  # PostgreSQL (Gold Layer)
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5432
  POSTGRES_DB=idp
  POSTGRES_USER=idp_user
  POSTGRES_PASSWORD=changeme
  DATABASE_URL=postgresql://idp_user:changeme@localhost:5432/idp
  
  # DuckDB (Transformation Layer)
  DUCKDB_PATH=data/gold.duckdb
  
  # Gemini API
  GEMINI_API_KEY=your_api_key_here
  GEMINI_EMBEDDING_MODEL=text-embedding-004
  GEMINI_CHAT_MODEL=gemini-2.0-flash
  
  # Airflow
  AIRFLOW__CORE__EXECUTOR=LocalExecutor
  AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql://idp_user:changeme@localhost:5432/airflow
  AIRFLOW__CORE__LOAD_EXAMPLES=False
  
  # API
  API_HOST=0.0.0.0
  API_PORT=8000
  API_RELOAD=true
  LOG_LEVEL=INFO
  ```

- [ ] Copy to `.env`: `cp .env.example .env`

- [ ] Update `.env` with actual credentials (especially `GEMINI_API_KEY`)

- [ ] Create `src/common/config.py` for centralized config management using `pydantic-settings`

### 0.4 Docker Infrastructure Setup

**Priority**: CRITICAL  
**Estimated Time**: 2 hours

- [ ] Create `docker-compose.yml`:
  ```yaml
  version: '3.8'
  
  services:
    minio:
      image: minio/minio:latest
      container_name: idp-minio
      command: server /data --console-address ":9001"
      ports:
        - "9000:9000"
        - "9001:9001"
      environment:
        - MINIO_ROOT_USER=${MINIO_ACCESS_KEY}
        - MINIO_ROOT_PASSWORD=${MINIO_SECRET_KEY}
      volumes:
        - minio_data:/data
      healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
        interval: 30s
        timeout: 10s
        retries: 3
  
    postgres:
      image: pgvector/pgvector:pg16
      container_name: idp-postgres
      ports:
        - "5432:5432"
      environment:
        - POSTGRES_USER=${POSTGRES_USER}
        - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
        - POSTGRES_DB=${POSTGRES_DB}
      volumes:
        - postgres_data:/var/lib/postgresql/data
        - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
        interval: 10s
        timeout: 5s
        retries: 5
  
    airflow-init:
      image: apache/airflow:3.0.0-python3.11
      container_name: idp-airflow-init
      environment:
        - AIRFLOW__CORE__EXECUTOR=LocalExecutor
        - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN}
        - AIRFLOW__CORE__LOAD_EXAMPLES=False
      command: >
        bash -c "airflow db init &&
                 airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com"
      depends_on:
        postgres:
          condition: service_healthy
  
    airflow-webserver:
      image: apache/airflow:3.0.0-python3.11
      container_name: idp-airflow-webserver
      command: webserver
      ports:
        - "8080:8080"
      environment:
        - AIRFLOW__CORE__EXECUTOR=LocalExecutor
        - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN}
        - AIRFLOW__CORE__LOAD_EXAMPLES=False
      volumes:
        - ./airflow/dags:/opt/airflow/dags
        - ./airflow/logs:/opt/airflow/logs
      depends_on:
        - airflow-init
        - postgres
  
    airflow-scheduler:
      image: apache/airflow:3.0.0-python3.11
      container_name: idp-airflow-scheduler
      command: scheduler
      environment:
        - AIRFLOW__CORE__EXECUTOR=LocalExecutor
        - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN}
        - AIRFLOW__CORE__LOAD_EXAMPLES=False
      volumes:
        - ./airflow/dags:/opt/airflow/dags
        - ./airflow/logs:/opt/airflow/logs
      depends_on:
        - airflow-init
        - postgres
  
  volumes:
    minio_data:
    postgres_data:
  ```

- [ ] Create `scripts/init-db.sql`:
  ```sql
  -- Enable pgvector extension
  CREATE EXTENSION IF NOT EXISTS vector;
  
  -- Create schemas
  CREATE SCHEMA IF NOT EXISTS bronze;
  CREATE SCHEMA IF NOT EXISTS silver;
  CREATE SCHEMA IF NOT EXISTS gold;
  CREATE SCHEMA IF NOT EXISTS embeddings;
  
  -- Create Airflow database
  CREATE DATABASE airflow;
  ```

- [ ] Start infrastructure services:
  ```bash
  docker compose up -d
  ```

- [ ] Verify services are running:
  ```bash
  docker compose ps
  ```

- [ ] Access MinIO console: http://localhost:9001 (minioadmin/minioadmin)

- [ ] Create `bronze` bucket in MinIO via console or CLI

- [ ] Access Airflow UI: http://localhost:8080 (admin/admin)

- [ ] Verify PostgreSQL connection:
  ```bash
  psql postgresql://idp_user:changeme@localhost:5432/idp -c "SELECT version();"
  ```

### 0.5 Testing Infrastructure Setup

**Priority**: HIGH  
**Estimated Time**: 1.5 hours

- [ ] Create `pytest.ini`:
  ```ini
  [pytest]
  testpaths = tests
  python_files = test_*.py
  python_classes = Test*
  python_functions = test_*
  addopts = 
      --strict-markers
      --cov=src
      --cov-report=term-missing
      --cov-report=html
      --cov-fail-under=80
  markers =
      unit: Unit tests
      integration: Integration tests
      pipeline: Pipeline tests
      slow: Slow tests
  ```

- [ ] Create `tests/conftest.py` with shared fixtures:
  ```python
  import pytest
  from pathlib import Path
  
  @pytest.fixture
  def test_data_dir() -> Path:
      return Path(__file__).parent / "data"
  
  @pytest.fixture
  def mock_env(monkeypatch):
      monkeypatch.setenv("POSTGRES_HOST", "localhost")
      monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
      # Add other env vars
  ```

- [ ] Create sample test file `tests/unit/test_sample.py`:
  ```python
  def test_sample():
      assert 1 + 1 == 2
  ```

- [ ] Run tests to verify setup:
  ```bash
  uv run pytest
  ```

- [ ] Verify coverage report generated in `htmlcov/`

### 0.6 Logging & Monitoring Setup

**Priority**: MEDIUM  
**Estimated Time**: 1 hour

- [ ] Create `src/common/logging_config.py`:
  ```python
  import logging
  import sys
  from pathlib import Path
  
  def setup_logging(log_level: str = "INFO") -> None:
      """Configure structured logging for the application."""
      log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
      
      logging.basicConfig(
          level=getattr(logging, log_level.upper()),
          format=log_format,
          handlers=[
              logging.StreamHandler(sys.stdout),
              logging.FileHandler("logs/app.log")
          ]
      )
  ```

- [ ] Create `logs/` directory: `mkdir -p logs`

- [ ] Add `logs/*.log` to `.gitignore`

- [ ] Create health check script `scripts/health_check.sh`:
  ```bash
  #!/bin/bash
  set -e
  
  echo "Checking MinIO..."
  curl -f http://localhost:9000/minio/health/live || exit 1
  
  echo "Checking PostgreSQL..."
  pg_isready -h localhost -p 5432 -U idp_user || exit 1
  
  echo "Checking Airflow..."
  curl -f http://localhost:8080/health || exit 1
  
  echo "All services healthy!"
  ```

- [ ] Make script executable: `chmod +x scripts/health_check.sh`

- [ ] Test health check: `./scripts/health_check.sh`

### 0.7 Documentation & Memory Setup

**Priority**: MEDIUM  
**Estimated Time**: 30 minutes

- [ ] Create `README.md` with quick start guide

- [ ] Create `.claude/projects/-home-pc-my-projects-data-platform/memory/` directory

- [ ] Create initial memory file for project context:
  ```markdown
  ---
  name: project-architecture
  description: IDP 5-layer Medallion architecture overview
  metadata:
    type: project
  ---
  
  IDP follows 5-layer Medallion: Bronze (MinIO) → Silver/Gold (DuckDB+dbt) → 
  Serving (PostgreSQL+pgvector) → Intelligence (FastAPI+Gemini) → 
  Orchestration (Airflow). World Bank focus, single-node first.
  
  **Why:** Lean stack, open-source first, maximize single-node before scaling.
  **How to apply:** Always consider layer boundaries when adding features.
  ```

- [ ] Update `MEMORY.md` index

### 0.8 Verification & Smoke Tests

**Priority**: CRITICAL  
**Estimated Time**: 1 hour

- [ ] Run full verification checklist:
  - [ ] `uv sync` completes without errors
  - [ ] `uv run ruff check .` passes
  - [ ] `uv run ruff format .` runs successfully
  - [ ] `uv run mypy .` passes (may have warnings initially)
  - [ ] `uv run pytest` passes with >80% coverage
  - [ ] All Docker services running: `docker compose ps`
  - [ ] MinIO accessible and `bronze` bucket exists
  - [ ] PostgreSQL accessible with schemas created
  - [ ] Airflow UI accessible
  - [ ] Health check script passes

- [ ] Create initial commit:
  ```bash
  git add .
  git commit -m "chore: phase 0 setup — infrastructure and tooling"
  ```

- [ ] Tag the phase:
  ```bash
  git tag phase-0-complete
  ```

---

## Success Criteria

✅ All services running in Docker  
✅ Python environment configured with uv  
✅ Code quality tools (ruff, mypy, pytest) working  
✅ Database schemas created  
✅ MinIO bucket created  
✅ Airflow accessible  
✅ Tests passing with >80% coverage  
✅ Documentation updated  

---

## Next Phase

→ [PHASE-1-INGESTION.md](PHASE-1-INGESTION.md) — World Bank API ingestion to Bronze layer
