# IDP Operations Guide

This document outlines standard operating procedures for the Intelligent Data Platform (IDP) including backup, restore, scaling, and troubleshooting.

## 1. Pipeline Execution

The primary orchestrator for the IDP is Apache Airflow.

### Managing Airflow

Access the Airflow Webserver at `http://localhost:8080`.
Default credentials are `admin` / `admin` (configure via `.env` in production).

**Manually triggering the pipeline:**
1. Navigate to the DAGs page.
2. Find `world_bank_pipeline`.
3. Click the "Play" button under Actions and select "Trigger DAG".

### Idempotency

The entire pipeline is built to be idempotent. Rerunning a failed or successful pipeline for a given time period will not duplicate data. 
- MinIO (Bronze): Overwrites data files for identical paths.
- DuckDB (Silver/Gold): Full refresh or idempotent MERGE operations.
- PostgreSQL (Serving): Uses `ON CONFLICT DO UPDATE` for indicators and embeddings.

---

## 2. Backup & Restore Procedures

### 2.1 PostgreSQL (Serving Layer & Airflow Metadata)

**Backup:**
Run `pg_dump` from within the PostgreSQL container:
```bash
docker exec -t idp-postgres pg_dump -U idp_user -d idp -F c -f /tmp/idp_backup.dump
docker cp idp-postgres:/tmp/idp_backup.dump ./backups/idp_backup_$(date +%Y%m%d).dump
```

**Restore:**
```bash
docker cp ./backups/idp_backup_20260601.dump idp-postgres:/tmp/
docker exec -t idp-postgres pg_restore -U idp_user -d idp -1 -c /tmp/idp_backup_20260601.dump
```

### 2.2 MinIO (Bronze Layer)

MinIO data persists in the `minio_data` Docker volume.

**Backup (using mc client):**
```bash
mc alias set idp_minio http://localhost:9000 minioadmin minioadmin
mc cp --recursive idp_minio/bronze ./backups/bronze_$(date +%Y%m%d)
```

**Restore:**
```bash
mc cp --recursive ./backups/bronze_20260601/ idp_minio/bronze
```

### 2.3 DuckDB

The DuckDB database is stored as a file in `data/gold.duckdb`. 
Simply copy the file to back it up:
```bash
cp data/gold.duckdb backups/gold_$(date +%Y%m%d).duckdb
```

---

## 3. Logs & Monitoring

### Component Logs

View logs via Docker Compose:

```bash
# All logs
docker compose logs -f

# Specific component logs
docker compose logs -f api
docker compose logs -f airflow-scheduler
docker compose logs -f postgres
```

### Airflow Logs

Task logs are persisted in `airflow/logs/` and can be viewed directly in the Airflow UI:
1. Click on a specific task instance in the DAG run.
2. Click the "Log" tab.

### Common Troubleshooting

**1. "MinIO connection refused"**
- Check if container is running: `docker compose ps minio`
- Verify proxy settings: Ensure `NO_PROXY` includes `minio` and `localhost`.

**2. "PostgreSQL password authentication failed"**
- Verify `.env` credentials match `docker-compose.yml` defaults.
- If changed after initial startup, the volume retains the old password. Drop the `postgres_data` volume and restart.

**3. "API /chat endpoint timeouts"**
- The Gemini API requires external internet access.
- Check that `HTTP_PROXY` and `HTTPS_PROXY` are correctly injected into the `idp-api` container.
- Check Gemini API key validity and quota.

**4. "Airflow DAG parsing errors"**
- Check the Airflow UI "Import Errors" banner.
- Usually caused by missing Python dependencies or incorrect file paths. Ensure `/opt/airflow/src` is in the `PYTHONPATH`.

---

## 4. Scaling

Currently, the IDP is designed as a single-node deployment (Docker Compose). 

To scale out for production:
1. Replace local MinIO with AWS S3, Google GCS, or Azure Blob Storage.
2. Replace local PostgreSQL with a managed service (e.g., AWS RDS PostgreSQL with pgvector extension).
3. Deploy FastAPI on a container orchestrator (Kubernetes, AWS ECS) behind a load balancer.
4. Deploy Airflow using the official Helm chart on Kubernetes, switching from `LocalExecutor` to `CeleryExecutor` or `KubernetesExecutor`.