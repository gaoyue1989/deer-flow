#!/bin/bash
# Full validation workflow with service restart
set -e

echo "=== multi-tenant-validation full workflow ==="
echo ""

# Step 1: Fetch and merge upstream
echo "▶ Step 1/6: Fetching upstream..."
git fetch upstream
echo "Merging upstream/main into current branch..."
git merge upstream/main --no-edit
echo ""

# Step 2: Run unit tests
echo "▶ Step 2/6: Running multi-tenant unit tests..."
cd backend
PYTHONPATH=. uv run pytest tests/test_auth_jwt.py tests/test_auth_router.py tests/test_user_store.py tests/test_multi_tenant_config.py tests/test_thread_metadata.py tests/test_thread_metadata_integration.py tests/test_user_context_middleware.py tests/test_file_helpers.py -v
cd ..
echo ""

# Step 3: Frontend lint check
echo "▶ Step 3/6: Frontend ESLint check..."
cd frontend
pnpm run lint
cd ..
echo ""

# Step 4: Restart services with make dev-daemon
echo "▶ Step 4/6: Restarting services with make dev-daemon..."
make stop
sleep 5
make dev-daemon
echo ""
sleep 10  # Wait for services to start

# Check if gateway is healthy
echo "Checking gateway health..."
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null; then
        echo "✓ Gateway is healthy"
        break
    fi
    echo "Waiting for gateway... ($i/30)"
    sleep 2
done

if ! curl -s http://localhost:8001/health > /dev/null; then
    echo "❌ Gateway failed to start"
    exit 1
fi
echo ""

# Step 5: Run API validation
echo "▶ Step 5/6: Running full multi-tenant API validation..."
mkdir -p memory user_profiles
python3 skills/public/multi-tenant-validation/scripts/validate_api.py
echo ""

# Step 6: Show result
echo "▶ Step 6/6: Complete"
echo "Report saved to MULTI_TENANT_API_VALIDATION_REPORT.md"
echo ""

cat MULTI_TENANT_API_VALIDATION_REPORT.md
