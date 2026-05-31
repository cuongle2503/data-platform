---
name: coding-standards
description: Baseline cross-project coding conventions for naming, readability, immutability, and code-quality review.
origin: ECC
---

# Coding Standards & Best Practices

Baseline coding conventions applicable across projects.

## When to Activate

- Starting a new project or module
- Reviewing code for quality and maintainability
- Refactoring existing code to follow conventions
- Enforcing naming, formatting, or structural consistency

## Code Quality Principles

### 1. Readability First
- Code is read more than written
- Clear variable and function names
- Self-documenting code preferred over comments
- Consistent formatting

### 2. KISS (Keep It Simple, Stupid)
- Simplest solution that works
- Avoid over-engineering
- No premature optimization

### 3. DRY (Don't Repeat Yourself)
- Extract common logic into functions
- Create reusable utilities
- Avoid copy-paste programming

### 4. YAGNI (You Aren't Gonna Need It)
- Don't build features before they're needed
- Avoid speculative generality
- Start simple, refactor when needed

## Naming Conventions

### Python
```python
# GOOD: Descriptive names
market_search_query = "election"
is_user_authenticated = True
total_revenue = 1000

# BAD: Unclear names
q = "election"
flag = True
x = 1000
```

### Function Naming
```python
# GOOD: Verb-noun pattern
def fetch_market_data(market_id: str): ...
def calculate_similarity(a: list[float], b: list[float]): ...
def is_valid_email(email: str) -> bool: ...

# BAD: Noun-only or unclear
def market(id): ...
def similarity(a, b): ...
def email(e): ...
```

### SQL Naming (dbt)
```sql
-- GOOD: snake_case, descriptive
SELECT customer_id, COUNT(*) AS order_count
FROM {{ ref('stg_orders') }}

-- BAD: ambiguous names
SELECT cid, COUNT(*) AS cnt
FROM orders
```

## Immutability (CRITICAL)

```python
# GOOD: Create new objects
@dataclass(frozen=True)
class Config:
    batch_size: int
    max_retries: int

def with_batch_size(config: Config, size: int) -> Config:
    return replace(config, batch_size=size)

# BAD: Mutate in-place
config.batch_size = 200
```

## Error Handling

```python
# GOOD: Comprehensive
def fetch_data(url: str) -> dict:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        logger.error("Timeout fetching %s", url)
        raise DataFetchError(f"Timeout: {url}")
    except requests.HTTPError as e:
        logger.error("HTTP %s from %s", e.response.status_code, url)
        raise DataFetchError(f"HTTP error from {url}") from e

# BAD: No error handling
def fetch_data(url: str) -> dict:
    return requests.get(url).json()
```

## Code Smell Detection

### Long Functions
- Functions >50 lines → split into smaller focused functions
- Files >800 lines → extract module

### Deep Nesting
```python
# GOOD: Early returns
def process(user, market, permission):
    if not user: return
    if not user.is_admin: return
    if not market: return
    if not market.is_active: return
    if not permission: return
    # Main logic

# BAD: Deep nesting
def process(user, market, permission):
    if user:
        if user.is_admin:
            if market:
                if market.is_active:
                    if permission:
                        # Main logic
```

### Magic Numbers
```python
# GOOD: Named constants
MAX_RETRIES = 3
DEBOUNCE_DELAY_SEC = 0.5

# BAD: Unexplained numbers
if retry_count > 3: ...
time.sleep(0.5)
```

## Code Quality Checklist

Before marking work complete:
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling
- [ ] No hardcoded values (use constants or config)
- [ ] No mutation (immutable patterns used)
- [ ] Type annotations on all function signatures (Python)
