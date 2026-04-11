#!/bin/bash
# Run all backend unit tests
# Usage: bash scripts/run_backend_tests.sh [output_file]

set -e

OUTPUT_FILE="${1:-/tmp/backend_test_results.txt}"
BACKEND_DIR="$(cd "$(dirname "$0")/../.." && pwd)/backend"

echo "=========================================="
echo "  Running Backend Unit Tests"
echo "=========================================="
echo ""
echo "Directory: $BACKEND_DIR"
echo "Output: $OUTPUT_FILE"
echo ""

cd "$BACKEND_DIR"

# Run tests with verbose output
.venv/bin/python -m pytest tests/ \
    -v \
    --tb=short \
    --durations=10 \
    2>&1 | tee "$OUTPUT_FILE"

# Extract summary
echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="

# Count results
PASSED=$(grep -oP '\d+(?= passed)' "$OUTPUT_FILE" | head -1 || echo "0")
FAILED=$(grep -oP '\d+(?= failed)' "$OUTPUT_FILE" | head -1 || echo "0")
SKIPPED=$(grep -oP '\d+(?= skipped)' "$OUTPUT_FILE" | head -1 || echo "0")
ERRORS=$(grep -oP '\d+(?= errors)' "$OUTPUT_FILE" | head -1 || echo "0")

echo "Passed:  $PASSED"
echo "Failed:  $FAILED"
echo "Skipped: $SKIPPED"
echo "Errors:  $ERRORS"
echo ""

# Determine status
if [ "$FAILED" != "0" ] || [ "$ERRORS" != "0" ]; then
    echo "Status: FAIL"
    exit 1
else
    echo "Status: PASS"
    exit 0
fi
