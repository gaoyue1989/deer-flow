# DeerFlow Validation Report

**Generated**: {{TIMESTAMP}}
**Branch**: {{BRANCH}}
**Commit**: {{COMMIT}}

---

## Overall Status: {{STATUS}}

{{SUMMARY}}

---

## Backend Unit Tests

**Command**: `cd backend && uv run pytest tests/ -v`

### Summary

| Metric | Count |
|--------|-------|
| Passed | {{TESTS_PASSED}} |
| Failed | {{TESTS_FAILED}} |
| Skipped | {{TESTS_SKIPPED}} |
| Errors | {{TESTS_ERRORS}} |
| Duration | {{TESTS_DURATION}} |

### Status: {{TEST_STATUS}}

{{TEST_DETAILS}}

### Failed Tests

{{FAILED_TESTS_LIST}}

---

## Frontend Linting

**Command**: `cd frontend && pnpm run lint`

### Summary

| Metric | Count |
|--------|-------|
| Errors | {{FRONTEND_ERRORS}} |
| Warnings | {{FRONTEND_WARNINGS}} |

### Status: {{FRONTEND_STATUS}}

{{FRONTEND_DETAILS}}

### Issues

{{FRONTEND_ISSUES_LIST}}

---

## Backend Linting

**Command**: `cd backend && uv run ruff check .`

### Summary

| Metric | Count |
|--------|-------|
| Errors | {{BACKEND_ERRORS}} |
| Warnings | {{BACKEND_WARNINGS}} |
| Fixable | {{BACKEND_FIXABLE}} |

### Status: {{BACKEND_STATUS}}

{{BACKEND_DETAILS}}

### Issues

{{BACKEND_ISSUES_LIST}}

---

## Action Items

{{ACTION_ITEMS}}

---

## Recommendations

{{RECOMMENDATIONS}}

---

## Appendix: Raw Output

### Backend Test Output

```
{{RAW_TEST_OUTPUT}}
```

### Frontend Lint Output

```
{{RAW_FRONTEND_OUTPUT}}
```

### Backend Lint Output

```
{{RAW_BACKEND_OUTPUT}}
```
