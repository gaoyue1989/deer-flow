---
name: tool-search-troubleshooting
description: Diagnose and troubleshoot why tool_search and MCP tools are not working in DeerFlow. Guides through: 1) Checking MCP server configuration, 2) Verifying server connectivity, 3) Analyzing tool loading logs, 4) Identifying root causes, 5) Providing fix recommendations. Use when the user says "tool_search not working", "MCP tools not loading", "deferred tools not available", "why can't I use MCP tools", or similar.
---

# DeerFlow tool_search Troubleshooting Skill

This skill guides the Agent through diagnosing why the `tool_search` mechanism and MCP tools are not working in DeerFlow.

## Structure

```
tool-search-troubleshooting/
├── SKILL.md                          ← You are here - core workflow and logic
├── scripts/
│   └── diagnose_tool_search.sh       ← Automated diagnostic script
├── references/
│   ├── architecture.md               ← tool_search mechanism architecture
│   ├── common_issues.md              ← Common issues and solutions
│   └── log_patterns.md               ← Key log patterns to look for
└── templates/
    └── report.template.md            ← Diagnostic report template
```

## Standard Operating Procedure (SOP)

### Phase 1: Check Configuration

1. **Check `config.yaml`** - Verify `tool_search.enabled` is `true`
2. **Check `extensions_config.json`** - Verify MCP server configurations
3. **Count enabled MCP servers** - Note how many servers have `enabled: true`

### Phase 2: Check MCP Server Connectivity

For each enabled MCP server:

1. **stdio type** - Check if the command exists (e.g., `npx` for npm-based servers)
2. **sse/http type** - Test HTTP connectivity to the server URL
3. **streamablehttp type** - Test HTTPS connectivity with any configured headers
4. **Record connectivity results** - Note which servers are reachable

### Phase 3: Analyze Tool Loading Logs

1. **Read gateway logs** - Check `logs/gateway.log` for MCP-related entries
2. **Look for key patterns**:
   - `MCP tools initialized: X tool(s) loaded` - Should show non-zero count
   - `Total tools loaded: X, built-in tools: Y, MCP tools: Z` - Z should be > 0
   - `Tool search active: X tools deferred` - Should appear when tool_search is enabled
   - `Failed to load MCP tools` - Indicates loading failure
3. **Identify errors**:
   - `UnboundLocalError` - Bug in langchain-mcp-adapters library
   - `ConnectError` / `Connection refused` - Server unreachable
   - `httpx.ConnectError` - Network connectivity issue

### Phase 4: Identify Root Cause

Based on findings, determine the root cause:

| Symptom | Root Cause |
|---------|------------|
| MCP tools: 0, ConnectError in logs | MCP server unreachable |
| MCP tools: 0, UnboundLocalError | langchain-mcp-adapters bug |
| MCP tools: 0, no errors | MCP initialization not triggered |
| tool_search returns "No deferred tools" | DeferredToolRegistry is empty |
| LLM doesn't call tool_search | Missing instructions in system prompt |

### Phase 5: Generate Report

1. **Collect all findings** - Configuration, connectivity, logs, root cause
2. **Generate diagnostic report** - Use `templates/report.template.md`
3. **Provide fix recommendations** - Based on identified root cause

## Execution Rules

- **Run diagnostic script first** - Execute `scripts/diagnose_tool_search.sh` to gather data
- **Follow the sequence** - Execute phases in order
- **Error handling** - If a step fails, record the issue and continue
- **Detailed logging** - Record findings for each phase
- **Template requirement** - The final report must use the template; do not output a free-form summary

## Architecture Reference

### tool_search Mechanism

The `tool_search` mechanism is a deferred tool discovery system:

1. **Initial state**: MCP tools are registered in `DeferredToolRegistry`, not exposed to LLM via `bind_tools`
2. **System prompt**: Lists deferred tool names in `<available-deferred-tools>` section
3. **LLM discovery**: LLM calls `tool_search(query="select:tool_name")` to get tool schemas
4. **Promotion**: Matched tools are removed from registry and become callable via `bind_tools`
5. **Middleware**: `DeferredToolFilterMiddleware` filters deferred tools from model binding

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| DeferredToolRegistry | `deerflow/tools/builtins/tool_search.py` | Stores deferred tools |
| tool_search tool | `deerflow/tools/builtins/tool_search.py` | LLM calls this to discover tools |
| DeferredToolFilterMiddleware | `deerflow/agents/middlewares/deferred_tool_filter_middleware.py` | Filters deferred tools from bind_tools |
| MCP tools loader | `deerflow/mcp/tools.py` | Loads tools from MCP servers |
| MCP cache | `deerflow/mcp/cache.py` | Caches MCP tools |
| Tool assembly | `deerflow/tools/tools.py` | Assembles all tools including MCP |

### Tool Loading Flow

```
get_available_tools()
├── loaded_tools (from config.yaml tool_groups)
├── builtin_tools (present_file, ask_clarification, etc.)
├── mcp_tools (from MCP servers) ← tool_search registers these in DeferredToolRegistry
└── acp_tools (ACP agent tools)
```

When `tool_search.enabled: true`:
- MCP tools are NOT added directly to the tool list
- Instead, they are registered in `DeferredToolRegistry`
- `tool_search` tool is added to `builtin_tools`
- LLM discovers tools at runtime via `tool_search`

## Common Issues and Solutions

### Issue 1: MCP Server Connection Failure

**Symptom**: `ConnectError` or `Connection refused` in logs

**Solutions**:
1. Verify the MCP server is running and accessible
2. Check network connectivity: `curl -v <server_url>`
3. Verify firewall rules allow the connection
4. Check if the URL is correct in `extensions_config.json`
5. If the server is down, disable it: set `enabled: false`

### Issue 2: langchain-mcp-adapters Bug

**Symptom**: `UnboundLocalError: cannot access local variable 'tools'`

**Solutions**:
1. Check library version: `pip show langchain-mcp-adapters`
2. Upgrade to latest version: `pip install --upgrade langchain-mcp-adapters`
3. If upgrade doesn't help, check for known issues in the library's GitHub

### Issue 3: tool_search Returns "No deferred tools available"

**Symptom**: LLM calls `tool_search` but gets empty result

**Solutions**:
1. Verify MCP tools are loading successfully (check logs for non-zero count)
2. Check that `tool_search.enabled: true` in `config.yaml`
3. Verify MCP servers are configured and enabled in `extensions_config.json`
4. Check that at least one MCP server is reachable

### Issue 4: LLM Doesn't Call tool_search

**Symptom**: LLM tries to call MCP tools directly without using tool_search

**Solutions**:
1. Check that `<available-deferred-tools>` section appears in system prompt
2. Verify the prompt includes instructions to use `tool_search`
3. Check that `tool_search` tool is in the available tools list
4. Consider enhancing the system prompt with clearer instructions

### Issue 5: MCP Tools Load But tool_search Doesn't Work

**Symptom**: MCP tools load successfully but LLM can't discover them via tool_search

**Solutions**:
1. Check that `DeferredToolRegistry` is populated (look for "Tool search active" in logs)
2. Verify `set_deferred_registry()` is called after loading MCP tools
3. Check that `DeferredToolFilterMiddleware` is added to the middleware chain
4. Verify the middleware is filtering tools correctly

## Key Tools

Use the following tools during execution:

1. **bash** - Run shell commands and diagnostic script
2. **read** - Read configuration files and logs
3. **grep** - Search for specific patterns in logs
4. **present_file** - Show generated diagnostic report

## Success Criteria

Diagnostic complete when:
- [x] Configuration check completed
- [x] MCP server connectivity verified
- [x] Tool loading logs analyzed
- [x] Root cause identified
- [x] Diagnostic report generated
- [x] Fix recommendations provided

## Read Reference Files

Before starting execution, read the following reference files:
1. `references/architecture.md` - tool_search mechanism details
2. `references/common_issues.md` - Common issues and solutions
3. `references/log_patterns.md` - Key log patterns to identify
4. `templates/report.template.md` - Diagnostic report template
