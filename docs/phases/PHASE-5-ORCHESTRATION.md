# Phase 5: Orchestration & Ops

**Duration**: 3-5 days  
**Goal**: Automate the entire pipeline using Airflow 3.0, schedule regular data updates, and finalize deployment configurations.

---

## Prerequisites Checklist
- [ ] Phase 1-4 completed (Ingestion, Transformation, Storage, API)
- [ ] Airflow 3.0 running in Docker
- [ ] Airflow connected to PostgreSQL metadata db

---

## Task List

### 5.1 Airflow Project Structure

**Priority**: CRITICAL  
**Estimated Time**: 2 hours

- [ ] Set up `airflow/dags/` structure
- [ ] Set up `airflow/plugins/` (if custom operators needed)
- [ ] Create `airflow/dags/world_bank_pipeline.py`

### 5.2 Airflow Operators & Tasks

**Priority**: HIGH  
**Estimated Time**: 6 hours

- [ ] Implement Ingestion Task:
  - Create `PythonOperator` calling `src/ingestion/world_bank/pipeline.py`
  - Handle idempotency flags

- [ ] Implement dbt Transformation Tasks:
  - Use `BashOperator` to run `dbt run` and `dbt test` in `dbt/` dir
  - Alternatively, use `Cosmos` or `Airflow dbt operator` if preferred

- [ ] Implement Export Task:
  - Create `PythonOperator` calling `src/transformation/exporter.py`

- [ ] Implement Embeddings Task:
  - Create `PythonOperator` calling `src/storage/generate_indicator_embeddings.py`

### 5.3 DAG Definition

**Priority**: CRITICAL  
**Estimated Time**: 4 hours

- [ ] Define DAG `world_bank_pipeline`:
  - Schedule: `@monthly` or `@weekly`
  - Retries: 2, Retry Delay: 5 minutes
  - Define task dependencies: `Ingest -> dbt run -> dbt test -> Export -> Update Embeddings`

- [ ] Create monitoring/alerting logic:
  - Configure Airflow email or Slack alerts on task failure

### 5.4 Docker & Deployment Finalization

**Priority**: HIGH  
**Estimated Time**: 4 hours

- [ ] Review `docker-compose.yml`:
  - Ensure API service correctly defined and depending on PostgreSQL
  - Ensure volumes configured correctly for data persistence

- [ ] Create `docker/Dockerfile.api`:
  - Optimize API image build (multi-stage, non-root user)
  - Run with uvicorn workers

- [ ] Create Nginx config (optional, for proxying):
  - Setup basic reverse proxy to FastAPI and Airflow Webserver

### 5.5 End-to-End Pipeline Testing

**Priority**: CRITICAL  
**Estimated Time**: 6 hours

- [ ] Trigger DAG manually from Airflow UI
- [ ] Monitor logs for all 5 steps
- [ ] Verify MinIO Bronze data updated
- [ ] Verify DuckDB Gold models created
- [ ] Verify PostgreSQL data populated
- [ ] Verify Embeddings created
- [ ] Hit API endpoints to confirm data is visible and Chatbot works with new data

### 5.6 Project Handoff & Documentation

**Priority**: MEDIUM  
**Estimated Time**: 2 hours

- [ ] Update `README.md` with full deployment and running instructions
- [ ] Create `docs/OPERATIONS.md`:
  - Backup/Restore procedures (pg_dump, MinIO replication)
  - Log locations
  - Common troubleshooting

---

## Success Criteria

✅ Airflow DAG successfully orchestrates all 5 layers  
✅ Pipeline runs idempotently without data duplication  
✅ Docker Compose can bring up the full stack from scratch  
✅ E2E tests confirm data flows from World Bank APIs to Chatbot responses  
✅ Project documentation complete  

---

**End of Phase 5. The IDP MVP is now complete and operational.**