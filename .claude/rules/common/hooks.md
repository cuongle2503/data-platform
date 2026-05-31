# Hooks System

## Hook Types

- **PreToolUse**: Before tool execution (validation, parameter modification)
- **PostToolUse**: After tool execution (auto-format, checks)
- **Stop**: When session ends (final verification)

## Configured Hooks (this project)

| Hook | Trigger | Action |
|------|---------|--------|
| PostToolUse | Edit/Write `*.py` | `ruff format` auto-format |

## Adding New Hooks

Edit `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "glob": "**/pytest*",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Running tests...'"
          }
        ]
      }
    ]
  }
}
```

## Best Practices

- PostToolUse hooks: keep fast (<1s)
- Always `exit 0` on failure — never block the user's tool
- Use `$CLAUDE_PROJECT_DIR` and `$CLAUDE_TOOL_INPUT_FILE_PATH` env vars
