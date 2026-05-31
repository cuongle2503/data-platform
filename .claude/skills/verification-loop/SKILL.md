---
name: verification-loop
description: A comprehensive verification system for Claude Code sessions. Run after completing features, before PRs, or after refactoring.
origin: ECC (adapted for Python)
---

# Verification Loop

A comprehensive quality gate system for Python data platform projects.

## When to Activate

- After completing a feature or significant code change
- Before creating a PR
- After refactoring
- Before merging to main

## Verification Phases

### Phase 1: Lint Check

```bash
uv run ruff check .
```

If lint errors found, fix before continuing.

### Phase 2: Format Check

```bash
uv run ruff format --check .
```

### Phase 3: Type Check

```bash
uv run mypy .
```

Report all type errors. Fix critical ones before continuing.

### Phase 4: Test Suite

```bash
uv run pytest --cov=lib --cov=pipelines --cov-report=term-missing
```

Report:
- Total tests: X
- Passed: X
- Failed: X
- Coverage: X%

Target: 80%+ coverage, 0 failures.

### Phase 5: dbt Tests (if applicable)

```bash
cd dbt && dbt test
```

### Phase 6: Airflow DAG Integrity

```bash
uv run pytest tests/ -k "dag" -v
```

### Phase 7: Security Scan

```bash
# Hardcoded secrets
uv run bandit -r lib/ pipelines/

# Check for print() statements
rg "print\(" lib/ pipelines/ --include="*.py"

# Check for TODO/FIXME without tickets
rg "TODO|FIXME" lib/ pipelines/ --include="*.py"
```

### Phase 8: Diff Review

```bash
git diff --stat HEAD~1
git diff HEAD~1 --name-only
```

Review each changed file for:
- Unintended changes
- Missing error handling
- Missing type annotations
- Potential edge cases

## Verification Report Template

```
VERIFICATION REPORT
===================

Lint:      [PASS/FAIL] (N issues)
Format:    [PASS/FAIL] (N files changed)
Types:     [PASS/FAIL] (N errors)
Tests:     [PASS/FAIL] (X/Y passed, Z% coverage)
dbt:       [PASS/FAIL] (N failures)
Airflow:   [PASS/FAIL] (N DAG errors)
Security:  [PASS/FAIL] (N issues)
Diff:      [N files changed]

Overall:   [READY/NOT READY] for PR

Issues to Fix:
1. ...
2. ...
```

## Quick Check (for small changes)

```bash
uv run ruff check . && uv run mypy . && uv run pytest
```

## Integration with Pre-Commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
```

**Remember**: Run verification before every PR. A green verification report means production-ready code.
