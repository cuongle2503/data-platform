# Layer 2 — Transformation (Silver & Gold)

## Objectives

Layer 2 cleans, standardizes, and models the raw data:

- **Silver**: staging tables that are typed, deduplicated, and sanitized
- **Gold**: business-ready dimensional tables (dims and facts) suited for APIs, BI, and AI

## DuckDB + dbt-core

DuckDB provides an in-process analytical engine that reads Parquet directly and executes SQL transformations efficiently on the single server. dbt-core + dbt-duckdb manage model definitions, tests, and documentation:

- `stg_*` models for Silver (staging)
- `dim_*` and `fact_*` models for Gold (marts)

## Silver Model: `stg_world_bank__indicators`

The main Silver table is `stg_world_bank__indicators`, which reads from Bronze and applies the following transformations:

| Column         | Type        | Transformation             | Description              |
|----------------|-------------|---------------------------|--------------------------|
| `country_code` | VARCHAR(3)  | `UPPER(TRIM(country_code))` | ISO 3-letter code    |
| `country_name` | VARCHAR     | `TRIM(country_name)`      | Country name             |
| `indicator_code` | VARCHAR   | `TRIM(indicator_code)`    | Indicator ID             |
| `indicator_name` | VARCHAR   | `TRIM(indicator_name)`    | Indicator name           |
| `year`         | INTEGER     | `CAST(year AS INTEGER)`   | Observation year         |
| `value`        | DOUBLE      | `CAST(value AS DOUBLE)` + filter NULL | Indicator value |
| `ingested_at`  | TIMESTAMP   | rename from `_ingested_at`| Ingestion timestamp      |

### Additional Rules

- Deduplicate on `(country_code, indicator_code, year)`
- Implement `not_null` tests on keys and `unique` tests on the composite key

This model is materialized as a DuckDB view, keeping the staging layer lightweight.

## From Silver to Gold

Gold models are defined in dbt and built in DuckDB, then exported to PostgreSQL:

- `gold.dim_countries`: country dimension (seed file + World Bank metadata)
- `gold.dim_indicators`: indicator dimension (seed file for 32 World Bank indicators)
- `gold.dim_dates`: generated date dimension from 1950–2030
- `gold.fact_economic_indicators`: unified fact table joining staging and dimensions

## Data Quality Tests

Data quality is enforced via dbt tests:

- `not_null` on dimension natural keys and fact foreign keys
- `unique` on dimension natural keys and fact grain
- Custom tests for value ranges and dates not in the future

### Example dbt Test Configuration

```yaml
# models/gold/schema.yml
version: 2

models:
  - name: fact_economic_indicators
    description: "Unified fact table for economic indicators"
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - indicator_key
            - country_key
            - date_key
            - source_system
    columns:
      - name: indicator_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_indicators')
              field: indicator_key
      - name: country_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_countries')
              field: country_key
      - name: date_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_dates')
              field: date_key
      - name: value
        tests:
          - not_null
```

## dbt Project Structure

```
dbt/
├── models/
│   ├── staging/
│   │   └── world_bank/
│   │       ├── stg_world_bank__indicators.sql
│   │       └── stg_world_bank__docs.sql
│   └── gold/
│       ├── dim_countries.sql
│       ├── dim_indicators.sql
│       ├── dim_dates.sql
│       └── fact_economic_indicators.sql
├── seeds/
│   ├── seed_countries.csv
│   └── seed_indicators.csv
├── tests/
│   └── custom_tests.sql
└── dbt_project.yml
```

## Export to PostgreSQL

After dbt builds Gold models in DuckDB, a separate export step loads them into PostgreSQL:

```python
# Export Gold tables from DuckDB to PostgreSQL
import duckdb
import psycopg

duck_conn = duckdb.connect("data/gold.duckdb")
pg_conn = psycopg.connect(os.environ["DATABASE_URL"])

for table in ["dim_countries", "dim_indicators", "dim_dates", "fact_economic_indicators"]:
    df = duck_conn.execute(f"SELECT * FROM gold.{table}").df()
    # Truncate and load
    with pg_conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE gold.{table} CASCADE")
    df.to_sql(table, pg_conn, schema="gold", if_exists="append", index=False)
```

This keeps transformation logic in dbt while serving data from PostgreSQL for API performance.
