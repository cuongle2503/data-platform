---
paths:
  - "**/*.py"
  - "**/dags/**"
  - "**/pipelines/**"
  - "**/dbt/**/*.sql"
  - "**/dbt/**/*.yml"
---
# Data Pipeline Rules (dbt + Airflow)

Specialized rules for data pipeline projects using dbt and Apache Airflow.

## dbt Conventions

### Model Organization

```
dbt/
├── models/
│   ├── staging/        # stg_* — thin views on raw sources
│   ├── intermediate/   # int_* — reusable transformations
│   └── marts/          # fct_*, dim_* — final dimensional models
├── macros/             # reusable Jinja macros
├── tests/              # singular tests
└── sources.yml         # source declarations
```

### Model Best Practices

- Use `ref()` and `source()` — never hardcode table names
- Every model has a `unique_key` test and `not_null` test on primary keys
- Sources déclared with `freshness` checks
- Materialization: `table` for marts, `view` for staging, `ephemeral` for reusable snippets
- Add `description:` on every column in schema.yml

### SQL Style (dbt)

```sql
-- Use CTEs, not subqueries
WITH base AS (
    SELECT * FROM {{ ref('stg_orders') }}
),
filtered AS (
    SELECT * FROM base WHERE status != 'cancelled'
)
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(amount) AS total_amount
FROM filtered
GROUP BY 1
```

## Airflow Conventions

### DAG Structure

```python
from datetime import datetime
from airflow.decorators import dag, task

@dag(
    dag_id="etl_daily_sales",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["etl", "sales"],
    doc_md=__doc__,
)
def etl_daily_sales():
    @task
    def extract() -> list[dict]:
        ...

    @task
    def transform(data: list[dict]) -> list[dict]:
        ...

    @task
    def load(transformed: list[dict]) -> int:
        ...

    extract() >> transform() >> load()

etl_daily_sales()
```

### Airflow Best Practices

- Use TaskFlow API (`@task` decorator) — not classic operators unless necessary
- `catchup=False` on every DAG unless backfill is intentional
- Idempotent tasks: re-running same DAG run produces same results
- No top-level code in DAG files (slows down scheduler)
- Connections stored as Airflow connections / secrets backend — never in source
- `max_active_runs` and `retries` set explicitly on every DAG

### Airflow Testing

```python
# DAG integrity test
def test_dag_parsing():
    """All DAGs must parse without error."""
    from airflow.models import DagBag
    dag_bag = DagBag()
    assert len(dag_bag.import_errors) == 0

# Task unit test
def test_transform_task():
    result = transform.function([{"id": 1}])
    assert len(result) > 0
```

## PostgreSQL / Database

- Use **SQLAlchemy 2.0** style (`select()` with `where()`)
- Parameterized queries — never f-strings
- Connection pooling via `create_engine(pool_size=...)`
- Migration management: dbt snapshots hoặc Alembic

## Idempotency (CRITICAL)

Every pipeline MUST produce the same result when re-run:

```sql
-- CORRECT: idempotent UPSERT
INSERT INTO fact_sales (id, amount, updated_at)
VALUES (%(id)s, %(amount)s, NOW())
ON CONFLICT (id) DO UPDATE SET
    amount = EXCLUDED.amount,
    updated_at = NOW();

-- WRONG: non-idempotent (creates duplicates)
INSERT INTO fact_sales (id, amount) VALUES (%(id)s, %(amount)s);
```

## Prohibited Patterns

- `SELECT *` in production pipelines — list columns explicitly
- `os.system()` or `subprocess` with shell=True for pipeline execution
- Storing raw credentials in Airflow variables
- Long-running tasks (>1h) without checkpoints
- Silent data loss (truncate + insert without backup/validation)
