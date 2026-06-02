# Layer 5 — Orchestration & Ops

## Objectives & Tooling

Layer 5 coordinates pipelines and ensures operational robustness:

- **Apache Airflow 2.10.3** orchestrates DAGs for ingestion, transformation, export, and embeddings.
- **Docker Compose** defines service containers and resource limits.
- **Nginx** (optional, deferred) provides secure external access.
- **Prometheus/Grafana** (optional, deferred) collect metrics and display dashboards.

Environment configuration describes ports, networks, volumes, env vars, and security checklist.

## World Bank DAG

The `world_bank_pipeline` DAG orchestrates the full data flow:

1. `ingest_bronze_data`: run the Python connector to pull new World Bank data into MinIO Bronze.
2. `dbt_run`: run `dbt run` for `stg_world_bank__indicators` and Gold models.
3. `dbt_test`: run `dbt test` to enforce data quality.
4. `export_to_serving`: export Gold from DuckDB to PostgreSQL.
5. `generate_embeddings`: update embeddings via Gemini API.

Tasks run sequentially with `catchup=False` and `max_active_runs=1` to ensure idempotency.

**Callbacks**: Task and DAG-level failure/success callbacks log to stdout (see `src/idp/orchestration/callbacks.py`). Email/Slack/PagerDuty integrations are TODO placeholders.

## Docker Compose Setup

The core infrastructure is defined in `docker-compose.yml` to run on a single machine:

```yaml
version: '3.8'

services:
  # MinIO for Bronze layer
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=${MINIO_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_PASSWORD}
    volumes:
      - minio_data:/data

  # PostgreSQL for Storage & Serving layer
  postgres:
    image: pgvector/pgvector:pg16
    ports:
      - "5433:5432"
    environment:
      - POSTGRES_USER=${PG_USER}
      - POSTGRES_PASSWORD=${PG_PASSWORD}
      - POSTGRES_DB=${PG_DB}
    volumes:
      - pg_data:/var/lib/postgresql/data

  # Apache Airflow 2.10.3 for Orchestration
  airflow-webserver:
    image: apache/airflow:2.10.3-python3.11
    command: webserver
    ports:
      - "8080:8080"
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://${PG_USER}:${PG_PASSWORD}@postgres:5432/${PG_DB}
    depends_on:
      - postgres
    volumes:
      - ./airflow/dags:/opt/airflow/dags
      - ./src:/opt/airflow/src

  airflow-scheduler:
    image: apache/airflow:2.10.3-python3.11
    command: scheduler
    depends_on:
      - airflow-webserver
    volumes:
      - ./airflow/dags:/opt/airflow/dags
      - ./src:/opt/airflow/src
      - ./dbt:/opt/airflow/dbt

  # FastAPI for Intelligence layer
  api:
    build:
      context: ./docker
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://${PG_USER}:${PG_PASSWORD}@postgres:5432/${PG_DB}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - postgres

volumes:
  minio_data:
  pg_data:
```

## Security & Operations

### Security Checklist
- Secure MinIO access with strong credentials and IAM policies
- PostgreSQL access limited to application services (FastAPI, Airflow)
- Encrypt Gemini API key and other secrets using environment variables or a secret manager
- Limit Docker container resources to prevent memory exhaustion on the 16GB RAM server

### Backup Policies
- Scheduled backups for PostgreSQL data (Gold layer & Embeddings)
- MinIO Bronze data mirrored/backed up periodically
- Airflow metadata database backed up daily

See [docs/OPERATIONS.md](../OPERATIONS.md) for detailed backup/restore procedures.
