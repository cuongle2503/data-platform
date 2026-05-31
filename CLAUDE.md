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
- Type annotations trên mọi function signature (mypy strict)
- `snake_case` cho variables, functions, files
- `PascalCase` cho classes
- `UPPER_SNAKE_CASE` cho constants
- Frozen dataclasses cho DTOs / config objects
- Context managers (`with`) cho resource management
- Không dùng `print()` — dùng `logging` module hoặc `loguru`

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
- Mỗi DAG nên có `doc_md` và `owner` attribute
- dbt models: tên file = tên model, dùng `ref()` thay vì table name cứng
- Sources khai báo trong `dbt/sources.yml`, freshness test cho mọi source
- Idempotent pipelines: chạy lại nhiều lần không tạo duplicate data

### Database
- Parameterized queries — không string interpolation
- Migration files (dbt snapshots hoặc Alembic) cho schema changes
- Không hardcode connection strings — dùng env vars

### Testing
- Unit test cho transformers, validators, utility functions
- Integration test cho database queries và dbt models (dbt test)
- Airflow DAG integrity test: `airflow dags test <dag_id>`

## Skills

Use the following skills when working on related tasks:

| Task | Skill |
|------|-------|
| `**/*.py` (viết/review/refactor Python) | `python-patterns` |
| `tests/**`, viết test, setup pytest | `python-testing` |
| Feature mới, fix bug, refactor | `tdd-workflow` |
| Trước PR, after feature complete | `verification-loop` |
| `**/dags/**`, `**/dbt/**`, pipeline code | `data-pipeline` |
| Schema changes, migrations, Alembic | `database-migrations` |
| API endpoints, REST design | `api-design` |
| Code quality review, naming conventions | `coding-standards` |

Skills are auto-discovered from `.claude/skills/`. Claude will activate them automatically based on context. You can also invoke them manually: `/python-patterns`, `/tdd-workflow`, etc.
