---
name: api-design
description: REST API design patterns including resource naming, status codes, pagination, filtering, error responses, and versioning for production APIs.
origin: ECC
---

# API Design Patterns

Conventions and best practices for designing consistent, developer-friendly REST APIs.

## When to Activate

- Designing new REST API endpoints
- Reviewing API contracts
- Setting up error handling and validation

## REST API Conventions

```
GET    /api/pipelines            # List all pipelines
GET    /api/pipelines/:id        # Get specific pipeline
POST   /api/pipelines            # Create new pipeline
PUT    /api/pipelines/:id        # Update pipeline (full)
PATCH  /api/pipelines/:id        # Update pipeline (partial)
DELETE /api/pipelines/:id        # Delete pipeline

# Query parameters for filtering
GET /api/pipelines?status=active&limit=20&offset=0&sort=-created_at
```

## Consistent Response Format

```python
@dataclass
class ApiResponse:
    success: bool
    data: Any | None = None
    error: str | None = None
    meta: dict | None = None  # {total, page, limit}

# Success
{
    "success": true,
    "data": [...],
    "meta": {"total": 100, "page": 1, "limit": 20}
}

# Error
{
    "success": false,
    "error": "Invalid request",
    "data": null
}
```

## HTTP Status Codes

| Code | When to Use |
|------|------------|
| 200 | Successful GET, PUT, PATCH |
| 201 | Successful POST (resource created) |
| 204 | Successful DELETE (no content) |
| 400 | Bad request (invalid input) |
| 401 | Unauthenticated |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 409 | Conflict (duplicate resource) |
| 422 | Validation error |
| 429 | Rate limited |
| 500 | Internal server error |

## Input Validation

```python
from pydantic import BaseModel, Field

class CreatePipelineRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    schedule: str = "0 6 * * *"  # cron expression
    tags: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("schedule")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        # Validate cron expression
        return v
```

## Pagination

```python
def paginate(query, page: int = 1, limit: int = 20) -> dict:
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    return {
        "data": items,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    }
```

## Error Handling (FastAPI)

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": str(exc)}
    )
```

## Rate Limiting

- Rate-limit auth and write-heavy endpoints
- Return 429 with `Retry-After` header
- Use shared store (Redis) for multi-instance deployments
