---
paths:
  - "**/*.py"
  - "**/*.pyi"
---
# Python Hooks

> Extends [common/hooks.md](../common/hooks.md) with Python-specific content.

## PostToolUse Hooks

Configured in `.claude/settings.json`:

- **ruff format**: Auto-format `.py` files after Edit/Write

## Recommended Additional Hooks

```json
{
  "PostToolUse": [
    {
      "matcher": "Edit|Write",
      "glob": "**/*.py",
      "hooks": [
        {"type": "command", "command": "cd $CLAUDE_PROJECT_DIR && uv run ruff check $CLAUDE_TOOL_INPUT_FILE_PATH 2>$null; exit 0"}
      ]
    }
  ]
}
```

## Warnings

- Warn about `print()` statements in edited files (use `logging` module instead)
- Warn about bare `except:` clauses (use `except Exception:`)
- Warn about mutable default arguments (`def fn(items=[])`)
