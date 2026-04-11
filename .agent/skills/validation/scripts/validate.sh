#!/bin/bash
# Run complete validation workflow
# Usage: bash scripts/validate.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=========================================="
echo "  DeerFlow Complete Validation"
echo "=========================================="
echo ""
echo "Project Root: $PROJECT_ROOT"
echo ""

# Temporary files for outputs
TEST_OUTPUT="/tmp/backend_test_results_$$.txt"
FRONTEND_OUTPUT="/tmp/frontend_lint_results_$$.txt"
BACKEND_OUTPUT="/tmp/backend_lint_results_$$.txt"
REPORT_OUTPUT="/tmp/validation_report_$$.md"

# Cleanup on exit
cleanup() {
    rm -f "$TEST_OUTPUT" "$FRONTEND_OUTPUT" "$BACKEND_OUTPUT"
}
trap cleanup EXIT

# Phase 1: Backend Tests
echo "Phase 1: Backend Unit Tests"
echo "=========================================="
"$SCRIPT_DIR/run_backend_tests.sh" "$TEST_OUTPUT" || true
echo ""

# Phase 2: Frontend Lint
echo "Phase 2: Frontend Linting"
echo "=========================================="
"$SCRIPT_DIR/run_frontend_lint.sh" "$FRONTEND_OUTPUT" || true
echo ""

# Phase 3: Backend Lint
echo "Phase 3: Backend Linting"
echo "=========================================="
"$SCRIPT_DIR/run_backend_lint.sh" "$BACKEND_OUTPUT" || true
echo ""

# Phase 4: Generate Report
echo "Phase 4: Generate Report"
echo "=========================================="
"$SCRIPT_DIR/generate_report.sh" "$TEST_OUTPUT" "$FRONTEND_OUTPUT" "$BACKEND_OUTPUT" "$REPORT_OUTPUT"

echo ""
echo "=========================================="
echo "  Validation Complete"
echo "=========================================="
echo ""
echo "Report: $REPORT_OUTPUT"
echo ""

# Display report
cat "$REPORT_OUTPUT"

# Copy report to project root
cp "$REPORT_OUTPUT" "$PROJECT_ROOT/validation_report.md"
echo ""
echo "Report copied to: $PROJECT_ROOT/validation_report.md"
