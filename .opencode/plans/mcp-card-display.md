# MCP工具自定义HTML卡片展示 - 实现计划

## 目标
当调用MCP工具时，如果工具名称有配置，激活响应配置展示卡片，使用HTML模板展示MCP返回参数。

## 技术方案
- 模板语法: Mustache (`{{variable}}`)
- 模板存储: 独立HTML文件
- 交互方式: HTML + 事件委托 (`data-action` + `data-params`)

## 配置格式示例
```json
{
  "mcpServers": {
    "weather": {
      "enabled": true,
      "type": "sse",
      "url": "http://example.com/mcp",
      "tools": {
        "get_weather": {
          "card_title": "天气信息",
          "icon": "cloud-sun",
          "template_path": "templates/weather/get_weather.html"
        }
      }
    }
  }
}
```

## 模板示例
```html
<div class="mcp-card weather-card">
  <h3>{{result.city}}</h3>
  <p>温度: {{result.temperature}}°C</p>
  <button data-action="view_detail" data-params='{"city": "{{args.city}}"}'>查看详情</button>
</div>
```

## 修改文件清单

### 后端
1. `backend/packages/harness/deerflow/config/extensions_config.py`
   - 新增 `McpToolDisplayConfig` 模型
   - 在 `McpServerConfig` 添加 `tools` 字段

2. `backend/packages/harness/deerflow/mcp/tools.py`
   - 加载模板配置并附加到工具元数据

3. `backend/app/gateway/routers/mcp.py`
   - MCP配置API返回tools配置给前端

### 前端
1. `frontend/src/core/mcp/types.ts` - 扩展类型定义
2. `frontend/src/core/mcp/hooks.ts` - 新增 `useMCPToolTemplates` hook
3. `frontend/src/components/workspace/messages/mcp-card.tsx` - **新建** MCPCard组件
4. `frontend/src/components/workspace/messages/message-group.tsx` - 集成MCPCard
5. 安装 `mustache` npm包

## 数据流
1. 前端加载时获取 /api/mcp/config (含tools模板配置)
2. 缓存模板配置到 React Context
3. Agent调用MCP工具 → SSE推送tool事件
4. ToolCall组件检测工具名称 → 匹配模板 → 渲染MCPCard
5. Mustache渲染HTML + 事件委托处理交互

---

## Verification Results (2026-04-12)

### Backend API Tests

| Test | Endpoint | Status | Details |
|------|----------|--------|---------|
| MCP Config | GET /api/mcp/config | ✅ 200 | 3 servers, weather has 1 tool |
| Template | GET /api/mcp/templates/get_weather | ✅ 200 | 1215 chars, Mustache + data-action |
| Not Found | GET /api/mcp/templates/nonexistent | ✅ 404 | Proper error message |

### Frontend Tests

| Test | URL | Status | Details |
|------|-----|--------|---------|
| Homepage | GET / | ✅ 200 | 123KB HTML, valid document |
| Compile | - | ✅ OK | Turbopack compiled in ~1s |

### Log Evidence

**Frontend:**
```
✓ Ready in 884ms
GET / 200 in 1091ms (compile: 520ms, render: 570ms)
```

**Gateway:**
```
INFO: 127.0.0.1 - "GET /api/mcp/config HTTP/1.1" 200 OK
INFO: 127.0.0.1 - "GET /api/mcp/templates/get_weather HTTP/1.1" 200 OK
```

### Configuration Note

`template_path` must use **absolute path** because Gateway runs from `backend/` directory:
```json
"template_path": "/root/.openclaw/workspace/deer-flow/templates/weather/get_weather.html"
```
