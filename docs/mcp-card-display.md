# MCP工具自定义HTML卡片展示 - 功能设计与验证文档

## 1. 功能概述

当Agent调用MCP工具时，如果工具名称在配置中有对应的显示配置，前端会激活自定义HTML卡片展示，使用Mustache模板引擎渲染MCP返回的参数，并通过事件委托支持卡片内交互功能。

### 1.1 核心特性

- **配置驱动**: 通过 `extensions_config.json` 配置工具显示模板
- **Mustache模板**: 使用 `{{variable}}` 语法渲染HTML
- **事件委托**: 通过 `data-action` 和 `data-params` 属性支持交互
- **降级处理**: 无配置时使用默认展示，模板错误时显示错误信息

---

## 2. 架构设计

### 2.1 数据流

```
用户输入 → Agent调用MCP工具 → MCP返回结果
                                      ↓
后端: _attach_display_config_to_tools() 附加元数据到工具metadata
                                      ↓
SSE事件流推送 tool 事件 (type: "tool", name: "weather_weather_api", content: "...")
                                      ↓
前端: useStream() 接收 → groupMessages() 分组 → convertToSteps() 转换
                                      ↓
ToolCall组件: getTemplate(name) 匹配模板 → MCPCard渲染
                                      ↓
Mustache.render(template, {args, result}) → dangerouslySetInnerHTML
                                      ↓
事件委托: onClick捕获 [data-action] → 触发回调
```

### 2.2 组件关系

```
MessageGroup
└── ChainOfThought
    └── ChainOfThoughtStep
        └── MCPCard (当工具名称匹配模板时)
            ├── Mustache渲染HTML
            └── 事件委托处理交互
```

---

## 3. 配置设计

### 3.1 配置文件结构

**文件**: `extensions_config.json`

```json
{
  "mcpServers": {
    "weather": {
      "enabled": true,
      "type": "sse",
      "url": "http://47.102.205.195:9001/mcp/sse",
      "description": "天气查询服务",
      "tools": {
        "weather_weather_api": {
          "card_title": "天气信息",
          "icon": "cloud-sun",
          "template_path": "/root/.openclaw/workspace/deer-flow/templates/weather/get_weather.html"
        }
      }
    }
  }
}
```

### 3.2 配置字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `card_title` | string | 否 | 卡片标题，默认使用工具名称 |
| `icon` | string | 否 | Lucide图标名称，默认"wrench" |
| `template_path` | string | 是 | HTML模板文件绝对路径 |

### 3.3 后端数据模型

**文件**: `backend/packages/harness/deerflow/config/extensions_config.py`

```python
class McpToolDisplayConfig(BaseModel):
    """Display configuration for a single MCP tool."""
    card_title: str = Field(default="", description="Title displayed on the card")
    icon: str = Field(default="wrench", description="Icon name from lucide-react")
    template_path: str = Field(default="", description="Path to the HTML template file")
    model_config = ConfigDict(extra="allow")

class McpServerConfig(BaseModel):
    """Configuration for a single MCP server."""
    # ... 其他字段 ...
    tools: dict[str, McpToolDisplayConfig] = Field(
        default_factory=dict,
        description="Map of tool name to display configuration",
    )
```

---

## 4. 模板设计

### 4.1 模板语法

使用 Mustache 模板引擎，支持以下语法：

| 语法 | 说明 | 示例 |
|------|------|------|
| `{{result.field}}` | 渲染结果字段 | `{{result.city}}` |
| `{{args.field}}` | 渲染参数字段 | `{{args.city}}` |
| `{{#field}}...{{/field}}` | 条件渲染（字段存在时） | `{{#result.forecast}}...{{/result.forecast}}` |

### 4.2 模板示例

**文件**: `templates/weather/get_weather.html`

```html
<div class="mcp-card mcp-card-weather">
  <div class="mcp-card-header">
    <span class="mcp-card-location">{{result.city}}{{#result.region}}, {{result.region}}{{/result.region}}</span>
    {{#result.condition}}<span class="mcp-card-condition">{{result.condition}}</span>{{/result.condition}}
  </div>
  <div class="mcp-card-body">
    <div class="mcp-card-temp">
      {{#result.temperature}}<span class="mcp-temp-value">{{result.temperature}}</span><span class="mcp-temp-unit">°C</span>{{/result.temperature}}
      {{#result.feels_like}}<span class="mcp-feels-like">体感 {{result.feels_like}}°C</span>{{/result.feels_like}}
    </div>
    {{#result.humidity}}<div class="mcp-detail">湿度: {{result.humidity}}%</div>{{/result.humidity}}
    {{#result.wind_speed}}<div class="mcp-detail">风速: {{result.wind_speed}} km/h</div>{{/result.wind_speed}}
  </div>
  <div class="mcp-card-footer">
    <button class="mcp-btn" data-action="refresh_weather" data-params='{"city": "{{args.city}}"}'>
      刷新天气
    </button>
    {{#result.forecast}}
    <button class="mcp-btn mcp-btn-secondary" data-action="view_forecast" data-params='{"city": "{{args.city}}"}'>
      查看预报
    </button>
    {{/result.forecast}}
  </div>
</div>
```

### 4.3 交互设计

通过 `data-action` 和 `data-params` 属性声明交互：

```html
<button data-action="refresh_weather" data-params='{"city": "{{args.city}}"}'>
  刷新天气
</button>
```

前端通过事件委托捕获点击：

```typescript
const handleContainerClick = (e: React.MouseEvent) => {
  const target = (e.target as HTMLElement).closest("[data-action]");
  if (!target) return;
  
  const action = target.getAttribute("data-action");
  const params = JSON.parse(target.getAttribute("data-params") || "{}");
  
  onAction({ action, params, toolName, serverName });
};
```

---

## 5. 前端组件设计

### 5.1 MCPCard 组件

**文件**: `frontend/src/components/workspace/messages/mcp-card.tsx`

```typescript
interface MCPCardProps {
  toolName: string;                    // 工具名称
  args: Record<string, unknown>;       // 调用参数
  result: string | Record<string, unknown> | undefined;  // 工具返回结果
  onAction?: (action: MCPCardAction) => void;            // 交互回调
}

export function MCPCard({ toolName, args, result, onAction }: MCPCardProps) {
  const { getTemplate, loadTemplateContent } = useMCPToolTemplates();
  const [templateContent, setTemplateContent] = useState<string | null>(null);
  
  // 1. 获取模板配置
  const template = getTemplate(toolName);
  
  // 2. 异步加载模板内容
  useEffect(() => {
    loadTemplateContent(template).then(setTemplateContent);
  }, [template]);
  
  // 3. Mustache渲染
  const view = { args, result: parseResult(result) };
  const renderedHtml = Mustache.render(templateContent, view);
  
  // 4. 渲染HTML + 事件委托
  return (
    <ChainOfThoughtStep label={template.card_title} icon={getIcon(template.icon)}>
      <div
        dangerouslySetInnerHTML={{ __html: renderedHtml }}
        onClick={handleContainerClick}
      />
    </ChainOfThoughtStep>
  );
}
```

### 5.2 useMCPToolTemplates Hook

**文件**: `frontend/src/core/mcp/hooks.ts`

```typescript
export function useMCPToolTemplates() {
  const { config } = useMCPConfig();
  
  // 从MCP配置中提取模板映射
  const templates = useMemo(() => {
    const result: Record<string, MCPToolTemplate> = {};
    for (const [serverName, serverConfig] of Object.entries(config.mcp_servers)) {
      if (serverConfig.tools) {
        for (const [toolName, toolConfig] of Object.entries(serverConfig.tools)) {
          result[toolName] = {
            card_title: toolConfig.card_title,
            icon: toolConfig.icon,
            template_path: toolConfig.template_path,
            server_name: serverName,
            tool_name: toolName,
          };
        }
      }
    }
    return result;
  }, [config]);
  
  // 获取模板配置
  const getTemplate = (toolName: string) => templates[toolName];
  
  // 加载模板内容（通过API）
  const loadTemplateContent = async (template: MCPToolTemplate): Promise<string> => {
    const response = await fetch(`/api/mcp/templates/${template.tool_name}`);
    const data = await response.json();
    return data.content;
  };
  
  return { templates, getTemplate, loadTemplateContent };
}
```

### 5.3 ToolCall 集成

**文件**: `frontend/src/components/workspace/messages/message-group.tsx`

```typescript
function ToolCall({ name, args, result, ... }) {
  const { getTemplate } = useMCPToolTemplates();
  
  // 已知工具特殊处理
  if (name === "web_search") { /* ... */ }
  else if (name === "bash") { /* ... */ }
  // MCP工具检查
  else {
    const mcpTemplate = getTemplate(name);
    if (mcpTemplate) {
      return <MCPCard toolName={name} args={args} result={result} />;
    }
    // 默认展示
    return <ChainOfThoughtStep label={name} icon={WrenchIcon} />;
  }
}
```

---

## 6. 后端API设计

### 6.1 MCP配置API

**端点**: `GET /api/mcp/config`

**响应**:
```json
{
  "mcp_servers": {
    "weather": {
      "enabled": true,
      "type": "sse",
      "url": "http://47.102.205.195:9001/mcp/sse",
      "description": "天气查询服务",
      "tools": {
        "weather_weather_api": {
          "card_title": "天气信息",
          "icon": "cloud-sun",
          "template_path": "/root/.../templates/weather/get_weather.html"
        }
      }
    }
  }
}
```

### 6.2 模板内容API

**端点**: `GET /api/mcp/templates/{tool_name}`

**响应**:
```json
{
  "content": "<div class=\"mcp-card\">...</div>"
}
```

**错误响应**:
```json
{
  "detail": "No template configured for tool: nonexistent"
}
```

### 6.3 工具元数据附加

**文件**: `backend/packages/harness/deerflow/mcp/tools.py`

```python
def _attach_display_config_to_tools(tools: list, extensions_config) -> None:
    """Attach display configuration to MCP tools metadata."""
    for server_name, server_config in extensions_config.mcp_servers.items():
        if not server_config.tools:
            continue
        for tool in tools:
            for mcp_tool_name, display_config in server_config.tools.items():
                if tool.name == mcp_tool_name or tool.name.endswith(f"__{mcp_tool_name}"):
                    display_info = {
                        "card_title": display_config.card_title,
                        "icon": display_config.icon,
                        "template_path": display_config.template_path,
                        "server_name": server_name,
                        "tool_name": mcp_tool_name,
                    }
                    if hasattr(tool, 'metadata') and isinstance(tool.metadata, dict):
                        tool.metadata["mcp_display"] = display_info
                    break
```

---

## 7. 样式设计

**文件**: `frontend/src/components/workspace/messages/mcp-card.css`

```css
.mcp-card {
  border-radius: 0.5rem;
  border: 1px solid var(--border);
  background-color: var(--card);
  padding: 0.75rem;
  font-size: 0.875rem;
}

.mcp-card-header {
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.5rem;
}

.mcp-card-location { font-weight: 500; }
.mcp-card-condition { color: var(--muted-foreground); font-size: 0.75rem; }

.mcp-temp-value { font-size: 1.5rem; font-weight: 600; }
.mcp-detail { color: var(--muted-foreground); font-size: 0.75rem; }

.mcp-btn {
  border-radius: 0.375rem;
  background-color: var(--primary);
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
  color: var(--primary-foreground);
  border: none;
  cursor: pointer;
}

.mcp-btn:hover { opacity: 0.9; }
.mcp-btn-secondary { background-color: var(--secondary); color: var(--secondary-foreground); }
```

---

## 8. 验证用例

### 8.1 后端配置验证

#### 用例 1.1: MCP配置API返回工具配置

| 项目 | 内容 |
|------|------|
| **端点** | `GET /api/mcp/config` |
| **预期** | 返回200，weather服务器包含tools配置 |
| **验证脚本** | ```bash curl -s http://localhost:8001/api/mcp/config \| python3 -c " import sys,json d=json.load(sys.stdin) weather = d['mcp_servers'].get('weather',{}) tools = weather.get('tools',{}) assert 'weather_weather_api' in tools, 'Tool not found' cfg = tools['weather_weather_api'] assert cfg['card_title'] == '天气信息' assert cfg['icon'] == 'cloud-sun' assert 'template_path' in cfg print('✓ 配置正确') " ``` |

#### 用例 1.2: 模板内容API返回HTML

| 项目 | 内容 |
|------|------|
| **端点** | `GET /api/mcp/templates/{tool_name}` |
| **预期** | 返回200，包含HTML模板内容 |
| **验证脚本** | ```bash curl -s http://localhost:8001/api/mcp/templates/weather_weather_api \| python3 -c " import sys,json d=json.load(sys.stdin) content = d.get('content','') assert len(content) > 0, 'Empty template' assert '{{result.city}}' in content, 'Missing mustache var' assert 'data-action' in content, 'Missing data-action' assert 'mcp-card' in content, 'Missing CSS class' print('✓ 模板正确') " ``` |

#### 用例 1.3: 不存在的工具返回404

| 项目 | 内容 |
|------|------|
| **端点** | `GET /api/mcp/templates/nonexistent_tool` |
| **预期** | 返回404，包含错误信息 |
| **验证脚本** | ```bash HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/mcp/templates/nonexistent_tool) [ "$HTTP_CODE" = "404" ] && echo "✓ 404正确" \|\| echo "✗ 预期404，实际$HTTP_CODE" ``` |

### 8.2 Mustache模板渲染验证

#### 用例 2.1: 完整数据渲染

| 项目 | 内容 |
|------|------|
| **输入** | 包含所有字段的模拟MCP结果 |
| **预期** | 正确渲染所有字段 |
| **验证脚本** | ```bash node << 'EOF' const Mustache = require('/root/.openclaw/workspace/deer-flow/frontend/node_modules/mustache'); const fs = require('fs'); const template = fs.readFileSync('/root/.openclaw/workspace/deer-flow/templates/weather/get_weather.html', 'utf8'); const view = { args: { city: "上海" }, result: { city: "上海", region: "浦东新区", condition: "多云", temperature: 26, feels_like: 28, humidity: 65, wind_speed: 15, forecast: true } }; const rendered = Mustache.render(template, view); const checks = [ ["城市", rendered.includes("上海")], ["区域", rendered.includes("浦东新区")], ["天气", rendered.includes("多云")], ["温度", rendered.includes("26")], ["体感", rendered.includes("28")], ["湿度", rendered.includes("65")], ["风速", rendered.includes("15")], ["刷新按钮", rendered.includes("刷新天气")], ["预报按钮", rendered.includes("查看预报")], ["data-action", rendered.includes("data-action")] ]; let allPass = true; checks.forEach(([name, pass]) => { console.log(`${pass ? '✓' : '✗'} ${name}`); if (!pass) allPass = false; }); process.exit(allPass ? 0 : 1); EOF ``` |

#### 用例 2.2: 部分字段缺失渲染

| 项目 | 内容 |
|------|------|
| **输入** | 只包含必要字段的MCP结果 |
| **预期** | 缺失字段不显示，不报错 |
| **验证脚本** | ```bash node << 'EOF' const Mustache = require('/root/.openclaw/workspace/deer-flow/frontend/node_modules/mustache'); const fs = require('fs'); const template = fs.readFileSync('/root/.openclaw/workspace/deer-flow/templates/weather/get_weather.html', 'utf8'); const view = { args: { city: "北京" }, result: { city: "北京", temperature: 22 } }; const rendered = Mustache.render(template, view); const checks = [ ["城市显示", rendered.includes("北京")], ["温度显示", rendered.includes("22")], ["无区域", !rendered.includes(", ")], ["无湿度", !rendered.includes("湿度")], ["无预报按钮", !rendered.includes("查看预报")] ]; let allPass = true; checks.forEach(([name, pass]) => { console.log(`${pass ? '✓' : '✗'} ${name}`); if (!pass) allPass = false; }); process.exit(allPass ? 0 : 1); EOF ``` |

### 8.3 前端组件验证

#### 用例 3.1: MCPCard组件导入

| 项目 | 内容 |
|------|------|
| **验证** | 组件文件存在且语法正确 |
| **检查** | ```bash # 文件存在 [ -f /root/.openclaw/workspace/deer-flow/frontend/src/components/workspace/messages/mcp-card.tsx ] && echo "✓ 文件存在" # TypeScript编译 cd /root/.openclaw/workspace/deer-flow/frontend && npx tsc --noEmit --skipLibCheck 2>&1 \| grep -q "error" && echo "✗ 编译错误" \|\| echo "✓ 编译通过" ``` |

#### 用例 3.2: ToolCall集成

| 项目 | 内容 |
|------|------|
| **验证** | message-group.tsx正确集成MCPCard |
| **检查** | ```bash grep -q "import { MCPCard }" /root/.openclaw/workspace/deer-flow/frontend/src/components/workspace/messages/message-group.tsx && echo "✓ MCPCard导入" grep -q "useMCPToolTemplates" /root/.openclaw/workspace/deer-flow/frontend/src/components/workspace/messages/message-group.tsx && echo "✓ Hook使用" grep -q "getTemplate(name)" /root/.openclaw/workspace/deer-flow/frontend/src/components/workspace/messages/message-group.tsx && echo "✓ 模板匹配逻辑" ``` |

#### 用例 3.3: useMCPToolTemplates Hook

| 项目 | 内容 |
|------|------|
| **验证** | Hook正确加载模板配置 |
| **检查** | ```bash grep -q "loadTemplateContent" /root/.openclaw/workspace/deer-flow/frontend/src/core/mcp/hooks.ts && echo "✓ 模板加载函数" grep -q "/api/mcp/templates/" /root/.openclaw/workspace/deer-flow/frontend/src/core/mcp/hooks.ts && echo "✓ API端点正确" ``` |

### 8.4 服务可用性验证

#### 用例 4.1: 服务端口状态

| 项目 | 内容 |
|------|------|
| **验证** | 所有服务正常运行 |
| **检查** | ```bash for port in 2024 8001 3000 2026; do if ss -tlnp \| grep -q ":$port "; then echo "✓ Port $port: UP" else echo "✗ Port $port: DOWN" fi done ``` |

#### 用例 4.2: Nginx反向代理

| 项目 | 内容 |
|------|------|
| **验证** | 通过2026端口访问正常 |
| **检查** | ```bash # 首页 curl -s -o /dev/null -w "%{http_code}" http://42.194.213.236:2026/ \| grep -q "200" && echo "✓ 首页正常" # API代理 curl -s http://42.194.213.236:2026/api/mcp/config \| python3 -c " import sys,json d=json.load(sys.stdin) assert 'mcp_servers' in d print('✓ API代理正常') " ``` |

### 8.5 端到端流程验证

#### 用例 5.1: 完整数据流

| 步骤 | 说明 |
|------|------|
| 1 | 用户发送天气查询请求 |
| 2 | Agent调用 `weather_weather_api` MCP工具 |
| 3 | MCP返回天气数据 |
| 4 | 前端通过SSE接收tool事件 |
| 5 | ToolCall组件检测工具名称匹配模板 |
| 6 | MCPCard加载并渲染HTML模板 |
| 7 | 显示天气卡片，包含交互按钮 |

#### 用例 5.2: 交互事件委托

| 项目 | 内容 |
|------|------|
| **验证** | 点击按钮触发正确事件 |
| **检查** | ```bash node << 'EOF' const rendered = `<div class="mcp-card"> <button data-action="refresh_weather" data-params='{"city": "上海"}'>刷新</button> <button data-action="view_forecast" data-params='{"city": "上海"}'>预报</button> </div>`; const parseAction = (html, selector) => { const match = html.match(new RegExp(`data-action="${selector}"[^>]*data-params='([^']+)'`)); return match ? JSON.parse(match[1]) : null; }; const refreshParams = parseAction(rendered, 'refresh_weather'); const forecastParams = parseAction(rendered, 'view_forecast'); console.log(refreshParams?.city === "上海" ? "✓ 刷新按钮参数正确" : "✗ 刷新按钮参数错误"); console.log(forecastParams?.city === "上海" ? "✓ 预报按钮参数正确" : "✗ 预报按钮参数错误"); EOF ``` |

### 8.6 边界情况验证

#### 用例 6.1: 模板文件不存在

| 项目 | 内容 |
|------|------|
| **操作** | 配置指向不存在的模板路径 |
| **预期** | MCPCard显示错误信息，不崩溃 |

#### 用例 6.2: MCP工具无配置

| 项目 | 内容 |
|------|------|
| **操作** | 调用未配置模板的MCP工具 |
| **预期** | 使用默认WrenchIcon展示 |

#### 用例 6.3: 模板渲染错误

| 项目 | 内容 |
|------|------|
| **操作** | 模板包含无效Mustache语法 |
| **预期** | 显示渲染错误信息 |

---

## 9. 验证结果汇总

| 用例 | 状态 | 备注 |
|------|------|------|
| 1.1 MCP配置API | ✅ | 返回正确配置 |
| 1.2 模板内容API | ✅ | 1215字符HTML |
| 1.3 404处理 | ✅ | 正确返回错误 |
| 2.1 完整渲染 | ✅ | 所有字段正确 |
| 2.2 部分渲染 | ✅ | 缺失字段隐藏 |
| 3.1 组件导入 | ✅ | 文件存在，编译通过 |
| 3.2 ToolCall集成 | ✅ | 正确集成 |
| 3.3 Hook验证 | ✅ | API端点正确 |
| 4.1 服务端口 | ✅ | 全部UP |
| 4.2 Nginx代理 | ✅ | 外部访问正常 |
| 5.1 端到端 | ⏳ | 需实际调用MCP |
| 5.2 事件委托 | ✅ | 参数解析正确 |

---

## 10. 修改文件清单

### 后端 (3个文件)

| 文件 | 变更 |
|------|------|
| `backend/packages/harness/deerflow/config/extensions_config.py` | 新增 `McpToolDisplayConfig` 模型，`McpServerConfig` 添加 `tools` 字段 |
| `backend/packages/harness/deerflow/mcp/tools.py` | 新增 `_attach_display_config_to_tools()` 函数，加载模板配置到工具metadata |
| `backend/app/gateway/routers/mcp.py` | 新增 `McpToolDisplayConfigResponse`，新增 `GET /api/mcp/templates/{tool_name}` 端点 |

### 前端 (6个文件)

| 文件 | 变更 |
|------|------|
| `frontend/src/core/mcp/types.ts` | 新增 `McpToolDisplayConfig`, `MCPToolTemplate` 接口 |
| `frontend/src/core/mcp/hooks.ts` | 新增 `useMCPToolTemplates()` hook |
| `frontend/src/core/mcp/index.ts` | 导出 hooks |
| `frontend/src/components/workspace/messages/mcp-card.tsx` | **新建** MCPCard 组件 (Mustache渲染 + 事件委托) |
| `frontend/src/components/workspace/messages/mcp-card.css` | **新建** MCP卡片样式 |
| `frontend/src/components/workspace/messages/message-group.tsx` | ToolCall 集成 MCPCard |

### 示例文件 (2个)

| 文件 | 说明 |
|------|------|
| `templates/weather/get_weather.html` | 天气卡片模板示例 |
| `extensions_config.json` | 更新含tools配置 |

---

## 11. 依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| `mustache` | 4.2.0 | 前端模板引擎 |
| `@types/mustache` | 4.2.6 | TypeScript类型定义 |

---

## 12. 注意事项

1. **模板路径**: `template_path` 必须使用**绝对路径**，因为Gateway进程工作目录在 `backend/`
2. **工具名称匹配**: 配置中的工具名称必须与MCP服务器返回的实际工具名称完全一致（如 `weather_weather_api`）
3. **CSS兼容性**: 项目使用 Tailwind CSS v4 + Turbopack，不支持 `@apply` 指令，需使用标准CSS属性
4. **安全考虑**: 使用 `dangerouslySetInnerHTML` 渲染HTML，模板内容应来自可信配置
