---
name: validation
description: Run comprehensive validation for DeerFlow project including: 1) Backend unit tests, 2) Frontend linting, 3) Backend linting (ruff), 4) Generate validation report. Use when user says "run validation", "run all tests", "check code quality", "validate project", "run tests and lint", or similar.
---

# DeerFlow Validation Skill

This skill runs comprehensive validation across the entire DeerFlow project, including backend unit tests, frontend linting, backend linting, and generates a detailed validation report.

## Structure

```
validation/
├── SKILL.md                          ← You are here - core workflow and logic
├── scripts/
│   ├── run_backend_tests.sh          ← Run all backend unit tests
│   ├── run_frontend_lint.sh          ← Run frontend ESLint
│   ├── run_backend_lint.sh           ← Run backend ruff linting
│   └── generate_report.sh            ← Generate validation report
├── references/
│   ├── test_guidelines.md            ← Testing best practices
│   └── fix_common_issues.md          ← How to fix common lint/test issues
└── templates/
    └── report.template.md            ← Validation report template
```

## Validation Workflow

### Phase 1: Backend Unit Tests

1. **Navigate to backend directory**
   - Change to `backend/` directory
   - Ensure virtual environment is activated

2. **Run all backend tests**
   ```bash
   cd backend
   .venv/bin/python -m pytest tests/ -v --tb=short
   ```

3. **Collect test results**
   - Count: passed, failed, skipped, errors
   - Record test duration
   - Capture any warnings or errors

4. **Identify failing tests**
   - List all failed test names
   - Capture failure messages
   - Categorize by test module

### Phase 2: Frontend Linting

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Run ESLint**
   ```bash
   pnpm run lint
   ```

3. **Collect lint results**
   - Count: errors, warnings
   - Record file paths with issues
   - Capture specific rule violations

### Phase 3: Backend Linting

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Run ruff check**
   ```bash
   uv run ruff check .
   ```

3. **Collect lint results**
   - Count: errors, warnings, fixable issues
   - Record file paths with issues
   - Capture specific rule violations (e.g., I001, UP045)

### Phase 4: Generate Validation Report

1. **Collect all results**
   - Backend test summary
   - Frontend lint summary
   - Backend lint summary

2. **Determine overall status**
   - PASS: All tests pass, no lint errors (warnings OK)
   - FAIL: Any test failures or lint errors

3. **Generate report using template**
   - Use `templates/report.template.md`
   - Fill in all sections with actual results
   - Include recommendations for fixes

## Execution Rules

- **Sequential execution** - Run phases in order (tests → frontend lint → backend lint → report)
- **Continue on warnings** - Warnings should not stop execution
- **Stop on critical errors** - If a phase completely fails (e.g., pytest crashes), report and continue to next phase
- **Comprehensive logging** - Capture stdout/stderr from all commands
- **Idempotency** - Safe to run multiple times
- **Report requirement** - Always generate a report, even if validation fails

## Success Criteria

Validation PASS criteria:
- [x] Backend tests: 0 failures, 0 errors (warnings OK)
- [x] Frontend lint: 0 errors (warnings OK)
- [x] Backend lint: 0 errors (warnings/fixable OK)
- [x] Report generated successfully

Validation FAIL criteria:
- [ ] Any backend test failures
- [ ] Any backend test errors
- [ ] Any frontend lint errors
- [ ] Any backend lint errors

## Known Acceptable Warnings

The following warnings are acceptable and do not cause validation failure:

**Backend Tests:**
- Deprecation warnings from dependencies (e.g., websockets, pydantic)
- UserWarnings from Pydantic serialization
- Live test skips (if config unavailable)

**Frontend Lint:**
- `@typescript-eslint/no-unused-vars` warnings
- Any ESLint warnings (not errors)

**Backend Lint:**
- `I001` - Import sorting (auto-fixable)
- `UP045` - Type annotation style (Optional vs X | None)
- Any ruff warnings (not errors)

## Key Tools

Use the following tools during execution:

1. **bash** - Run shell commands for tests and linting
2. **read** - Read generated reports and logs
3. **write** - Generate validation report
4. **present_file** - Present the final validation report to user

## Report Format

The validation report must use `templates/report.template.md` and include:

1. **Overall Status** - PASS/FAIL with summary
2. **Backend Tests** - Detailed test results
3. **Frontend Lint** - Linting results
4. **Backend Lint** - Linting results
5. **Action Items** - Specific fixes needed (if any)
6. **Recommendations** - Suggestions for improving code quality

## Troubleshooting

If validation fails:

1. **Read failure details** - Examine specific error messages
2. **Categorize issues** - Group by type (test failure, lint error, etc.)
3. **Provide fix guidance** - Reference `references/fix_common_issues.md`
4. **Offer to fix** - Ask user if they want help fixing issues

## Related Commands

Manual commands user can run:

```bash
# Backend tests only
cd backend && uv run pytest tests/ -v

# Frontend lint only
cd frontend && pnpm run lint

# Backend lint only
cd backend && uv run ruff check .

# Backend lint auto-fix
cd backend && uv run ruff check . --fix
```
