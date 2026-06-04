# Tech Stack: Lean vs Deferred Technologies

For the World Bank-first deployment, the architecture prioritizes a lean, single-node setup over distributed systems to minimize operational complexity. The recommended core stack outlines the components to implement immediately, while deferred technologies indicate areas for future scaling.

## Core (Implement Now)

These components form the foundation of the Intelligent Data Platform (IDP) and can comfortably run on the target hardware (16GB RAM, 512GB SSD):

- **MinIO**: S3-compatible object storage for the Bronze layer (raw Parquet and PDFs).
- **DuckDB**: Fast, in-process analytical engine for transforming data from Bronze to Gold.
- **dbt-core & dbt-duckdb**: Transformation logic, testing, and modeling.
- **PostgreSQL 16**: Relational database for Gold dimensional models and serving.
- **pgvector**: PostgreSQL extension for vector embeddings storage and semantic search.
- **FastAPI**: High-performance Python framework for building REST and WebSocket APIs.
- **Gemini**: LLM for text embeddings (`text-embedding-004`) and RAG generation (`2.0 Flash`, `2.5 Pro`).
- **Airflow 2.10.3**: Orchestration for ingestion and transformation DAGs.
- **Docker Compose**: Containerization and deployment management for the single-node setup.

## Deferred (Scale Later)

These technologies add complexity and overhead. They should only be introduced when there is a demonstrated need (e.g., scale limits, specific analytical requirements, or transition to cloud):

- **Elasticsearch**: Powerful full-text search engine (deferred in favor of PostgreSQL `tsvector`).
- **Redis + Celery**: Asynchronous task queues (deferred since Airflow handles orchestration).
- **Spark / Dataproc**: Distributed data processing (deferred in favor of DuckDB's vertical scaling).
- **Pub/Sub or Kafka**: Streaming event buses (deferred since current ingestion is batch-oriented).
- **BigQuery / Dataflow**: Managed GCP data warehouse and processing (deferred to keep system on-prem first).
- **Looker Studio / Superset**: BI dashboards (deferred; focus initially on API access).
- **LangGraph / LlamaIndex**: Advanced LLM orchestration and multi-agent workflows (deferred in favor of a lean Python RAG pipeline).
- **MLflow / Evidently AI / SHAP**: MLOps and model explainability (deferred until custom model training is introduced).
- **Neo4j**: Graph database for data lineage and complex relationships (optional, can be added later).

## Extending to New Sources

This architecture is designed to be the single source of truth. Future data sources—such as NSO Vietnam or FRED—can extend the same patterns without changing the core design:
- Add new connectors in Layer 1 (Bronze).
- Create new staging models in Layer 2 (Silver).
- Merge into the same Gold dimensional and fact tables using the `source_system` column to differentiate records.