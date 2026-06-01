# IDP Documentation

**Intelligent Data Platform** — Economic data platform with 5-layer Medallion architecture.

---

## Documentation Structure

### 📐 Architecture (`architecture/`)
System design, layer specifications, and technical decisions.

- [00-overview.md](architecture/00-overview.md) — Executive summary and design principles
- [01-layer-ingestion.md](architecture/01-layer-ingestion.md) — Layer 1: World Bank API → MinIO Bronze
- [02-layer-transformation.md](architecture/02-layer-transformation.md) — Layer 2: DuckDB + dbt (Silver/Gold)
- [03-layer-storage.md](architecture/03-layer-storage.md) — Layer 3: PostgreSQL + pgvector
- [04-layer-intelligence.md](architecture/04-layer-intelligence.md) — Layer 4: FastAPI + Gemini RAG
- [05-layer-orchestration.md](architecture/05-layer-orchestration.md) — Layer 5: Airflow orchestration
- [06-api-spec.md](architecture/06-api-spec.md) — REST & WebSocket API specification
- [07-tech-stack.md](architecture/07-tech-stack.md) — Core vs deferred technologies
- [08-project-structure.md](architecture/08-project-structure.md) — Project structure and code organization

### 🚀 Implementation Phases (`phases/`)
Step-by-step implementation plans with detailed task lists.

- [PHASE-README.md](phases/PHASE-README.md) — **START HERE** — Master index and progress tracker
- [PHASE-0-SETUP.md](phases/PHASE-0-SETUP.md) — Infrastructure and tooling setup
- [PHASE-1-INGESTION.md](phases/PHASE-1-INGESTION.md) — World Bank data ingestion
- [PHASE-2-TRANSFORMATION.md](phases/PHASE-2-TRANSFORMATION.md) — dbt transformation pipeline
- [PHASE-3-STORAGE.md](phases/PHASE-3-STORAGE.md) — PostgreSQL optimization & embeddings
- [PHASE-4-INTELLIGENCE.md](phases/PHASE-4-INTELLIGENCE.md) — FastAPI & RAG chatbot
- [PHASE-5-ORCHESTRATION.md](phases/PHASE-5-ORCHESTRATION.md) — Airflow DAG automation

---

## Quick Start

**New to the project?**
1. Read [architecture/00-overview.md](architecture/00-overview.md) for system overview
2. Follow [phases/PHASE-README.md](phases/PHASE-README.md) for implementation

**Ready to build?**
→ Start with [phases/PHASE-0-SETUP.md](phases/PHASE-0-SETUP.md)

---

## Architecture at a Glance

```
World Bank APIs
      ↓
[Layer 1] Ingestion → MinIO (Bronze Parquet)
      ↓
[Layer 2] DuckDB + dbt → Silver/Gold models
      ↓
[Layer 3] PostgreSQL + pgvector → Serving layer
      ↓
[Layer 4] FastAPI + Gemini → RAG chatbot
      ↓
[Layer 5] Airflow → Orchestration
```

**Tech Stack**: Python 3.11+, MinIO, DuckDB, dbt, PostgreSQL 16, pgvector, FastAPI, Gemini, Airflow 3.0

---

**Last Updated**: 2026-06-01
