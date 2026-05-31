---
paths:
  - "**/*.py"
  - "**/*.pyi"
---
# Python Patterns

> Extends [common/patterns.md](../common/patterns.md) with Python-specific content.

## Protocol (Duck Typing)

```python
from typing import Protocol

class Repository(Protocol):
    def find_by_id(self, id: str) -> dict | None: ...
    def save(self, entity: dict) -> dict: ...
```

## Dataclasses as DTOs

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class CreateUserRequest:
    name: str
    email: str
    age: int | None = None
```

## Context Managers & Generators

- Use context managers (`with` statement) for resource management
- Use generators for lazy evaluation and memory-efficient iteration

```python
def read_batches(filepath: str, batch_size: int = 1000):
    """Generator: yields batches without loading entire file."""
    batch = []
    with open(filepath) as f:
        for line in f:
            batch.append(line.strip())
            if len(batch) >= batch_size:
                yield batch
                batch = []
    if batch:
        yield batch
```

## Decorators

```python
import functools
import time

def retry(max_attempts: int = 3, delay: float = 1.0):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))
        return wrapper
    return decorator
```
