---
paths:
  - "**/*.py"
  - "**/*.pyi"
---
# Python Security

> Extends [common/security.md](../common/security.md) with Python-specific content.

## Secret Management

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["OPENAI_API_KEY"]  # Raises KeyError if missing
db_url = os.environ["DATABASE_URL"]
```

## Security Scanning

- Use **bandit** for static security analysis:

```bash
uv run bandit -r lib/ pipelines/
```

## SQL Injection Prevention

ALWAYS use parameterized queries:

```python
# CORRECT: parameterized
conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# WRONG: string interpolation
conn.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

## Dependency Scanning

```bash
uv sync --refresh   # update lockfile
pip-audit           # check for known vulnerabilities
```
