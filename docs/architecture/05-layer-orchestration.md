# Layer 5 — Orchestration & Ops

## Objectives & Tooling

Layer 5 coordinates pipelines and ensures operational robustness:

- **Airflow 3.0** orchestrates DAGs for ingestion, transformation, export, and embeddings.
- **Docker Compose** defines service containers and resource limits.
- **Nginx** (optional) provides secure external access.
- **Prometheus/Grafana** (optional) collect metrics and display dashboards.

Environment configuration describes ports, networks, volumes, env vars, and security checklist.

## World Bank DAG

An example World Bank DAG:

1. `world_bank_ingest`: run the Python connector to pull new World Bank data into Bronze.
2. `dbt_run_world_bank`: run `dbt run` for `stg_world_bank__indicators` and Gold models.
3. `dbt_test_world_bank`: run `dbt test` to enforce data quality.
4. `export_gold_world_bank`: export Gold from DuckDB to PostgreSQL.
5. `refresh_embeddings_world_bank`: update embeddings.

## Docker Compose Setup

The core infrastructure is defined in a `docker-compose.yml` file to run on a single machine:

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
      - "5432:5432"
    environment:
      - POSTGRES_USER=${PG_USER}
      - POSTGRES_PASSWORD=${PG_PASSWORD}
      - POSTGRES_DB=${PG_DB}
    volumes:
      - pg_data:/var/lib/postgresql/data

  # Airflow 3.0 for Orchestration
  airflow-webserver:
    image: apache/airflow:3.0.0
    command: webserver
    ports:
      - "8080:8080"
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://${PG_USER}:${PG_PASSWORD}@postgres:5432/airflow
    depends_on:
      - postgres

  airflow-scheduler:
    image: apache/airflow:3.0.0
    command: scheduler
    depends_on:
      - airflow-webserver

  # FastAPI for Intelligence layer
  api:
    build:
      context: ./api
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