#!/bin/bash
# Generate validation report from raw outputs
# Usage: bash scripts/generate_report.sh [test_output] [frontend_output] [backend_output] [report_output]

set -e

TEST_OUTPUT="${1:-/tmp/backend_test_results.txt}"
FRONTEND_OUTPUT="${2:-/tmp/frontend_lint_results.txt}"
BACKEND_OUTPUT="${3:-/tmp/backend_lint_results.txt}"
REPORT_OUTPUT="${4:-/tmp/validation_report.md}"

TEMPLATE_FILE="$(cd "$(dirname "$0")/../templates" && pwd)/report.template.md"

echo "Generating validation report..."

# Get current timestamp
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
BRANCH=$(git -C "$(dirname "$0")/../.." rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
COMMIT=$(git -C "$(dirname "$0")/../.." rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Parse test results
TESTS_PASSED=$(grep -oP '\d+(?= passed)' "$TEST_OUTPUT" | head -1 || echo "0")
TESTS_FAILED=$(grep -oP '\d+(?= failed)' "$TEST_OUTPUT" | head -1 || echo "0")
TESTS_SKIPPED=$(grep -oP '\d+(?= skipped)' "$TEST_OUTPUT" | head -1 || echo "0")
TESTS_ERRORS=$(grep -oP '\d+(?= errors)' "$TEST_OUTPUT" | head -1 || echo "0")
TESTS_DURATION=$(grep -oP 'in [\d.]+s' "$TEST_OUTPUT" | tail -1 || echo "unknown")

# Parse frontend lint results
FRONTEND_ERRORS=$(grep -oP '\d+(?= errors)' "$FRONTEND_OUTPUT" | head -1 || echo "0")
FRONTEND_WARNINGS=$(grep -oP '\d+(?= warnings)' "$FRONTEND_OUTPUT" | head -1 || echo "0")

# Parse backend lint results
BACKEND_ERRORS=$(grep -c "^E" "$BACKEND_OUTPUT" || echo "0")
BACKEND_WARNINGS=$(grep -c "^W" "$BACKEND_OUTPUT" || echo "0")
BACKEND_FIXABLE=$(grep -c "\[\*\]" "$BACKEND_OUTPUT" || echo "0")

# Determine overall status
if [ "$TESTS_FAILED" != "0" ] || [ "$TESTS_ERRORS" != "0" ] || [ "$FRONTEND_ERRORS" != "0" ] || [ "$BACKEND_ERRORS" != "0" ]; then
    STATUS="FAIL"
    SUMMARY="Validation failed. There are test failures or lint errors that need to be addressed."
else
    STATUS="PASS"
    SUMMARY="All validation checks passed successfully."
fi

# Determine test status
if [ "$TESTS_FAILED" != "0" ] || [ "$TESTS_ERRORS" != "0" ]; then
    TEST_STATUS="FAIL"
else
    TEST_STATUS="PASS"
fi

# Determine frontend status
if [ "$FRONTEND_ERRORS" != "0" ]; then
    FRONTEND_STATUS="FAIL"
else
    FRONTEND_STATUS="PASS"
fi

# Determine backend status
if [ "$BACKEND_ERRORS" != "0" ]; then
    BACKEND_STATUS="FAIL"
else
    BACKEND_STATUS="PASS"
fi

# Extract failed tests
FAILED_TESTS_LIST=""
if [ "$TESTS_FAILED" != "0" ] || [ "$TESTS_ERRORS" != "0" ]; then
    FAILED_TESTS_LIST=$(grep "^FAILED\|^ERROR" "$TEST_OUTPUT" | head -20 || echo "See test output for details")
fi

# Generate action items
ACTION_ITEMS=""
if [ "$TESTS_FAILED" != "0" ] || [ "$TESTS_ERRORS" != "0" ]; then
    ACTION_ITEMS="${ACTION_ITEMS}1. **Fix failing tests** - Review test failures and fix underlying issues\n"
fi
if [ "$FRONTEND_ERRORS" != "0" ]; then
    ACTION_ITEMS="${ACTION_ITEMS}2. **Fix frontend lint errors** - Run \`pnpm run lint --fix\` or fix manually\n"
fi
if [ "$BACKEND_ERRORS" != "0" ]; then
    ACTION_ITEMS="${ACTION_ITEMS}3. **Fix backend lint errors** - Run \`uv run ruff check . --fix\` or fix manually\n"
fi
if [ -z "$ACTION_ITEMS" ]; then
    ACTION_ITEMS="No action items - all checks passed!"
fi

# Generate recommendations
RECOMMENDATIONS=""
if [ "$BACKEND_FIXABLE" != "0" ]; then
    RECOMMENDATIONS="${RECOMMENDATIONS}- Run \`uv run ruff check . --fix\` to auto-fix $BACKEND_FIXABLE issues\n"
fi
if [ "$FRONTEND_WARNINGS" != "0" ]; then
    RECOMMENDATIONS="${RECOMMENDATIONS}- Review $FRONTEND_WARNINGS frontend warnings for potential improvements\n"
fi
if [ "$BACKEND_WARNINGS" != "0" ]; then
    RECOMMENDATIONS="${RECOMMENDATIONS}- Review $BACKEND_WARNINGS backend warnings for code quality improvements\n"
fi
if [ -z "$RECOMMENDATIONS" ]; then
    RECOMMENDATIONS="No additional recommendations."
fi

# Read template and replace placeholders
REPORT=$(cat "$TEMPLATE_FILE")
REPORT="${REPORT//\{\{TIMESTAMP\}\}/$TIMESTAMP}"
REPORT="${REPORT//\{\{BRANCH\}\}/$BRANCH}"
REPORT="${REPORT//\{\{COMMIT\}\}/$COMMIT}"
REPORT="${REPORT//\{\{STATUS\}\}/$STATUS}"
REPORT="${REPORT//\{\{SUMMARY\}\}/$SUMMARY}"
REPORT="${REPORT//\{\{TESTS_PASSED\}\}/$TESTS_PASSED}"
REPORT="${REPORT//\{\{TESTS_FAILED\}\}/$TESTS_FAILED}"
REPORT="${REPORT//\{\{TESTS_SKIPPED\}\}/$TESTS_SKIPPED}"
REPORT="${REPORT//\{\{TESTS_ERRORS\}\}/$TESTS_ERRORS}"
REPORT="${REPORT//\{\{TESTS_DURATION\}\}/$TESTS_DURATION}"
REPORT="${REPORT//\{\{TEST_STATUS\}\}/$TEST_STATUS}"
REPORT="${REPORT//\{\{FRONTEND_ERRORS\}\}/$FRONTEND_ERRORS}"
REPORT="${REPORT//\{\{FRONTEND_WARNINGS\}\}/$FRONTEND_WARNINGS}"
REPORT="${REPORT//\{\{FRONTEND_STATUS\}\}/$FRONTEND_STATUS}"
REPORT="${REPORT//\{\{BACKEND_ERRORS\}\}/$BACKEND_ERRORS}"
REPORT="${REPORT//\{\{BACKEND_WARNINGS\}\}/$BACKEND_WARNINGS}"
REPORT="${REPORT//\{\{BACKEND_FIXABLE\}\}/$BACKEND_FIXABLE}"
REPORT="${REPORT//\{\{BACKEND_STATUS\}\}/$BACKEND_STATUS}"
REPORT="${REPORT//\{\{FAILED_TESTS_LIST\}\}/$FAILED_TESTS_LIST}"
REPORT="${REPORT//\{\{ACTION_ITEMS\}\}/$ACTION_ITEMS}"
REPORT="${REPORT//\{\{RECOMMENDATIONS\}\}/$RECOMMENDATIONS}"

# Write report
echo "$REPORT" > "$REPORT_OUTPUT"

echo "Report generated: $REPORT_OUTPUT"
