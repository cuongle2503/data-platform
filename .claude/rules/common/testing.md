# Testing Requirements

## Minimum Test Coverage: 80%

Test Types (ALL required):
1. **Unit Tests** — Individual functions, utilities, data transformers
2. **Integration Tests** — Database operations, API endpoints, dbt models
3. **Pipeline Tests** — DAG integrity, end-to-end data flows

## Test-Driven Development

MANDATORY workflow:
1. Write test first (RED)
2. Run test — it should FAIL
3. Write minimal implementation (GREEN)
4. Run test — it should PASS
5. Refactor (IMPROVE)
6. Verify coverage (80%+)

## Test Structure (AAA Pattern)

Arrange-Act-Assert:

```python
def test_calculate_total_with_discount():
    # Arrange
    items = [{"price": 100, "qty": 2}, {"price": 50, "qty": 1}]

    # Act
    result = calculate_total(items, discount=0.1)

    # Assert
    assert result == 225.0
```

### Test Naming

Use descriptive names that explain behavior:

```python
def test_returns_empty_list_when_no_records_match_filter():
    ...

def test_raises_value_error_when_connection_string_is_invalid():
    ...

def test_falls_back_to_cache_when_database_is_unavailable():
    ...
```

## Fixtures & Factories

- Use `conftest.py` for shared fixtures
- Use factory functions for test data (not hardcoded dicts)
- Clean up test data in `teardown` or use transactions for rollback
