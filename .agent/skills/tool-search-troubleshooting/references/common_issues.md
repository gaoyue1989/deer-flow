# Common Issues and Solutions

## Issue 1: MCP Server Connection Failure

### Symptoms
- Log: `ConnectError: All connection attempts failed`
- Log: `Connection refused`
- MCP tools loaded: 0

### Root Cause
The MCP server is unreachable due to:
- Server not running
- Wrong URL configuration
- Network/firewall blocking
- DNS resolution failure

### Solutions

1. **Verify server is running**
   ```bash
   curl -v <server_url>
   ```

2. **Check configuration**
   ```bash
   cat extensions_config.json | python3 -m json.tool
   ```
   Verify the URL is correct and matches the server.

3. **Test connectivity**
   ```bash
   # For HTTP servers
   curl -v http://<host>:<port>/mcp/sse

   # For HTTPS servers
   curl -v https://<host>/mcp
   ```

4. **Disable unreachable server**
   If the server is down and cannot be fixed immediately:
   ```json
   {
     "mcpServers": {
       "weather": {
         "enabled": false,
         ...
       }
     }
   }
   ```

5. **Check firewall rules**
   ```bash
   # Check if port is open
   nc -zv <host> <port>

   # Check firewall status
   sudo ufw status
   ```

---

## Issue 2: langchain-mcp-adapters UnboundLocalError

### Symptoms
- Log: `UnboundLocalError: cannot access local variable 'tools' where it is not associated with a value`
- Stack trace points to `langchain_mcp_adapters/tools.py`

### Root Cause
Bug in `langchain-mcp-adapters` library when handling exceptions during tool loading. The `tools` variable is referenced before assignment in error handling code.

### Solutions

1. **Upgrade the library**
   ```bash
   cd backend
   uv pip install --upgrade langchain-mcp-adapters
   ```

2. **Check for known issues**
   Visit the library's GitHub repository and check for:
   - Open issues with similar errors
   - Recent releases that fix this bug
   - Workarounds suggested by maintainers

3. **Workaround: Fix unreachable servers first**
   The bug is triggered when a server connection fails. Fixing connectivity issues (Issue 1) may work around this bug.

4. **Patch the library (temporary)**
   If upgrade is not possible, patch the library:
   ```bash
   # Find the library location
   find .venv -name "tools.py" -path "*/langchain_mcp_adapters/*"

   # Edit the file to initialize tools = [] before the try block
   ```

---

## Issue 3: tool_search Returns "No deferred tools available"

### Symptoms
- LLM calls `tool_search` and gets: `"No deferred tools available."`
- Log: No "Tool search active" message

### Root Cause
The `DeferredToolRegistry` is empty because:
- MCP tools failed to load
- `tool_search.enabled` is false
- MCP tools loading was skipped

### Solutions

1. **Check tool_search configuration**
   ```bash
   grep -A1 "tool_search:" config.yaml
   ```
   Should show `enabled: true`

2. **Check MCP tools loading**
   ```bash
   tail -100 logs/gateway.log | grep -i "mcp\|tool"
   ```
   Look for:
   - `MCP tools initialized: X tool(s) loaded` (X should be > 0)
   - `Tool search active: X tools deferred`

3. **Verify MCP servers are enabled**
   ```bash
   cat extensions_config.json | python3 -c "
   import json, sys
   config = json.load(sys.stdin)
   servers = config.get('mcpServers', {})
   enabled = [n for n, c in servers.items() if c.get('enabled')]
   print('Enabled servers:', enabled)
   "
   ```

4. **Restart the gateway**
   After fixing configuration:
   ```bash
   make stop && sleep 5 && make dev-daemon
   ```

---

## Issue 4: LLM Doesn't Call tool_search

### Symptoms
- LLM tries to call MCP tools directly
- LLM says "I don't have access to that tool"
- No `tool_search` calls in logs

### Root Cause
The LLM doesn't understand it needs to use `tool_search` first because:
- `<available-deferred-tools>` section is missing from system prompt
- No instructions on how to use `tool_search`
- `tool_search` tool is not in the available tools list

### Solutions

1. **Check system prompt**
   Look for `<available-deferred-tools>` in the system prompt:
   ```bash
   # Enable debug logging to see the system prompt
   ```

2. **Verify tool_search is in tools list**
   Check logs for:
   - `Total tools loaded: X, built-in tools: Y, MCP tools: 0, ACP tools: 0`
   - built-in tools should include `tool_search`

3. **Enhance system prompt (if needed)**
   The `<available-deferred-tools>` section should include instructions:
   ```
   <available-deferred-tools>
   These tools are available but not loaded. Use tool_search to load them.
   Example: tool_search(query="select:tool_name") or tool_search(query="keyword")

   Available tools:
   - tool1
   - tool2
   </available-deferred-tools>
   ```

4. **Check DeferredToolFilterMiddleware**
   Verify the middleware is added:
   ```bash
   grep -r "DeferredToolFilterMiddleware" backend/packages/harness/deerflow/agents/
   ```

---

## Issue 5: MCP Tools Load But tool_search Doesn't Work

### Symptoms
- Log: `MCP tools initialized: X tool(s) loaded` (X > 0)
- But `tool_search` returns empty results
- LLM cannot discover tools

### Root Cause
The `DeferredToolRegistry` is not being populated even though MCP tools load successfully.

### Solutions

1. **Check tool assembly logic**
   In `deerflow/tools/tools.py`, verify:
   ```python
   if config.tool_search.enabled:
       registry = DeferredToolRegistry()
       for t in mcp_tools:
           registry.register(t)
       set_deferred_registry(registry)
   ```

2. **Check registry state**
   Add debug logging to verify the registry is populated:
   ```python
   logger.info(f"DeferredToolRegistry has {len(registry)} tools")
   ```

3. **Verify ContextVar isolation**
   The registry uses `contextvars.ContextVar`. If the registry is set in one context but accessed in another, it will appear empty.

4. **Check middleware chain**
   Verify `DeferredToolFilterMiddleware` is in the middleware list:
   ```python
   if app_config.tool_search.enabled:
       middlewares.append(DeferredToolFilterMiddleware())
   ```

---

## Issue 6: Promoted Tools Not Callable

### Symptoms
- `tool_search` returns tool schemas
- But LLM still cannot call the tool
- Log: Tool not found in available tools

### Root Cause
After promotion, the tool should be callable in the next `bind_tools` call, but something prevents this.

### Solutions

1. **Check promote logic**
   Verify `registry.promote()` is called after `tool_search`:
   ```python
   registry.promote({t.name for t in matched_tools})
   ```

2. **Verify middleware filtering**
   The `DeferredToolFilterMiddleware` should stop filtering promoted tools:
   ```python
   deferred_names = {e.name for e in registry.entries}
   # Promoted tools are no longer in registry.entries
   # So they pass through the filter
   ```

3. **Check agent loop**
   The agent must re-enter the model node after `tool_search` returns. Verify the agent loop is working correctly.

---

## Diagnostic Checklist

Use this checklist when troubleshooting:

- [ ] `config.yaml` has `tool_search.enabled: true`
- [ ] `extensions_config.json` has enabled MCP servers
- [ ] MCP servers are reachable (test with curl)
- [ ] Gateway logs show `MCP tools initialized: X tool(s) loaded` (X > 0)
- [ ] Gateway logs show `Tool search active: X tools deferred`
- [ ] Gateway logs show `Total tools loaded: X, built-in tools: Y, MCP tools: 0`
- [ ] No `UnboundLocalError` in logs
- [ ] No `ConnectError` in logs
- [ ] `<available-deferred-tools>` appears in system prompt
- [ ] `tool_search` tool is in available tools list
- [ ] `DeferredToolFilterMiddleware` is in middleware chain
