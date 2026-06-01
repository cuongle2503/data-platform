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
