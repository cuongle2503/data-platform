# Security Guidelines

## Mandatory Security Checks

Before ANY commit:
- [ ] No hardcoded secrets (API keys, passwords, tokens, connection strings)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries only)
- [ ] Authentication/authorization verified
- [ ] Error messages don't leak sensitive data
- [ ] Secrets loaded from env vars or secret manager, never in source

## Secret Management

```python
import os

# CORRECT: env var with validation
DATABASE_URL = os.environ["DATABASE_URL"]  # KeyError if missing

# NEVER:
# DATABASE_URL = "postgresql://user:pass@host/db"   # HARDCODED
```

- ALWAYS use environment variables or a secret manager
- Validate required secrets at startup
- Rotate any secrets that may have been exposed
- Use `.env.example` to document required vars (never commit `.env`)

## Security Response Protocol

If security issue found:
1. STOP immediately
2. Use **security-reviewer** agent
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review entire codebase for similar issues
