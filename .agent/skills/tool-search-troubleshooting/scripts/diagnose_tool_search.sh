#!/bin/bash
# diagnose_tool_search.sh - Automated diagnostic script for tool_search mechanism
# Usage: bash .agent/skills/tool-search-troubleshooting/scripts/diagnose_tool_search.sh

set -e

# Configuration
GATEWAY_URL="${GATEWAY_URL:-http://localhost:8001}"
CONFIG_FILE="${CONFIG_FILE:-config.yaml}"
EXTENSIONS_FILE="${EXTENSIONS_FILE:-extensions_config.json}"
LOG_FILE="${LOG_FILE:-logs/gateway.log}"
OUTPUT_DIR="${OUTPUT_DIR:-.agent/skills/tool-search-troubleshooting/output}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Output tracking
ISSUES=()
WARNINGS=()
INFO_ITEMS=()

# Helper functions
print_section() {
    echo ""
    echo "============================================================"
    echo " $1"
    echo "============================================================"
    echo ""
}

print_ok() {
    echo -e "${GREEN}✓${NC} $1"
    INFO_ITEMS+=("OK: $1")
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS+=("WARNING: $1")
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
    ISSUES+=("ERROR: $1")
}

# Create output directory
mkdir -p "$OUTPUT_DIR"

print_section "tool_search Diagnostic Script"
echo "Timestamp: $(date -Iseconds)"
echo "Working directory: $(pwd)"

# Phase 1: Check Configuration
print_section "Phase 1: Configuration Check"

# Check config.yaml
if [ -f "$CONFIG_FILE" ]; then
    print_ok "config.yaml exists"

    # Check tool_search.enabled
    if grep -q "tool_search:" "$CONFIG_FILE"; then
        TOOL_SEARCH_ENABLED=$(grep -A1 "tool_search:" "$CONFIG_FILE" | grep "enabled:" | awk '{print $2}')
        if [ "$TOOL_SEARCH_ENABLED" = "true" ]; then
            print_ok "tool_search.enabled = true"
        else
            print_warn "tool_search.enabled = $TOOL_SEARCH_ENABLED (should be true)"
        fi
    else
        print_warn "tool_search section not found in config.yaml"
    fi
else
    print_fail "config.yaml not found at $CONFIG_FILE"
fi

# Check extensions_config.json
if [ -f "$EXTENSIONS_FILE" ]; then
    print_ok "extensions_config.json exists"

    # Count MCP servers
    MCP_SERVER_COUNT=$(python3 -c "
import json
with open('$EXTENSIONS_FILE') as f:
    config = json.load(f)
servers = config.get('mcpServers', {})
print(len(servers))
" 2>/dev/null || echo "0")

    print_ok "MCP servers configured: $MCP_SERVER_COUNT"

    # List enabled servers
    ENABLED_SERVERS=$(python3 -c "
import json
with open('$EXTENSIONS_FILE') as f:
    config = json.load(f)
servers = config.get('mcpServers', {})
enabled = [name for name, cfg in servers.items() if cfg.get('enabled', False)]
print('\n'.join(enabled))
" 2>/dev/null)

    if [ -n "$ENABLED_SERVERS" ]; then
        print_ok "Enabled MCP servers:"
        echo "$ENABLED_SERVERS" | while read -r server; do
            echo "    - $server"
        done
    else
        print_warn "No enabled MCP servers found"
    fi
else
    print_fail "extensions_config.json not found at $EXTENSIONS_FILE"
fi

# Phase 2: Check MCP Server Connectivity
print_section "Phase 2: MCP Server Connectivity Check"

# Test each enabled server
python3 -c "
import json
import requests
import sys

with open('$EXTENSIONS_FILE') as f:
    config = json.load(f)

servers = config.get('mcpServers', {})

for name, cfg in servers.items():
    if not cfg.get('enabled', False):
        print(f'SKIP: {name} (disabled)')
        continue

    server_type = cfg.get('type', 'unknown')
    url = cfg.get('url', '')

    if server_type == 'stdio':
        print(f'CHECK: {name} (stdio type - command: {cfg.get(\"command\", \"N/A\")})')
        continue

    if not url:
        print(f'FAIL: {name} (no URL configured)')
        continue

    try:
        if url.startswith('https://'):
            resp = requests.get(url, timeout=10, verify=True)
        else:
            resp = requests.get(url, timeout=10)
        print(f'OK: {name} (HTTP {resp.status_code})')
    except requests.exceptions.ConnectionError as e:
        print(f'FAIL: {name} (ConnectionError: {str(e)[:100]})')
    except requests.exceptions.Timeout:
        print(f'FAIL: {name} (Timeout)')
    except Exception as e:
        print(f'FAIL: {name} ({type(e).__name__}: {str(e)[:100]})')
" 2>/dev/null || print_fail "Failed to check MCP server connectivity"

# Phase 3: Analyze Tool Loading Logs
print_section "Phase 3: Tool Loading Log Analysis"

if [ -f "$LOG_FILE" ]; then
    print_ok "Gateway log exists"

    # Check MCP tools initialization
    MCP_INIT=$(tail -500 "$LOG_FILE" | grep "MCP tools initialized" | tail -1)
    if [ -n "$MCP_INIT" ]; then
        echo "MCP init: $MCP_INIT"

        # Extract tool count
        TOOL_COUNT=$(echo "$MCP_INIT" | grep -oP '\d+(?= tool\(s\))' || echo "0")
        if [ "$TOOL_COUNT" -gt 0 ] 2>/dev/null; then
            print_ok "MCP tools loaded: $TOOL_COUNT"
        else
            print_fail "MCP tools loaded: 0"
        fi
    else
        print_warn "No MCP initialization log found"
    fi

    # Check total tools loaded
    TOOLS_LOADED=$(tail -500 "$LOG_FILE" | grep "Total tools loaded" | tail -1)
    if [ -n "$TOOLS_LOADED" ]; then
        echo "Tools loaded: $TOOLS_LOADED"

        # Extract MCP tools count
        MCP_TOOLS=$(echo "$TOOLS_LOADED" | grep -oP 'MCP tools: \K\d+' || echo "0")
        if [ "$MCP_TOOLS" -gt 0 ] 2>/dev/null; then
            print_ok "MCP tools in agent: $MCP_TOOLS"
        else
            print_fail "MCP tools in agent: 0"
        fi
    fi

    # Check tool_search active
    TOOL_SEARCH_ACTIVE=$(tail -500 "$LOG_FILE" | grep "Tool search active" | tail -1)
    if [ -n "$TOOL_SEARCH_ACTIVE" ]; then
        print_ok "tool_search is active"
        echo "  $TOOL_SEARCH_ACTIVE"
    else
        print_warn "No 'Tool search active' log found"
    fi

    # Check for errors
    echo ""
    echo "Error patterns in logs:"

    if tail -500 "$LOG_FILE" | grep -q "UnboundLocalError"; then
        print_fail "Found UnboundLocalError (langchain-mcp-adapters bug)"
        tail -500 "$LOG_FILE" | grep "UnboundLocalError" | tail -1 | sed 's/^/  /'
    fi

    if tail -500 "$LOG_FILE" | grep -q "ConnectError\|Connection refused"; then
        print_fail "Found connection errors"
        tail -500 "$LOG_FILE" | grep "ConnectError\|Connection refused" | tail -2 | sed 's/^/  /'
    fi

    if tail -500 "$LOG_FILE" | grep -q "Failed to load MCP tools"; then
        print_fail "Found 'Failed to load MCP tools' error"
        tail -500 "$LOG_FILE" | grep "Failed to load MCP tools" | tail -1 | sed 's/^/  /'
    fi

else
    print_fail "Gateway log not found at $LOG_FILE"
fi

# Phase 4: Check langchain-mcp-adapters Version
print_section "Phase 4: Library Version Check"

MCP_ADAPTERS_VERSION=$(find .venv -name "langchain_mcp_adapters-*.dist-info" -type d 2>/dev/null | head -1 | grep -oP 'langchain_mcp_adapters-\K[^-]+' || echo "not found")

if [ -n "$MCP_ADAPTERS_VERSION" ] && [ "$MCP_ADAPTERS_VERSION" != "not found" ]; then
    print_ok "langchain-mcp-adapters version: $MCP_ADAPTERS_VERSION"
else
    print_warn "langchain-mcp-adapters version not found"
fi

# Phase 5: Summary
print_section "Diagnostic Summary"

echo "Issues found: ${#ISSUES[@]}"
for issue in "${ISSUES[@]}"; do
    echo "  - $issue"
done

echo ""
echo "Warnings: ${#WARNINGS[@]}"
for warning in "${WARNINGS[@]}"; do
    echo "  - $warning"
done

echo ""
echo "Info: ${#INFO_ITEMS[@]}"

# Generate report
print_section "Generating Report"

REPORT_FILE="$OUTPUT_DIR/diagnostic_report_$(date +%Y%m%d_%H%M%S).md"

cat > "$REPORT_FILE" << EOF
# tool_search Diagnostic Report

**Generated**: $(date -Iseconds)
**Working Directory**: $(pwd)

## Configuration

- tool_search.enabled: ${TOOL_SEARCH_ENABLED:-unknown}
- MCP servers configured: ${MCP_SERVER_COUNT:-0}
- langchain-mcp-adapters version: ${MCP_ADAPTERS_VERSION:-unknown}

## MCP Server Connectivity

\`\`\`
$(python3 -c "
import json
import requests

with open('$EXTENSIONS_FILE') as f:
    config = json.load(f)

servers = config.get('mcpServers', {})

for name, cfg in servers.items():
    if not cfg.get('enabled', False):
        print(f'- {name}: disabled')
        continue

    server_type = cfg.get('type', 'unknown')
    url = cfg.get('url', '')

    if server_type == 'stdio':
        print(f'- {name}: stdio (command: {cfg.get(\"command\", \"N/A\")})')
        continue

    if not url:
        print(f'- {name}: no URL')
        continue

    try:
        if url.startswith('https://'):
            resp = requests.get(url, timeout=10, verify=True)
        else:
            resp = requests.get(url, timeout=10)
        print(f'- {name}: OK (HTTP {resp.status_code})')
    except Exception as e:
        print(f'- {name}: FAIL ({type(e).__name__})')
" 2>/dev/null || echo "Failed to check connectivity")
\`\`\`

## Tool Loading Status

- MCP tools initialized: ${TOOL_COUNT:-0}
- MCP tools in agent: ${MCP_TOOLS:-0}
- tool_search active: $([ -n "$TOOL_SEARCH_ACTIVE" ] && echo "yes" || echo "no")

## Issues Found

$(if [ ${#ISSUES[@]} -gt 0 ]; then
    for issue in "${ISSUES[@]}"; do
        echo "- $issue"
    done
else
    echo "No critical issues found"
fi)

## Warnings

$(if [ ${#WARNINGS[@]} -gt 0 ]; then
    for warning in "${WARNINGS[@]}"; do
        echo "- $warning"
    done
else
    echo "No warnings"
fi)

## Recommendations

$(if echo "${ISSUES[*]}" | grep -q "UnboundLocalError"; then
    echo "1. Upgrade langchain-mcp-adapters: pip install --upgrade langchain-mcp-adapters"
    echo "2. Check for known issues in the library's GitHub repository"
fi)

$(if echo "${ISSUES[*]}" | grep -q "ConnectError\|Connection refused"; then
    echo "1. Verify MCP servers are running and accessible"
    echo "2. Check network connectivity and firewall rules"
    echo "3. Verify server URLs in extensions_config.json"
    echo "4. Consider disabling unreachable servers (set enabled: false)"
fi)

$(if [ "${MCP_TOOLS:-0}" -eq 0 ] 2>/dev/null; then
    echo "1. Fix MCP server connectivity issues first"
    echo "2. Restart the gateway service after fixing connectivity"
    echo "3. Check gateway logs for detailed error messages"
fi)

$(if [ "${#ISSUES[@]}" -eq 0 ] && [ "${#WARNINGS[@]}" -eq 0 ]; then
    echo "No issues found. tool_search mechanism should be working correctly."
    echo "If problems persist, check the LLM's behavior and system prompt."
fi)
EOF

print_ok "Report generated: $REPORT_FILE"

echo ""
echo "Diagnostic complete."
