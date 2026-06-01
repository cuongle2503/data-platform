# Layer 3 — Storage & Serving (Gold + Embeddings)

## Objectives

Layer 3 provides durable storage for cleaned data and fast serving for downstream consumers:

- Gold dimensional model in PostgreSQL 16 (schema `gold`)
- Embeddings for indicators and document chunks in schema `embeddings` with pgvector

## Gold Dimension Tables

### `gold.dim_countries`

| Column       | Type       | PK | Description                                  |
|--------------|------------|----|----------------------------------------------|
| `country_key`  | SERIAL   | ✓  | Surrogate key                                |
| `country_code` | VARCHAR(3) |  | ISO 3-letter code (natural key)              |
| `country_name` | VARCHAR   |   | Full country name                            |
| `region`       | VARCHAR   |   | World Bank region                            |
| `income_group` | VARCHAR   |   | Low / Lower-middle / Upper-middle / High     |
| `is_asean`     | BOOLEAN   |   | ASEAN member flag                            |
| `is_primary`   | BOOLEAN   |   | Primary focus country (Vietnam)              |

**Natural key**: `country_code`

**Indexes**:
- Primary key on `country_key`
- Unique index on `country_code`

### `gold.dim_indicators`

| Column          | Type    | PK | Description                                    |
|-----------------|---------|----|------------------------------------------------|
| `indicator_key` | SERIAL  | ✓  | Surrogate key                                  |
| `indicator_code`| VARCHAR |    | Original source code                           |
| `indicator_name`| VARCHAR |    | Human-readable name                            |
| `source_system` | VARCHAR |    | `world_bank` (initially), later `nso_vietnam`, `fred` |
| `category`      | VARCHAR |    | gdp, prices, trade, rates, labor, investment, structure, technology |
| `unit`          | VARCHAR |    | %, USD, Index, etc.                            |
| `frequency`     | VARCHAR |    | annual, sparse, etc.                           |
| `description`   | TEXT    |    | Detailed description                           |

**Natural key**: `(indicator_code, source_system)`

**Indexes**:
- Primary key on `indicator_key`
- Unique index on `(indicator_code, source_system)`
- Index on `category` for filtering

### `gold.dim_dates`

| Column             | Type    | PK | Description                     |
|--------------------|---------|----|---------------------------------|
| `date_key`         | INTEGER | ✓  | YYYYMMDD                        |
| `full_date`        | DATE    |    | Actual date                     |
| `year`             | INTEGER |    | Year                            |
| `quarter`          | INTEGER |    | Quarter (1–4)                   |
| `month`            | INTEGER |    | Month (1–12)                    |
| `month_name`       | VARCHAR |    | Month name                      |
| `day_of_week`      | INTEGER |    | 1=Monday, 7=Sunday              |
| `is_weekend`       | BOOLEAN |    | Weekend indicator               |
| `is_vietnam_holiday` | BOOLEAN |  | Vietnamese public holidays      |
| `fiscal_year_vn`   | INTEGER |    | Vietnam fiscal year             |

**Natural key**: `date_key`

**Indexes**:
- Primary key on `date_key`
- Index on `year` for time-series queries

## Gold Fact Table: `gold.fact_economic_indicators`

The central fact table:

| Column        | Type             | FK →           | Description                                  |
|---------------|------------------|----------------|----------------------------------------------|
| `indicator_key` | INTEGER        | dim_indicators | Indicator reference                          |
| `country_key`   | INTEGER        | dim_countries  | Country reference                            |
| `date_key`      | INTEGER        | dim_dates      | Date reference                               |
| `period_start`  | DATE           |                | Period start date                            |
| `period_end`    | DATE           |                | Period end date                              |
| `value`         | DOUBLE PRECISION |              | Indicator value                              |
| `source_system` | VARCHAR        |                | world_bank (initially)                       |
| `loaded_at`     | TIMESTAMP      |                | Load timestamp                               |

**Grain**: one row per indicator × country × period × source_system

With only World Bank, `source_system='world_bank'` for all rows.

**Indexes**:
- Composite index on `(indicator_key, country_key, date_key, source_system)` (unique)
- Index on `country_key` for country-level queries
- Index on `indicator_key` for indicator-level queries
- Index on `date_key` for time-series queries

## Embeddings Schema

Schema `embeddings` (conceptual design):

### `embeddings.economic_embeddings`

| Column     | Type      | Description                                    |
|------------|-----------|------------------------------------------------|
| `id`       | SERIAL    | Primary key                                    |
| `ref_type` | VARCHAR   | `economic_indicator` or `world_bank_report`    |
| `ref_id`   | VARCHAR   | Identifier of a fact row or document chunk     |
| `embedding`| VECTOR(768) | pgvector array (Gemini text-embedding-004)   |
| `metadata` | JSONB     | Contextual information                         |
| `created_at` | TIMESTAMP | Creation timestamp                          |

**Indexes**:
- Primary key on `id`
- Index on `ref_type` for filtering
- HNSW index on `embedding` for vector similarity search:
  ```sql
  CREATE INDEX ON embeddings.economic_embeddings 
  USING hnsw (embedding vector_cosine_ops);
  ```

This allows semantic search over numeric series and document text in the Intelligence layer.

## PostgreSQL Configuration

For optimal performance on the 16GB RAM server:

```ini
# postgresql.conf
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 64MB
max_connections = 100

# Enable pgvector
shared_preload_libraries = 'vector'
```

## Backup Strategy

- Daily full backup of PostgreSQL using `pg_dump`
- Continuous WAL archiving for point-in-time recovery
- Weekly backup of MinIO Bronze bucket
- Backup retention: 30 days
