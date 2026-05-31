# Common Patterns

## Repository Pattern

Encapsulate data access behind a consistent interface:

```python
from typing import Protocol, TypeVar

T = TypeVar("T")

class Repository(Protocol[T]):
    def find_all(self) -> list[T]: ...
    def find_by_id(self, id: str) -> T | None: ...
    def create(self, entity: T) -> T: ...
    def update(self, entity: T) -> T: ...
    def delete(self, id: str) -> None: ...
```

- Business logic depends on the abstract interface, not the storage mechanism
- Enables easy swapping of data sources and simplifies testing with mocks

## Data Transfer Objects (DTOs)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class PipelineRun:
    run_id: str
    dag_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
```

## Pipeline Patterns

### Idempotency

Every pipeline run MUST be idempotent:
- Use `MERGE` / `INSERT ... ON CONFLICT` instead of `INSERT`
- Delete-write only when necessary and scoped to partition
- Checkpoint intermediate results so partial reruns are safe

### Configuration

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class PipelineConfig:
    source_db: str
    target_db: str
    batch_size: int = 10000
    max_retries: int = 3
```
