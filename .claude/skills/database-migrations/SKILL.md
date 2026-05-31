---
name: database-migrations
description: Database migration best practices for schema changes, data migrations, rollbacks, and zero-downtime deployments for PostgreSQL.
origin: ECC
---

# Database Migration Patterns

Safe, reversible database schema changes for production systems.

## When to Activate

- Creating or altering database tables
- Adding/removing columns or indexes
- Running data migrations (backfill, transform)
- Planning zero-downtime schema changes
- Setting up migration tooling (Alembic, dbt snapshots)

## Core Principles

1. **Every change is a migration** — never alter production databases manually
2. **Migrations are forward-only in production** — rollbacks use new forward migrations
3. **Schema and data migrations are separate** — never mix DDL and DML in one migration
4. **Test migrations against production-sized data**
5. **Migrations are immutable once deployed** — never edit a migration that has run

## Migration Safety Checklist

- [ ] Migration has both UP and DOWN (or explicitly marked irreversible)
- [ ] No full table locks on large tables (use concurrent operations)
- [ ] New columns have defaults or are nullable
- [ ] Indexes created concurrently on large tables
- [ ] Data backfill is a separate migration from schema change
- [ ] Tested against production-like data
- [ ] Rollback plan documented

## PostgreSQL Patterns

### Adding a Column Safely

```sql
-- GOOD: Nullable column, no lock
ALTER TABLE users ADD COLUMN avatar_url TEXT;

-- GOOD: Column with default (Postgres 11+ instant)
ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;

-- BAD: NOT NULL without default
ALTER TABLE users ADD COLUMN role TEXT NOT NULL;
```

### Adding Index Without Downtime

```sql
-- GOOD: Non-blocking
CREATE INDEX CONCURRENTLY idx_users_email ON users (email);
```

### Renaming Column (Zero-Downtime)

```
Step 1: ADD new column (migration 001)
Step 2: Backfill data (migration 002)
Step 3: Update app to read/write both, deploy
Step 4: DROP old column (migration 003)
```

### Large Data Migrations

```sql
-- BAD: Single transaction
UPDATE users SET normalized_email = LOWER(email);

-- GOOD: Batched with checkpoint
DO $$
DECLARE
  batch_size INT := 10000;
  rows_updated INT;
BEGIN
  LOOP
    UPDATE users SET normalized_email = LOWER(email)
    WHERE id IN (
      SELECT id FROM users
      WHERE normalized_email IS NULL
      LIMIT batch_size FOR UPDATE SKIP LOCKED
    );
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    EXIT WHEN rows_updated = 0;
    COMMIT;
  END LOOP;
END $$;
```

## Alembic (Python)

```bash
# Create migration
alembic revision --autogenerate -m "add_user_avatar"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Show history
alembic history
```

### Data Migration with Alembic

```python
def upgrade():
    op.add_column("users", sa.Column("display_name", sa.String()))
    # Data migration in same file but separate operation
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE users SET display_name = username"))

def downgrade():
    op.drop_column("users", "display_name")
```

## dbt Snapshots (SCD Type 2)

```sql
{% snapshot orders_snapshot %}
  {{
    config(
      target_schema='snapshots',
      unique_key='id',
      strategy='timestamp',
      updated_at='updated_at',
    )
  }}
  SELECT * FROM {{ source('raw', 'orders') }}
{% endsnapshot %}
```

## Zero-Downtime Migration Strategy

```
Phase 1: EXPAND
  - Add new column/table (nullable or with default)
  - Deploy: app writes to BOTH old and new
  - Backfill existing data

Phase 2: MIGRATE
  - Deploy: app reads from NEW, writes to BOTH
  - Verify data consistency

Phase 3: CONTRACT
  - Deploy: app only uses NEW
  - Drop old column/table in separate migration
```

## Anti-Patterns

| Anti-Pattern | Better Approach |
|-------------|-----------------|
| Manual SQL in production | Always use migration files |
| Editing deployed migrations | Create new migration instead |
| NOT NULL without default | Add nullable → backfill → add constraint |
| Inline index on large table | CREATE INDEX CONCURRENTLY |
| Schema + data in one migration | Separate migrations |
| Dropping column before removing code | Remove code first, drop column next deploy |
