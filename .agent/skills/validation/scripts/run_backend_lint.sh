#!/bin/bash
# Run backend ruff linting
# Usage: bash scripts/run_backend_lint.sh [output_file]

set -e

OUTPUT_FILE="${1:-/tmp/backend_lint_results.txt}"
BACKEND_DIR="$(cd "$(dirname "$0")/../.." && pwd)/backend"

echo "=========================================="
echo "  Running Backend Linting (ruff)"
echo "=========================================="
echo ""
echo "Directory: $BACKEND_DIR"
echo "Output: $OUTPUT_FILE"
echo ""

cd "$BACKEND_DIR"

# Run ruff check
uv run ruff check . 2>&1 | tee "$OUTPUT_FILE"

# Extract summary
echo ""
echo "=========================================="
echo "  Lint Summary"
echo "=========================================="

# Count errors and warnings
ERRORS=$(grep -c "^E" "$OUTPUT_FILE" || echo "0")
WARNINGS=$(grep -c "^W" "$OUTPUT_FILE" || echo "0")
FIXABLE=$(grep -c "\[\*\]" "$OUTPUT_FILE" || echo "0")

echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"
echo "Fixable:  $FIXABLE"
echo ""

# Determine status
if [ "$ERRORS" != "0" ]; then
    echo "Status: FAIL"
    exit 1
else
    echo "Status: PASS (warnings: $WARNINGS, fixable: $FIXABLE)"
    exit 0
fi
