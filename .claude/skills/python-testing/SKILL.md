---
name: python-testing
description: Python testing strategies using pytest, TDD methodology, fixtures, mocking, parametrization, and coverage requirements.
origin: ECC
---

# Python Testing Patterns

Comprehensive testing strategies for Python applications using pytest, TDD methodology, and best practices.

## When to Activate

- Writing new Python code (follow TDD: red, green, refactor)
- Designing test suites for Python projects
- Reviewing Python test coverage
- Setting up testing infrastructure

## Core Testing Philosophy

### Test-Driven Development (TDD)

Always follow the TDD cycle:

1. **RED**: Write a failing test for the desired behavior
2. **GREEN**: Write minimal code to make the test pass
3. **REFACTOR**: Improve code while keeping tests green

### Coverage Requirements

- **Target**: 80%+ code coverage
- **Critical paths**: 100% coverage required

```bash
pytest --cov=mypackage --cov-report=term-missing --cov-report=html
```

## Test Structure (AAA Pattern)

```python
def test_calculate_total_with_discount():
    # Arrange
    items = [{"price": 100, "qty": 2}, {"price": 50, "qty": 1}]

    # Act
    result = calculate_total(items, discount=0.1)

    # Assert
    assert result == 225.0
```

## Fixtures

### Basic Fixture

```python
@pytest.fixture
def sample_data():
    return {"name": "Alice", "age": 30}

def test_sample_data(sample_data):
    assert sample_data["name"] == "Alice"
```

### Fixture with Setup/Teardown

```python
@pytest.fixture
def database():
    db = Database(":memory:")
    db.create_tables()
    yield db
    db.close()

def test_database_query(database):
    result = database.query("SELECT * FROM users")
    assert len(result) > 0
```

### Fixture Scopes

- `function` (default) — runs for each test
- `module` — runs once per module
- `session` — runs once per test session

### Conftest.py for Shared Fixtures

```python
# tests/conftest.py
import pytest

@pytest.fixture
def client():
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client
```

## Parametrization

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("PyThOn", "PYTHON"),
])
def test_uppercase(input, expected):
    assert input.upper() == expected
```

## Markers

```python
@pytest.mark.slow
def test_slow_operation(): ...

@pytest.mark.integration
def test_api_integration(): ...

@pytest.mark.unit
def test_unit_logic(): ...
```

Run subsets:
```bash
pytest -m "not slow"
pytest -m integration
pytest -m "unit and not slow"
```

## Mocking

```python
from unittest.mock import patch, Mock

@patch("mypackage.external_api_call")
def test_with_mock(api_call_mock):
    api_call_mock.return_value = {"status": "success"}
    result = my_function()
    api_call_mock.assert_called_once()
    assert result["status"] == "success"

# Mock exception
api_call_mock.side_effect = ConnectionError("Network error")
```

## Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_add(2, 3)
    assert result == 5
```

## Testing Exceptions

```python
def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_custom_exception():
    with pytest.raises(ValueError, match="invalid input"):
        validate_input("invalid")
```

## Testing with Temp Files

```python
def test_with_tmp_path(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")
    result = process_file(str(test_file))
    assert result == "hello world"
```

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_models.py
│   ├── test_utils.py
│   └── test_services.py
├── integration/             # Integration tests
│   ├── test_api.py
│   └── test_database.py
└── e2e/                     # End-to-end tests
    └── test_user_flow.py
```

## Best Practices

**DO:**
- Follow TDD: Write tests before code
- Test one thing: Each test should verify a single behavior
- Use descriptive names: `test_user_login_with_invalid_credentials_fails`
- Use fixtures to eliminate duplication
- Mock external dependencies
- Test edge cases: empty inputs, None values, boundary conditions

**DON'T:**
- Don't test implementation — test behavior, not internals
- Don't use complex conditionals in tests
- Don't share state between tests
- Don't test third-party code — trust libraries
- Don't use print statements — use assertions
- Don't write tests that are too brittle

## Running Tests

```bash
pytest                                          # All tests
pytest tests/test_utils.py                      # Specific file
pytest tests/test_utils.py::test_function       # Specific test
pytest -v                                       # Verbose
pytest --cov=mypackage --cov-report=html        # Coverage
pytest -m "not slow"                            # Exclude slow
pytest -x                                       # Stop on first failure
pytest --lf                                     # Last failed
pytest -k "test_user"                           # Pattern match
```

**Remember**: Tests are code too. Keep them clean, readable, and maintainable. Good tests catch bugs; great tests prevent them.
