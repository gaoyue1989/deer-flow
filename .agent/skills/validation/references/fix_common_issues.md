# Fix Common Validation Issues

## Backend Test Failures

### Test Fails with "User not found" (401)

**Cause**: Invalid or expired LLM API key in `config.yaml`

**Fix**:
1. Check which model is configured as default
2. Verify API key is valid:
   ```bash
   curl -X POST "https://api.example.com/v1/chat/completions" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "your-model", "messages": [{"role": "user", "content": "hi"}]}'
   ```
3. Update `config.yaml` with valid API key
4. Reorder models if needed (first model is default)

### Test Fails with ModuleNotFoundError

**Cause**: Missing Python dependency

**Fix**:
```bash
cd backend
uv add <package-name>
```

### Test Fails with Import Error (deerflow not found)

**Cause**: deerflow harness package not installed

**Fix**:
```bash
cd backend/packages/harness
uv pip install -e .
```

### DBUserStore Tests Error (TypeEr...)

**Cause**: Type evaluation error, often due to Python version or type annotation issues

**Fix**:
1. Check Python version compatibility
2. Review type annotations in `db_store.py`
3. Consider using `from __future__ import annotations`

## Frontend Lint Errors

### ESLint Errors

**Common issues**:
- Missing semicolons
- Unused variables
- Type errors in TypeScript

**Fix**:
```bash
cd frontend
pnpm run lint --fix
```

For manual fixes, edit the file at the specified line number.

## Backend Lint Errors

### Ruff I001 (Import sorting)

**Fix automatically**:
```bash
cd backend
uv run ruff check . --fix
```

**Fix manually**: Organize imports in this order:
1. `from __future__` imports
2. Standard library imports
3. Third-party imports
4. Local application imports

### Ruff UP045 (Optional type annotation)

**Issue**: Using `Optional[X]` instead of `X | None`

**Fix automatically**:
```bash
cd backend
uv run ruff check . --fix
```

**Fix manually**:
```python
# Before
def func() -> Optional[dict]:

# After
def func() -> dict | None:
```

### Ruff E*** (Error codes)

Review the specific error code and fix according to ruff documentation:
```bash
uv run ruff rule <ERROR_CODE>
```

## Running Auto-Fix

For both frontend and backend:

```bash
# Backend auto-fix
cd backend
uv run ruff check . --fix

# Frontend auto-fix
cd frontend
pnpm run lint --fix
```

## Validation After Fixes

Always re-run validation after applying fixes:

```bash
# Full validation
cd backend && uv run pytest tests/ -q
cd frontend && pnpm run lint
cd backend && uv run ruff check .
```
