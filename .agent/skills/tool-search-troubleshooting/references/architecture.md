# tool_search Architecture Reference

## Overview

`tool_search` is a deferred tool discovery mechanism in DeerFlow that allows the LLM to dynamically discover and use MCP tools at runtime, rather than loading all tool schemas into the context upfront.

## Problem Statement

When many MCP servers are configured, all MCP tool schemas would be loaded into the LLM's context via `bind_tools`. This consumes significant context tokens and can cause:
- Context window overflow
- Increased latency
- Higher costs

## Solution: Deferred Tool Loading

Instead of loading all tool schemas upfront, `tool_search` defers tool discovery:

1. **Initial state**: MCP tools are registered in `DeferredToolRegistry` but NOT exposed to LLM
2. **System prompt**: Lists only tool names in `<available-deferred-tools>` section
3. **Discovery**: LLM calls `tool_search(query="...")` to get tool schemas
4. **Promotion**: Matched tools are removed from registry and become callable
5. **Execution**: LLM can now call the promoted tools directly

## Key Components

### 1. DeferredToolRegistry

**File**: `backend/packages/harness/deerflow/tools/builtins/tool_search.py`

Stores deferred tools and handles search:

```python
class DeferredToolRegistry:
    def register(self, tool: BaseTool) -> None
    def promote(self, names: set[str]) -> None
    def search(self, query: str) -> list[BaseTool]
```

Search query formats:
- `select:name1,name2` - Exact name match
- `+keyword rest` - Name must contain keyword, rank by rest
- `keyword query` - Regex match against name + description

### 2. tool_search Tool

**File**: `backend/packages/harness/deerflow/tools/builtins/tool_search.py`

LangChain tool that LLM calls to discover deferred tools:

```python
@tool
def tool_search(query: str) -> str:
    """Fetches full schema definitions for deferred tools so they can be called."""
    registry = get_deferred_registry()
    matched_tools = registry.search(query)
    tool_defs = [convert_to_openai_function(t) for t in matched_tools]
    registry.promote({t.name for t in matched_tools})
    return json.dumps(tool_defs)
```

### 3. DeferredToolFilterMiddleware

**File**: `backend/packages/harness/deerflow/agents/middlewares/deferred_tool_filter_middleware.py`

Intercepts `bind_tools` calls and removes deferred tools:

```python
class DeferredToolFilterMiddleware(AgentMiddleware):
    def wrap_model_call(self, request, handler):
        return handler(self._filter_tools(request))

    def _filter_tools(self, request):
        registry = get_deferred_registry()
        deferred_names = {e.name for e in registry.entries}
        active_tools = [t for t in request.tools if t.name not in deferred_names]
        return request.override(tools=active_tools)
```

### 4. MCP Tools Loader

**File**: `backend/packages/harness/deerflow/mcp/tools.py`

Loads tools from MCP servers:

```python
async def get_mcp_tools() -> list[BaseTool]:
    extensions_config = ExtensionsConfig.from_file()
    servers_config = build_servers_config(extensions_config)
    client = MultiServerMCPClient(servers_config)
    tools = await client.get_tools()
    return tools
```

### 5. MCP Cache

**File**: `backend/packages/harness/deerflow/mcp/cache.py`

Caches MCP tools to avoid re-initialization:

```python
def get_cached_mcp_tools() -> list[BaseTool]:
    # Check if cache is stale based on config mtime
    # If stale, reinitialize MCP tools
    # Return cached tools
```

### 6. Tool Assembly

**File**: `backend/packages/harness/deerflow/tools/tools.py`

Assembles all tools including MCP:

```python
def get_available_tools() -> list[BaseTool]:
    # Load configured tools
    loaded_tools = [...]

    # Load MCP tools
    if include_mcp:
        mcp_tools = get_cached_mcp_tools()

        # When tool_search is enabled
        if config.tool_search.enabled:
            registry = DeferredToolRegistry()
            for t in mcp_tools:
                registry.register(t)
            set_deferred_registry(registry)
            builtin_tools.append(tool_search_tool)

    return loaded_tools + builtin_tools + mcp_tools + acp_tools
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  extensions_config.json                                      │
│  [{"server1": {...}, "server2": {...}]                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  get_cached_mcp_tools()                                      │
│  - Read config from disk                                     │
│  - Initialize MCP clients                                    │
│  - Load tools from all servers                               │
└────────────────────────────┬────────────────────────────────┘
                             │
               ┌─────────────┘
               │ tool_search.enabled?
               │
               ▼ Yes
┌─────────────────────────────────────────────────────────────┐
│  DeferredToolRegistry                                        │
│  - Register all MCP tools                                    │
│  - Add tool_search to builtin tools                          │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent Initialization                                        │
│  - System prompt includes <available-deferred-tools>         │
│  - DeferredToolFilterMiddleware added to chain               │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM Runtime                                                 │
│  1. LLM sees tool names in system prompt                     │
│  2. LLM calls tool_search(query="...")                       │
│  3. tool_search returns schemas, promotes tools              │
│  4. Next bind_tools includes promoted tools                  │
│  5. LLM calls promoted tools directly                        │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Enable tool_search

In `config.yaml`:

```yaml
tool_search:
  enabled: true
```

### Configure MCP Servers

In `extensions_config.json`:

```json
{
  "mcpServers": {
    "github": {
      "enabled": true,
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    },
    "weather": {
      "enabled": true,
      "type": "sse",
      "url": "http://example.com/mcp/sse"
    }
  }
}
```

## Concurrency Safety

The `DeferredToolRegistry` uses `contextvars.ContextVar` for per-request isolation:

```python
_registry_var: contextvars.ContextVar[DeferredToolRegistry | None] = \
    contextvars.ContextVar("deferred_tool_registry", default=None)
```

This prevents concurrent requests from interfering with each other's registry state.
