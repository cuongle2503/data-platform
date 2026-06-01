# IDP Overview

## Executive Summary

The Intelligent Data Platform (IDP) is a lean, on-premise-first data and AI platform for economic data, designed to run on a single 16GB RAM, 512GB SSD server and expand later to Google Cloud as needed. The architecture follows a Medallion pattern (Bronze/Silver/Gold) and a five-layer model—Ingestion, Transformation, Storage & Serving, Intelligence (RAG), and Orchestration & Ops—implemented with open-source components: MinIO, DuckDB, dbt-core, PostgreSQL, pgvector, Airflow, FastAPI, and optional Neo4j.

This documentation covers:

- Conceptual architecture and design principles
- Detailed description of each of the 5 layers
- World Bank-focused data model (1 Silver + 3 dims + 1 fact + embeddings schema)
- API design, including full request/response shapes for key endpoints that sit on top of Gold and embeddings
- Implementation blueprint for the World Bank pipeline and a clear lean vs. deferred technology split

## Design Principles

High-level design is guided by four principles:

- **Basic first, modern later**: Build a minimal end-to-end path from source to user before adding complexity.
- **Lean stack**: Add as few services as possible; each new component must demonstrably reduce manual work or unlock a concrete capability.
- **Open-source first**: Use MinIO, DuckDB, dbt-core, PostgreSQL, pgvector, Neo4j, Airflow, FastAPI, etc., and rely on managed cloud services only when justified.
- **Single-node first**: Maximize the existing 16GB/512GB on-prem server before scaling out or adopting distributed engines.

## High-Level Architecture

External sources (World Bank Open Data and World Bank Documents) feed an on-premise stack that stores raw data in MinIO (Bronze), transforms it with DuckDB + dbt (Silver/Gold), materializes a dimensional model in PostgreSQL (Gold), and serves it through APIs and a RAG-enabled chatbot.

### The 5 Logical Layers

1. **Layer 1 — Ingestion & Raw Storage**: Python connectors pull data from World Bank APIs, store raw Parquet files in MinIO.
2. **Layer 2 — Transformation (Silver & Gold)**: DuckDB + dbt convert Bronze into cleaned Silver staging and Gold marts.
3. **Layer 3 — Storage & Serving (Gold + Embeddings)**: PostgreSQL holds Gold dims/facts and an embeddings schema built on pgvector.
4. **Layer 4 — Intelligence (RAG & Chatbot)**: FastAPI + PostgreSQL + pgvector + Gemini provide search and LLM-powered Q&A.
5. **Layer 5 — Orchestration & Ops**: Airflow 3.0 orchestrates all jobs; Docker Compose, Nginx, and optional monitoring support operations.

## Documentation Structure

- [00-overview.md](00-overview.md) — This file
- [01-layer-ingestion.md](01-layer-ingestion.md) — Layer 1: Ingestion & Raw Storage
- [02-layer-transformation.md](02-layer-transformation.md) — Layer 2: Transformation (Silver & Gold)
- [03-layer-storage.md](03-layer-storage.md) — Layer 3: Storage & Serving
- [04-layer-intelligence.md](04-layer-intelligence.md) — Layer 4: Intelligence (RAG & Chatbot)
- [05-layer-orchestration.md](05-layer-orchestration.md) — Layer 5: Orchestration & Ops
- [06-data-model.md](06-data-model.md) — World Bank Data Model
- [07-api-spec.md](07-api-spec.md) — API Specification
- [08-tech-stack.md](08-tech-stack.md) — Technology Stack & Decisions

## Quick Start

See [05-layer-orchestration.md](05-layer-orchestration.md) for deployment instructions and the World Bank DAG workflow.
