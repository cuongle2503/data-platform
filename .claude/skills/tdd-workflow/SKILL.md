---
name: tdd-workflow
description: Use this skill when writing new features, fixing bugs, or refactoring code. Enforces test-driven development with 80%+ coverage including unit, integration, and pipeline tests.
origin: ECC (adapted for Python)
---

# Test-Driven Development Workflow

This skill ensures all code development follows TDD principles with comprehensive test coverage.

## When to Activate

- Writing new features or functionality
- Fixing bugs or issues
- Refactoring existing code
- Adding API endpoints or pipeline tasks

## Core Principles

### 1. Tests BEFORE Code
ALWAYS write tests first, then implement code to make tests pass.

### 2. Coverage Requirements
- Minimum 80% coverage (unit + integration + pipeline tests)
- All edge cases covered
- Error scenarios tested
- Boundary conditions verified

### 3. Test Types

| Type | Scope | Tool |
|------|-------|------|
| Unit Tests | Individual functions, utilities, data transformers | pytest |
| Integration Tests | API endpoints, database operations, dbt models | pytest + dbt test |
| Pipeline Tests | DAG integrity, end-to-end data flows | Airflow DAG test |

## TDD Workflow Steps

### Step 1: Write User Journey
```
As a [role], I want [action], so that [benefit]

Example:
As a data analyst, I want the daily sales pipeline to aggregate order totals,
so that I can report on daily revenue trends.
```

### Step 2: Write Test First (RED)

```python
# tests/unit/test_sales_transformer.py
def test_aggregate_daily_sales_with_multiple_orders():
    # Arrange
    orders = [
        {"customer_id": 1, "amount": 100.0, "date": "2024-01-15"},
        {"customer_id": 1, "amount": 50.0, "date": "2024-01-15"},
        {"customer_id": 2, "amount": 200.0, "date": "2024-01-15"},
    ]

    # Act
    result = aggregate_daily_sales(orders)

    # Assert
    assert len(result) == 2  # 2 customers
    assert result[0]["total_amount"] == 150.0

def test_aggregate_daily_sales_empty_input():
    assert aggregate_daily_sales([]) == []

def test_aggregate_daily_sales_handles_null_amounts():
    orders = [{"customer_id": 1, "amount": None, "date": "2024-01-15"}]
    with pytest.raises(ValueError, match="null amount"):
        aggregate_daily_sales(orders)
```

Run: `uv run pytest tests/unit/test_sales_transformer.py`
→ **Must FAIL** (RED gate)

### Step 3: Git Checkpoint (RED)
```bash
git add -A && git commit -m "test: add reproducer for daily sales aggregation"
```

### Step 4: Implement Code (GREEN)

```python
# pipelines/transformers/sales.py
def aggregate_daily_sales(orders: list[dict]) -> list[dict]:
    """Aggregate orders by customer for daily sales reporting."""
    if not orders:
        return []

    grouped: dict[int, float] = {}
    for order in orders:
        if order["amount"] is None:
            raise ValueError(f"null amount in order: {order}")
        cid = order["customer_id"]
        grouped[cid] = grouped.get(cid, 0.0) + order["amount"]

    return [
        {"customer_id": cid, "total_amount": total}
        for cid, total in grouped.items()
    ]
```

Run: `uv run pytest tests/unit/test_sales_transformer.py`
→ **Must PASS** (GREEN gate)

### Step 5: Git Checkpoint (GREEN)
```bash
git add -A && git commit -m "fix: implement daily sales aggregation"
```

### Step 6: Refactor
Improve while keeping tests GREEN:
- Extract helper functions
- Add type annotations
- Improve naming

### Step 7: Verify Coverage
```bash
uv run pytest --cov=pipelines --cov=lib --cov-report=term-missing
# Target: 80%+
```

## Testing Patterns (Python)

### Mock External Dependencies

```python
from unittest.mock import patch, Mock

@patch("pipelines.extract.fetch_from_api")
def test_extract_with_mock_api(mock_fetch):
    mock_fetch.return_value = [{"id": 1, "name": "Test"}]
    result = extract_data("2024-01-01")
    assert len(result) == 1
    mock_fetch.assert_called_once_with("2024-01-01")
```

### Database Integration Test

```python
@pytest.mark.integration
def test_insert_and_query(db_session):
    db_session.execute(
        "INSERT INTO sales (id, amount) VALUES (1, 100)"
    )
    result = db_session.execute("SELECT SUM(amount) FROM sales").scalar()
    assert result == 100
```

### Airflow DAG Test

```python
def test_dag_parsing():
    from airflow.models import DagBag
    dag_bag = DagBag()
    assert len(dag_bag.import_errors) == 0, str(dag_bag.import_errors)

def test_dag_structure():
    from airflow.models import DagBag
    dag = DagBag().get_dag("etl_daily_sales")
    tasks = dag.tasks
    task_ids = [t.task_id for t in tasks]
    assert "extract" in task_ids
    assert "transform" in task_ids
    assert "load" in task_ids
```

## Common Testing Mistakes

| Wrong | Right |
|-------|-------|
| Testing implementation details | Test behavior / output |
| Brittle mocks tied to internals | Mock at boundaries (API, DB) |
| Tests depend on each other | Independent + fixture setup |
| Skipping edge cases | Test: empty, None, large, negative |
| Only testing happy path | Test error paths explicitly |

## Best Practices

1. **Write Tests First** — Always TDD
2. **One concept per test** — Focus on single behavior
3. **Descriptive names** — `test_raises_value_error_when_source_is_empty`
4. **AAA structure** — Arrange, Act, Assert
5. **Mock at boundaries** — Isolate unit tests from external services
6. **Test edge cases** — None, empty, zero, negative, massive
7. **Test error paths** — Not just happy paths
8. **Keep tests fast** — Unit tests < 10ms, integration < 1s
9. **Clean up** — Use fixtures with teardown or transaction rollback
10. **Review coverage gaps** — Focus on untested branches

**Remember**: Tests are not optional. They are the safety net that enables confident refactoring, rapid development, and production reliability.
