---
name: data-pipeline
description: Data pipeline patterns for dbt, Apache Airflow, and PostgreSQL — idempotency, DAG design, dbt modeling, and data quality best practices.
---

# Data Pipeline Patterns

Best practices for building reliable, idempotent data pipelines with dbt, Airflow, and PostgreSQL.

## When to Activate

- Designing new data pipelines or DAGs
- Writing or refactoring dbt models
- Setting up Airflow orchestration
- Debugging pipeline failures or data quality issues
- Reviewing data pipeline code

## dbt Modeling

### Layer Convention

```
dbt/models/
├── staging/        # stg_* — thin views on raw sources, minimal transformation
├── intermediate/   # int_* — reusable building blocks
└── marts/          # fct_*, dim_* — final dimensional models for consumption
```

### Model Rules

```sql
-- Use ref() and source() — never hardcode table names
SELECT *
FROM {{ ref('stg_orders') }}
WHERE status != 'cancelled'

-- Use CTEs, not subqueries
WITH base AS (
    SELECT * FROM {{ ref('stg_orders') }}
),
aggregated AS (
    SELECT customer_id, COUNT(*) AS order_count
    FROM base
    GROUP BY 1
)
SELECT * FROM aggregated
```

### Source Freshness

```yaml
# sources.yml
sources:
  - name: raw
    schema: raw_data
    tables:
      - name: orders
        freshness:
          warn_after: {count: 6, period: hour}
          error_after: {count: 24, period: hour}
        loaded_at_field: _etl_loaded_at
```

### Testing

```yaml
# Every model must have these tests
models:
  - name: fct_orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_id
      - name: amount
        tests:
          - dbt_utils.accepted_range:
              min_value: 0
```

### Materialization Strategy

| Materialization | When |
|----------------|------|
| `view` | Staging models, simple transformations |
| `table` | Marts, models queried frequently |
| `incremental` | Large fact tables, append-only data |
| `ephemeral` | Reusable CTE snippets |

## Airflow DAG Design

### DAG Structure (TaskFlow API)

```python
from datetime import datetime
from airflow.decorators import dag, task

@dag(
    dag_id="etl_daily_sales",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["etl", "sales"],
    doc_md=__doc__,
)
def etl_daily_sales():
    @task(retries=3, retry_delay=timedelta(minutes=5))
    def extract() -> list[dict]:
        """Extract from source database."""
        ...

    @task
    def transform(raw: list[dict]) -> list[dict]:
        """Transform and validate."""
        ...

    @task
    def load(transformed: list[dict]) -> int:
        """Load to warehouse, return row count."""
        ...

    @task
    def run_dbt(loaded_count: int):
        """Trigger dbt after load."""
        ...

    extract() >> transform() >> load() >> run_dbt()

etl_daily_sales()
```

### Airflow Best Practices

- `catchup=False` unless backfill is intentional
- **Idempotent tasks**: same DAG run = same result
- No top-level code in DAG files (slows scheduler parsing)
- Connections via Airflow secrets backend — never in source code
- `max_active_runs` and `retries` explicit on every DAG
- Task timeout: `execution_timeout=timedelta(hours=1)`

### Airflow Testing

```python
# DAG integrity test
def test_all_dags_parse():
    from airflow.models import DagBag
    dag_bag = DagBag()
    assert len(dag_bag.import_errors) == 0, str(dag_bag.import_errors)

# Task unit test
def test_transform_task():
    result = transform.function([{"id": 1, "amount": 100}])
    assert len(result) > 0
```

## Idempotency (CRITICAL)

Every pipeline MUST produce the same result when re-run:

```sql
-- CORRECT: Idempotent UPSERT
INSERT INTO fact_sales (id, amount, updated_at)
VALUES (%(id)s, %(amount)s, NOW())
ON CONFLICT (id) DO UPDATE SET
    amount = EXCLUDED.amount,
    updated_at = NOW();

-- WRONG: Creates duplicates
INSERT INTO fact_sales (id, amount) VALUES (%(id)s, %(amount)s);
```

## Data Quality Checks

```python
# Custom dbt test (in tests/generic/)
{% test positive_values(model, column_name) %}
SELECT *
FROM {{ model }}
WHERE {{ column_name }} < 0
{% endtest %}

# Row count validation in Airflow
@task
def validate_row_count(table: str, min_rows: int = 1):
    count = db.query(f"SELECT COUNT(*) FROM {table}")
    if count < min_rows:
        raise ValueError(f"{table} has only {count} rows (min: {min_rows})")
```

## Prohibited Patterns

| Pattern | Why It's Bad | Alternative |
|---------|-------------|-------------|
| `SELECT *` in production | Schema changes break pipelines | List columns explicitly |
| Hardcoded table names in dbt | Breaks lineage | Use `ref()` and `source()` |
| `os.system()` for pipeline execution | No error handling, no retries | Use Airflow operators |
| Credentials in Airflow variables | Security risk | Airflow secrets backend |
| Tasks >1h without checkpoints | Hard to resume on failure | Split into smaller tasks |
| `TRUNCATE + INSERT` without backup | Silent data loss | UPSERT or staged swap |
| No freshness checks on sources | Stale data goes undetected | dbt source freshness |
