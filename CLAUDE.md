# CLAUDE.md — Data Platform

This file guides Claude Code when working in this repository.

## Stack

- **Runtime**: Python >=3.11
- **Package manager**: uv (pyproject.toml)
- **Linter / Formatter**: ruff (replaces flake8 + isort + black)
- **Type checker**: mypy (strict mode)
- **Test framework**: pytest + pytest-cov
- **Database**: PostgreSQL (via SQLAlchemy / psycopg)
- **Pipeline**: dbt (transformations) + Apache Airflow (orchestration)

## Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy .

# dbt
cd dbt && dbt test && dbt run

# Airflow (local dev)
airflow standalone
```

## Code Style

- PEP 8 via ruff — line length 100
- Type annotations on every function signature (mypy strict)
- `snake_case` for variables, functions, files
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Frozen dataclasses for DTOs / config objects
- Context managers (`with`) for resource management
- Avoid `print()` — use `logging` module or `loguru`

## Project Structure

```
data-platform/
├── pipelines/          # DAG definitions
├── dbt/                # dbt models, tests, macros
├── plugins/            # Airflow plugins / custom operators
├── lib/                # Shared utilities
├── tests/              # pytest tests
├── pyproject.toml      # Project config + dependencies
└── dags/               # Airflow DAG files (if synced to Airflow)
```

## Key Conventions

### Data Pipeline
- Each DAG should have `doc_md` and `owner` attributes
- dbt models: file name = model name, use `ref()` instead of hardcoded table names
- Sources declared in `dbt/sources.yml`, freshness test for every source
- Idempotent pipelines: rerunning multiple times does not create duplicate data

### Database
- Parameterized queries — no string interpolation
- Migration files (dbt snapshots or Alembic) for schema changes
- Don't hardcode connection strings — use env vars

### Testing
- Unit tests for transformers, validators, utility functions
- Integration tests for database queries and dbt models (dbt test)
- Airflow DAG integrity test: `airflow dags test <dag_id>`

## Skills

Use the following skills when working on related tasks:

| Task | Skill |
|------|-------|
| `**/*.py` (write/review/refactor Python) | `python-patterns` |
| `tests/**`, write tests, setup pytest | `python-testing` |
| New features, bug fixes, refactoring | `tdd-workflow` |
| Before PR, after feature complete | `verification-loop` |
| `**/dags/**`, `**/dbt/**`, pipeline code | `data-pipeline` |
| Schema changes, migrations, Alembic | `database-migrations` |
| API endpoints, REST design | `api-design` |
| Code quality review, naming conventions | `coding-standards` |

Skills are auto-discovered from `.claude/skills/`. Claude will activate them automatically based on context. You can also invoke them manually: `/python-patterns`, `/tdd-workflow`, etc.
