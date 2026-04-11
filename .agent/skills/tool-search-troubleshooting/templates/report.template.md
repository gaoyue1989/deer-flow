# tool_search Diagnostic Report

**Generated**: {{TIMESTAMP}}
**Working Directory**: {{WORKING_DIR}}
**Diagnostic Script**: `bash .agent/skills/tool-search-troubleshooting/scripts/diagnose_tool_search.sh`

---

## Executive Summary

**Overall Status**: {{PASS|FAIL|PARTIAL}}

**Brief Description**: {{One-sentence summary of the diagnostic result}}

---

## Configuration

| Setting | Value | Status |
|---------|-------|--------|
| tool_search.enabled | {{true\|false}} | {{✓\|✗}} |
| MCP servers configured | {{count}} | {{✓\|✗}} |
| MCP servers enabled | {{count}} | {{✓\|✗}} |
| langchain-mcp-adapters version | {{version}} | {{✓\|✗\|?}} |

---

## MCP Server Connectivity

| Server | Type | URL | Status | Details |
|--------|------|-----|--------|---------|
| {{server1}} | {{stdio\|sse\|http}} | {{url}} | {{✓\|✗\|?}} | {{details}} |
| {{server2}} | {{stdio\|sse\|http}} | {{url}} | {{✓\|✗\|?}} | {{details}} |

---

## Tool Loading Status

| Metric | Value | Expected | Status |
|--------|-------|----------|--------|
| MCP tools initialized | {{count}} | > 0 | {{✓\|✗}} |
| MCP tools in agent | {{count}} | 0 (when deferred) | {{✓\|✗}} |
| tool_search active | {{yes\|no}} | yes | {{✓\|✗}} |
| Deferred tools count | {{count}} | > 0 | {{✓\|✗}} |

---

## Issues Found

### Critical Issues

{{List each critical issue with:}}
- **Issue**: {{description}}
- **Evidence**: {{log snippet or error message}}
- **Impact**: {{what is affected}}
- **Root Cause**: {{identified cause}}
- **Recommendation**: {{how to fix}}

### Warnings

{{List each warning with:}}
- **Warning**: {{description}}
- **Evidence**: {{log snippet}}
- **Recommendation**: {{suggested action}}

---

## Root Cause Analysis

{{Detailed analysis of the root cause(s) identified:}}

1. **Primary Root Cause**: {{description}}
2. **Contributing Factors**: {{list any factors that made the issue worse}}
3. **Evidence**: {{log snippets, configuration snippets, etc.}}

---

## Recommendations

### Immediate Fixes

{{Actions to fix the issue immediately:}}

1. {{Step 1}}
   ```bash
   {{command}}
   ```

2. {{Step 2}}
   ```bash
   {{command}}
   ```

### Long-term Improvements

{{Suggestions for preventing similar issues:}}

1. {{Suggestion 1}}
2. {{Suggestion 2}}

---

## Verification Steps

After applying fixes, verify with:

```bash
# Restart the gateway
make stop && sleep 5 && make dev-daemon

# Run diagnostic script again
bash .agent/skills/tool-search-troubleshooting/scripts/diagnose_tool_search.sh

# Check gateway logs
tail -100 logs/gateway.log | grep -i "mcp\|tool_search\|deferred"

# Test tool_search via API
curl -X POST http://localhost:8001/api/threads/{{thread_id}}/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "input": {"messages": [{"role": "user", "content": "Use tool_search to find weather tools"}]},
    "config": {"configurable": {"model_name": "qwen3.5-plus"}}
  }'
```

---

## Appendix

### Log Snippets

{{Relevant log excerpts:}}

```
{{log content}}
```

### Configuration Files

{{Relevant configuration excerpts:}}

**config.yaml**:
```yaml
tool_search:
  enabled: {{true\|false}}
```

**extensions_config.json**:
```json
{
  "mcpServers": {
    {{server configurations}}
  }
}
```

### Diagnostic Script Output

{{Full output from diagnose_tool_search.sh if needed}}
