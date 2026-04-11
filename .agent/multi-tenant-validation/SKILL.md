---
name: multi-tenant-validation
description: Merge upstream bytedance/deer-flow, run unit tests, restart services with make dev-daemon, validate multi-tenant API according to backend/MULTI_TENANT_REPORT.md, validate frontend code, generate validation report, and verify the complete multi-tenant feature works correctly. Use this skill after merging upstream changes to automatically validate the entire multi-tenant feature end-to-end.
---

# Multi-Tenant Feature Validation Skill

This skill automates the complete validation workflow for the DeerFlow multi-tenant feature:
1. Merge upstream (bytedance/deer-flow) changes into current branch
2. Run all multi-tenant related unit tests
3. Validate frontend code (lint check)
4. **Stop all running services and restart with `make dev-daemon`** (ensures latest code is running)
5. Wait for all services to be healthy
6. Run comprehensive multi-tenant API validation according to the specification
7. Generate a validation report in markdown format
8. All isolation guarantees are verified (cross-user access is correctly blocked)

## Workflow

### Step 1: Merge Upstream
- Fetch and merge changes from https://github.com/bytedance/deer-flow upstream repository
- Conflicts must be resolved by the user if any

### Step 2: Run Unit Tests
- Run all multi-tenant related tests in `backend/tests/`:
  - `test_auth_jwt.py` - JWT creation/decoding/verification
  - `test_auth_router.py` - Authentication endpoints
  - `test_user_store.py` - User storage CRUD
  - `test_multi_tenant_config.py` - Configuration loading
  - `test_thread_metadata.py` - Thread metadata filtering
  - `test_thread_metadata_integration.py` - Integration tests
  - `test_user_context_middleware.py` - User context middleware
  - `test_file_helpers.py` - Atomic file operations

### Step 3: Frontend Validation
- Run ESLint to check for code errors
- Verify authentication components work with multi-tenant

### Step 4: Restart Services
- **Stop all running services** with `make stop`
- Start all services **fresh** in daemon mode (background) with `make dev-daemon`
- Automatically waits for gateway to be healthy (up to 60 seconds)
- This ensures the latest merged code is actually running

### Step 5: Run API Validation
Creates two test users and verifies all multi-tenant isolation guarantees:
| Test | Description | Expected |
|------|-------------|----------|
| Unauthenticated `/me` | No auth request | Returns default user |
| User registration | Register two distinct users | Both succeed |
| Duplicate registration | Register same email twice | Second fails with 400 |
| Wrong password login | Login with wrong password | Fails with 401 |
| Correct password login | Login with correct password | Succeeds with token |
| Create thread | Each user creates thread | `user_id` auto-injected |
| Search threads | User searches threads | Only sees own threads |
| Cross-user thread access | User A tries to access User B's thread | Blocked with 403 |
| Create agent | User creates agent | Agent metadata records `user_id` |
| List agents | User lists agents | Only sees own agents |
| Cross-user agent access | User A tries to access User B's agent | Blocked with 403 |
| Set/Get user profile | Profile storage by user | Isolated per-user storage |
| Invalid token | Request with invalid token | Falls back to default (200 OK, backward compatibility) |

### Step 6: Generate Report
- Outputs `MULTI_TENANT_API_VALIDATION_REPORT.md` with pass/fail results
- Shows success rate

## Usage

```
# Just invoke the skill - it will do everything from merge to report
/invoke multi-tenant-validation
```

## Requirements

- Git configured with upstream `https://github.com/bytedance/deer-flow`
- All dependencies installed (run `make install` first)
- multi-tenant enabled in `config.yaml`: `multi_tenant.enabled: true`
- Python requests library available

## Output

- `MULTI_TENANT_API_VALIDATION_REPORT.md` - Complete test results
- All services running in background (daemon mode) with latest code

