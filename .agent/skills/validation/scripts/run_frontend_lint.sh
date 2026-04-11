#!/bin/bash
# Run frontend ESLint
# Usage: bash scripts/run_frontend_lint.sh [output_file]

set -e

OUTPUT_FILE="${1:-/tmp/frontend_lint_results.txt}"
FRONTEND_DIR="$(cd "$(dirname "$0")/../.." && pwd)/frontend"

echo "=========================================="
echo "  Running Frontend Linting"
echo "=========================================="
echo ""
echo "Directory: $FRONTEND_DIR"
echo "Output: $OUTPUT_FILE"
echo ""

cd "$FRONTEND_DIR"

# Run ESLint
pnpm run lint 2>&1 | tee "$OUTPUT_FILE"

# Extract summary
echo ""
echo "=========================================="
echo "  Lint Summary"
echo "=========================================="

# Count errors and warnings
ERRORS=$(grep -oP '\d+(?= errors?)' "$OUTPUT_FILE" | head -1 || echo "0")
WARNINGS=$(grep -oP '\d+(?= warnings?)' "$OUTPUT_FILE" | head -1 || echo "0")

echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

# Determine status
if [ "$ERRORS" != "0" ]; then
    echo "Status: FAIL"
    exit 1
else
    echo "Status: PASS"
    exit 0
fi
