---
paths:
  - "**/*.py"
  - "**/*.pyi"
---
# Python Coding Style

> Extends [common/coding-style.md](../common/coding-style.md) with Python-specific content.

## Standards

- Follow **PEP 8** conventions (enforced by ruff)
- Use **type annotations** on all function signatures (enforced by mypy strict)
- Max line length: 100 (config in pyproject.toml)

## Immutability

Prefer immutable data structures:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    name: str
    email: str

from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float
```

## Formatting

- **ruff** for formatting (replaces black)
- **ruff** for import sorting (replaces isort)
- **ruff** for linting (replaces flake8)

## Naming

- `snake_case` — variables, functions, methods, modules
- `PascalCase` — classes, exceptions
- `UPPER_SNAKE_CASE` — constants, module-level config
- `_leading_underscore` — private/internal

## Logging

Use `logging` or `loguru` — never `print()`:

```python
import logging

logger = logging.getLogger(__name__)

def process_batch(items: list[dict]) -> int:
    logger.info("Processing %d items", len(items))
    ...
```
