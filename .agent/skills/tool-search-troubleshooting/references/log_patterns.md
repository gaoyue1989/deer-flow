# Key Log Patterns for tool_search Troubleshooting

## Successful tool_search Flow

### Expected Log Sequence

```
# Phase 1: MCP tools initialization
deerflow.mcp.cache - INFO - MCP tools initialized: 5 tool(s) loaded (config mtime: 1775910673.195122)

# Phase 2: Agent creation with tool_search
deerflow.tools.tools - INFO - Tool search active: 5 tools deferred
deerflow.tools.tools - INFO - Total tools loaded: 8, built-in tools: 3, MCP tools: 0, ACP tools: 0

# Phase 3: LLM calls tool_search
deerflow.tools.builtins.tool_search - DEBUG - Promoted 2 tool(s) from deferred to active: {'weather_query', 'weather_forecast'}

# Phase 4: LLM calls promoted tool
# (No specific log, tool executes normally)
```

## Key Log Patterns

### MCP Tools Loading

| Pattern | Meaning | Expected Value |
|---------|---------|----------------|
| `MCP tools initialized: X tool(s) loaded` | MCP tools loaded from servers | X > 0 |
| `Total tools loaded: X, built-in tools: Y, MCP tools: Z` | Tool assembly result | Z = 0 (when tool_search enabled) |
| `Tool search active: X tools deferred` | Deferred registry populated | X > 0 |
| `No enabled MCP servers configured` | No MCP servers enabled | Should not appear if configured |
| `Failed to load MCP tools: ...` | MCP loading failed | Should not appear |

### tool_search Operation

| Pattern | Meaning | Expected Value |
|---------|---------|----------------|
| `Tool search active: X tools deferred` | Registry populated | X > 0 |
| `Promoted X tool(s) from deferred to active` | Tools discovered | X > 0 after tool_search call |
| `No deferred tools available` | Registry empty | Should not appear if MCP tools loaded |

### Error Patterns

| Pattern | Severity | Root Cause |
|---------|----------|------------|
| `UnboundLocalError: cannot access local variable 'tools'` | Critical | langchain-mcp-adapters bug |
| `ConnectError: All connection attempts failed` | Critical | MCP server unreachable |
| `Connection refused` | Critical | Server not running or port blocked |
| `httpx.ConnectError` | Critical | Network connectivity issue |
| `Failed to load MCP tools` | Critical | MCP loading failed |
| `langchain-mcp-adapters not installed` | Warning | Missing dependency |

## Log Analysis Commands

### Check MCP Tools Status

```bash
# Check MCP initialization
tail -500 logs/gateway.log | grep "MCP tools initialized"

# Check tool assembly
tail -500 logs/gateway.log | grep "Total tools loaded"

# Check tool_search activation
tail -500 logs/gateway.log | grep "Tool search active"
```

### Check for Errors

```bash
# Check for UnboundLocalError
tail -500 logs/gateway.log | grep "UnboundLocalError"

# Check for connection errors
tail -500 logs/gateway.log | grep "ConnectError\|Connection refused"

# Check for MCP loading failures
tail -500 logs/gateway.log | grep "Failed to load MCP tools"
```

### Check tool_search Operation

```bash
# Check tool_search calls
tail -500 logs/gateway.log | grep "tool_search\|Tool search"

# Check tool promotion
tail -500 logs/gateway.log | grep "Promoted.*from deferred"
```

### Full MCP-Related Log Search

```bash
# Search all MCP-related logs
tail -1000 logs/gateway.log | grep -i "mcp\|deferred\|tool_search"
```

## Log Levels

| Level | When to Use |
|-------|-------------|
| INFO | Normal operation (tool loading, agent creation) |
| DEBUG | Detailed operation (tool promotion, filtering) |
| WARNING | Non-critical issues (missing optional dependency) |
| ERROR | Critical failures (MCP loading failed) |

## Example: Successful Diagnostic

```bash
$ tail -500 logs/gateway.log | grep -i "mcp\|deferred\|tool_search"

2026-04-11 21:01:34 - deerflow.mcp.cache - INFO - MCP tools initialized: 5 tool(s) loaded (config mtime: 1775910673.195122)
2026-04-11 21:01:34 - deerflow.tools.tools - INFO - Tool search active: 5 tools deferred
2026-04-11 21:01:34 - deerflow.tools.tools - INFO - Total tools loaded: 8, built-in tools: 3, MCP tools: 0, ACP tools: 0
2026-04-11 21:02:08 - deerflow.agents.lead_agent.agent - INFO - Create Agent(default) -> ...
2026-04-11 21:02:08 - deerflow.tools.tools - INFO - Total tools loaded: 8, built-in tools: 3, MCP tools: 0, ACP tools: 0
```

Analysis:
- ✓ MCP tools loaded: 5
- ✓ tool_search active: 5 tools deferred
- ✓ MCP tools in agent: 0 (correct, they're deferred)
- ✓ No errors

## Example: Failed Diagnostic

```bash
$ tail -500 logs/gateway.log | grep -i "mcp\|deferred\|tool_search"

2026-04-11 21:01:34 - deerflow.mcp.tools - ERROR - Failed to load MCP tools: unhandled errors in a TaskGroup (1 sub-exception)
2026-04-11 21:01:34 - deerflow.mcp.cache - INFO - MCP tools initialized: 0 tool(s) loaded (config mtime: 1775910673.195122)
2026-04-11 21:01:34 - deerflow.tools.tools - INFO - Total tools loaded: 8, built-in tools: 3, MCP tools: 0, ACP tools: 0
```

Analysis:
- ✗ MCP tools loaded: 0
- ✗ No "Tool search active" message
- ✗ Error: "Failed to load MCP tools"
- Root cause: Check for ConnectError or UnboundLocalError
