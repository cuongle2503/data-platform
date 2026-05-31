---
name: python-patterns
description: Pythonic idioms, PEP 8 standards, type hints, and best practices for building robust, efficient, and maintainable Python applications.
origin: ECC
---

# Python Development Patterns

Idiomatic Python patterns and best practices for building robust, efficient, and maintainable applications.

## When to Activate

- Writing new Python code
- Reviewing Python code
- Refactoring existing Python code
- Designing Python packages/modules

## Core Principles

### 1. Readability Counts

Python prioritizes readability. Code should be obvious and easy to understand.

```python
# Good: Clear and readable
def get_active_users(users: list[User]) -> list[User]:
    """Return only active users from the provided list."""
    return [user for user in users if user.is_active]


# Bad: Clever but confusing
def get_active_users(u):
    return [x for x in u if x.a]
```

### 2. Explicit is Better Than Implicit

Avoid magic; be clear about what your code does.

### 3. EAFP - Easier to Ask Forgiveness Than Permission

Python prefers exception handling over checking conditions.

```python
# Good: EAFP style
def get_value(dictionary: dict, key: str) -> Any:
    try:
        return dictionary[key]
    except KeyError:
        return default_value
```

## Type Hints

### Modern Type Hints (Python 3.9+)

```python
def process_items(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}
```

### Protocol-Based Duck Typing

```python
from typing import Protocol

class Renderable(Protocol):
    def render(self) -> str: ...

def render_all(items: list[Renderable]) -> str:
    return "\n".join(item.render() for item in items)
```

## Error Handling

- Catch specific exceptions, never bare `except:`
- Chain exceptions with `raise ... from e`
- Create custom exception hierarchy: `class AppError(Exception)`

## Context Managers

```python
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    logger.info("%s took %.4fs", name, elapsed)

class DatabaseTransaction:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.begin_transaction()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        return False
```

## Comprehensions and Generators

- List comprehensions for simple transformations
- Generator expressions for lazy evaluation: `sum(x * x for x in range(1_000_000))`
- Generator functions for large file processing

## Data Classes and Named Tuples

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class User:
    id: str
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def __post_init__(self):
        if "@" not in self.email:
            raise ValueError(f"Invalid email: {self.email}")
```

## Package Organization

```
myproject/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       ├── models/
│       └── utils/
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_models.py
├── pyproject.toml
└── README.md
```

## Anti-Patterns to Avoid

```python
# BAD: Mutable default arguments
def append_to(item, items=[]): ...

# GOOD: Use None
def append_to(item, items=None):
    if items is None:
        items = []
    ...

# BAD: Checking type with type()
if type(obj) == list: ...

# GOOD: Use isinstance
if isinstance(obj, list): ...

# BAD: from module import *
# GOOD: Explicit imports

# BAD: Bare except
try: risky()
except: pass

# GOOD: Specific exception
try: risky()
except SpecificError as e: logger.error(...)
```

## Quick Reference

| Idiom | Description |
|-------|-------------|
| EAFP | Easier to Ask Forgiveness than Permission |
| Context managers | Use `with` for resource management |
| List comprehensions | For simple transformations |
| Generators | For lazy evaluation and large datasets |
| Type hints | Annotate function signatures |
| Dataclasses | For data containers with auto-generated methods |
| f-strings | For string formatting (Python 3.6+) |
| `pathlib.Path` | For path operations |
| `enumerate` | For index-element pairs in loops |

**Remember**: Python code should be readable, explicit, and follow the principle of least surprise. When in doubt, prioritize clarity over cleverness.
