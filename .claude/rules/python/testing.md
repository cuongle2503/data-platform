---
paths:
  - "**/*.py"
  - "**/*.pyi"
---
# Python Testing

> Extends [common/testing.md](../common/testing.md) with Python-specific content.

## Framework

Use **pytest** as the testing framework.

## Coverage

```bash
uv run pytest --cov=lib --cov=pipelines --cov-report=term-missing
```

## Test Organization

Use `pytest.mark` for test categorization:

```python
import pytest

@pytest.mark.unit
def test_calculate_total():
    ...

@pytest.mark.integration
def test_database_connection():
    ...

@pytest.mark.slow
def test_full_pipeline_run():
    ...
```

Run subsets:

```bash
uv run pytest -m "unit"
uv run pytest -m "not slow"
```

## Fixtures

```python
@pytest.fixture
def sample_data() -> list[dict]:
    return [
        {"id": 1, "name": "Alice", "score": 95},
        {"id": 2, "name": "Bob", "score": 87},
    ]

def test_top_scorers(sample_data):
    result = top_scorers(sample_data, threshold=90)
    assert len(result) == 1
```

## Database Testing

- Use test database or transaction rollback
- Factory fixtures for test records
- Never test against production data
