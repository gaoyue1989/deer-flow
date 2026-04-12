# MCP工具自定义HTML卡片配置指南

## 1. 概述

本文档详细介绍如何为MCP工具配置自定义HTML卡片展示。通过配置，当Agent调用MCP工具后，前端会以美观的卡片形式展示工具返回的数据，而不是简单的文本。

### 1.1 功能特性

- **配置驱动**: 通过 `extensions_config.json` 配置工具显示模板
- **Mustache模板**: 使用 `{{variable}}` 语法渲染HTML
- **数据解析**: 支持自定义数据解析函数处理嵌套API响应
- **事件委托**: 通过 `data-action` 和 `data-params` 属性支持交互
- **降级处理**: 无配置时使用默认展示，模板错误时显示错误信息

### 1.2 适用场景

- 天气查询服务 → 天气卡片
- 麦当劳积分兑换 → 商品列表卡片
- 麦当劳账户查询 → 账户信息卡片
- 麦当劳优惠券 → 优惠券列表卡片
- 任何其他结构化数据展示

---

## 2. 配置步骤

### 2.1 第一步: 了解MCP工具返回数据

在配置模板前，需要先了解MCP工具的实际返回格式。

#### 方法1: 通过后端测试脚本

```bash
cd /root/.openclaw/workspace/deer-flow/backend
uv run python << 'EOF'
import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def test_tool():
    async with streamablehttp_client(
        "https://your-mcp-server.com",
        headers={"Authorization": "Bearer YOUR_TOKEN"}
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 列出所有工具
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"Tool: {tool.name}")
                print(f"Schema: {json.dumps(tool.inputSchema, indent=2)}")
            
            # 调用工具查看返回
            result = await session.call_tool("tool_name", arguments={"param": "value"})
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text[:3000])

asyncio.run(test_tool())
EOF
```

#### 方法2: 查看API返回示例

典型的MCP工具返回格式：

```json
{
  "success": true,
  "code": 200,
  "message": "请求成功",
  "datetime": "2026-04-12 12:23:33",
  "traceId": "...",
  "data": {
    "availablePoint": "920.6",
    "accumulativePoint": "11627.3",
    "currency": "麦享会积分"
  }
}
```

### 2.2 第二步: 创建HTML模板文件

在项目根目录创建 `templates` 目录，按服务分类存放模板：

```
templates/
├── weather/
│   └── get_weather.html
└── mcd/
    ├── points_products.html
    ├── my_account.html
    └── my_coupons.html
```

#### 模板语法

使用 Mustache 模板引擎：

| 语法 | 说明 | 示例 |
|------|------|------|
| `{{result.field}}` | 渲染结果字段 | `{{result.city}}` |
| `{{args.field}}` | 渲染参数字段 | `{{args.city}}` |
| `{{#field}}...{{/field}}` | 条件渲染（字段存在或为true时显示） | `{{#result.forecast}}...{{/result.forecast}}` |
| `{{^field}}...{{/field}}` | 反向条件（字段不存在或为false时显示） | `{{^result.products}}暂无数据{{/result.products}}` |
| `{{#array}}...{{/array}}` | 数组遍历 | `{{#result.products}}...{{/result.products}}` |

#### 模板示例: 积分兑换商品

```html
<div class="mcp-card mcp-card-mcd">
  <div class="mcp-card-header">
    <span class="mcp-card-title">🍟 积分兑换商品</span>
    <span class="mcp-card-time">{{result.datetime}}</span>
  </div>
  
  <div class="mcp-card-body">
    {{#result.products}}
    <div class="mcd-product-item">
      <div class="mcd-product-image">
        <img src="{{spuImage}}" alt="{{spuName}}">
      </div>
      <div class="mcd-product-info">
        <div class="mcd-product-name">{{spuName}}</div>
        <div class="mcd-product-selling">{{selling}}</div>
        <div class="mcd-detail-row">
          <span>所需积分</span>
          <span class="mcd-points">{{point}} 积分</span>
        </div>
      </div>
      <div class="mcd-product-action">
        {{#canRedeem}}
        <button class="mcd-btn mcd-btn-primary" 
                data-action="redeem_product" 
                data-params='{"skuId": {{skuId}}, "spuName": "{{spuName}}"}'>
          立即兑换
        </button>
        {{/canRedeem}}
        {{^canRedeem}}
        <span class="mcd-btn mcd-btn-disabled">积分不足</span>
        {{/canRedeem}}
      </div>
    </div>
    {{/result.products}}
    
    {{^result.products}}
    <div class="mcd-empty-state">
      <div class="mcd-empty-icon">🎁</div>
      <div class="mcd-empty-text">暂无可兑换商品</div>
    </div>
    {{/result.products}}
  </div>
</div>
```

### 2.3 第三步: 配置 extensions_config.json

在 `extensions_config.json` 中为MCP服务器添加 `tools` 配置：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "enabled": true,
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      },
      "description": "麦当劳中国MCP服务",
      "tools": {
        "mcd-mcp_mall-points-products": {
          "card_title": "积分兑换商品",
          "icon": "gift",
          "template_path": "/root/.openclaw/workspace/deer-flow/templates/mcd/points_products.html"
        },
        "mcd-mcp_query-my-account": {
          "card_title": "我的麦享会账户",
          "icon": "user",
          "template_path": "/root/.openclaw/workspace/deer-flow/templates/mcd/my_account.html"
        }
      }
    }
  }
}
```

#### 配置字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `card_title` | string | 否 | 卡片标题，默认使用工具名称 |
| `icon` | string | 否 | Lucide图标名称，默认"wrench"。可用图标见 https://lucide.dev/icons |
| `template_path` | string | 是 | HTML模板文件**绝对路径** |

#### 工具名称匹配规则

配置中的工具名称必须与LangChain加载后的实际工具名称完全一致：

- 如果MCP服务器返回的工具名是 `mall-points-products`
- LangChain加载后可能变为 `mcd-mcp_mall-points-products`（带服务器前缀）
- 配置时应使用完整名称 `mcd-mcp_mall-points-products`

查看实际工具名称的方法：
```bash
cd /root/.openclaw/workspace/deer-flow/backend
uv run python -c "
import asyncio
from deerflow.mcp.tools import get_mcp_tools
async def main():
    tools = await get_mcp_tools()
    for t in tools:
        if 'mcd' in t.name.lower() or 'mall' in t.name.lower():
            print(f'Tool: {t.name}')
asyncio.run(main())
"
```

### 2.4 第四步: 添加数据解析函数（可选）

如果API返回的数据结构是嵌套的，需要在 `mcp-card.tsx` 中添加解析函数。

#### 示例: 解析麦当劳积分商品数据

```typescript
function parseMCDPointsProducts(raw: Record<string, unknown>, userPoints?: number): Record<string, unknown> {
  if (!raw.data || !Array.isArray(raw.data)) return raw;
  
  // 将嵌套的 data 数组扁平化为 products
  const products = raw.data.map((item: Record<string, unknown>) => ({
    ...item,
    canRedeem: userPoints ? Number(item.point) <= userPoints : true,
  }));
  
  return {
    datetime: raw.datetime,
    userPoints,
    products,
  };
}
```

#### 在 MCPCard 中使用解析函数

```typescript
let flattenedResult: Record<string, unknown>;

if (toolName.includes("mall-points-products")) {
  flattenedResult = parseMCDPointsProducts(parsedResult);
} else if (toolName.includes("query-my-account")) {
  flattenedResult = parseMCDAccount(parsedResult);
} else {
  flattenedResult = parsedResult;
}
```

### 2.5 第五步: 添加CSS样式

在 `frontend/src/components/workspace/messages/mcd-card.css` 中添加样式：

```css
.mcp-card-mcd {
  border-radius: 0.75rem;
  border: 1px solid var(--border, #e5e7eb);
  background: linear-gradient(135deg, #ffffff 0%, #fff9f0 100%);
  padding: 1rem;
  box-shadow: 0 2px 8px rgba(255, 195, 0, 0.1);
}

.mcd-product-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  background-color: #ffffff;
  border-radius: 0.5rem;
}

/* ... 更多样式 */
```

---

## 3. 完整示例: 麦当劳积分兑换

### 3.1 API返回数据

```json
{
  "success": true,
  "code": 200,
  "message": "请求成功",
  "datetime": "2026-04-12 12:23:33",
  "data": [
    {
      "spuName": "2.9元圆筒冰淇淋",
      "spuId": 15865,
      "skuId": 16555,
      "spuImage": "https://img.mcd.cn/ecs/b6ac0a0d579a8035.png",
      "point": "50",
      "shopId": 2,
      "selling": "2.9元圆筒冰淇淋1份",
      "upTime": "2026-03-22 00:00:03",
      "downTime": "2026-12-31 00:00:00"
    },
    {
      "spuName": "28.9元板烧四件套",
      "spuId": 16052,
      "skuId": 16742,
      "spuImage": "https://img.mcd.cn/ecs/13ade740ef5107d2.png",
      "point": "800",
      "selling": "28.9元板烧四件套",
      "upTime": "2026-04-01 00:00:00",
      "downTime": "2026-12-31 00:00:00"
    }
  ]
}
```

### 3.2 模板文件

`templates/mcd/points_products.html`:

```html
<div class="mcp-card mcp-card-mcd">
  <div class="mcp-card-header">
    <span class="mcp-card-title">🍟 积分兑换商品</span>
    <span class="mcp-card-time">{{result.datetime}}</span>
  </div>
  
  <div class="mcp-card-body">
    {{#result.products}}
    <div class="mcd-product-item">
      <img src="{{spuImage}}" alt="{{spuName}}" width="80" height="80">
      <div class="mcd-product-info">
        <div class="mcd-product-name">{{spuName}}</div>
        <div class="mcd-product-selling">{{selling}}</div>
        <div class="mcd-points">{{point}} 积分</div>
        <div class="mcd-time">{{upTime}} 至 {{downTime}}</div>
      </div>
      {{#canRedeem}}
      <button class="mcd-btn" data-action="redeem" data-params='{"skuId": {{skuId}}}'>
        立即兑换
      </button>
      {{/canRedeem}}
      {{^canRedeem}}
      <span class="mcd-btn-disabled">积分不足</span>
      {{/canRedeem}}
    </div>
    {{/result.products}}
  </div>
</div>
```

### 3.3 配置

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "enabled": true,
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "tools": {
        "mcd-mcp_mall-points-products": {
          "card_title": "积分兑换商品",
          "icon": "gift",
          "template_path": "/root/.openclaw/workspace/deer-flow/templates/mcd/points_products.html"
        }
      }
    }
  }
}
```

### 3.4 数据解析

```typescript
function parseMCDPointsProducts(raw: Record<string, unknown>): Record<string, unknown> {
  if (!raw.data || !Array.isArray(raw.data)) return raw;
  
  return {
    datetime: raw.datetime,
    products: raw.data.map(item => ({
      ...item,
      canRedeem: true, // 可根据用户积分动态计算
    })),
  };
}
```

---

## 4. 交互功能

### 4.1 声明交互

在HTML模板中使用 `data-action` 和 `data-params`：

```html
<button class="mcd-btn" 
        data-action="redeem_product" 
        data-params='{"skuId": {{skuId}}, "spuName": "{{spuName}}", "point": {{point}}}'>
  立即兑换
</button>
```

### 4.2 处理交互事件

MCPCard组件通过事件委托捕获点击：

```typescript
const handleContainerClick = (e: React.MouseEvent) => {
  const target = (e.target as HTMLElement).closest("[data-action]");
  if (!target) return;
  
  const action = target.getAttribute("data-action");
  const params = JSON.parse(target.getAttribute("data-params") || "{}");
  
  onAction({ action, params, toolName, serverName });
};
```

### 4.3 可用交互类型

| action | 说明 | 参数示例 |
|--------|------|----------|
| `redeem_product` | 兑换商品 | `{"skuId": 16555, "spuName": "冰淇淋"}` |
| `use_coupon` | 使用优惠券 | `{"couponId": "xxx"}` |
| `view_detail` | 查看详情 | `{"productId": 123}` |
| `refresh` | 刷新数据 | `{}` |

---

## 5. 常见问题

### 5.1 卡片不显示

**问题**: 配置了模板但前端没有显示卡片

**排查步骤**:
1. 检查工具名称是否匹配
   ```bash
   # 查看实际加载的工具名称
   curl http://localhost:8001/api/mcp/config | python3 -c "
   import sys,json
   d=json.load(sys.stdin)
   for n,s in d['mcp_servers'].items():
     for tn in s.get('tools',{}): print(f'{n}: {tn}')
   "
   ```

2. 检查模板路径是否正确
   ```bash
   # 测试模板API
   curl http://localhost:8001/api/mcp/templates/mcd-mcp_mall-points-products
   ```

3. 检查前端控制台是否有错误

### 5.2 模板渲染失败

**问题**: 显示 "Template render error"

**原因**:
- Mustache语法错误
- 数据结构与模板不匹配

**解决**:
```bash
# 本地测试模板渲染
node << 'EOF'
const Mustache = require('mustache');
const fs = require('fs');

const template = fs.readFileSync('templates/mcd/points_products.html', 'utf8');
const data = { result: { products: [...] } };

try {
  console.log(Mustache.render(template, data));
} catch (e) {
  console.error('Render error:', e.message);
}
EOF
```

### 5.3 样式不生效

**问题**: 卡片显示但样式混乱

**解决**:
1. 确认CSS文件已导入 `mcp-card.tsx`
2. 检查CSS类名是否与模板一致
3. 清除浏览器缓存

---

## 6. 模板文件清单

| 文件路径 | 用途 | 对应工具 |
|----------|------|----------|
| `templates/weather/get_weather.html` | 天气卡片 | weather_weather_api |
| `templates/mcd/points_products.html` | 积分兑换商品 | mcd-mcp_mall-points-products |
| `templates/mcd/my_account.html` | 账户信息 | mcd-mcp_query-my-account |
| `templates/mcd/my_coupons.html` | 优惠券列表 | mcd-mcp_query-my-coupons |

---

## 7. 最佳实践

1. **使用绝对路径**: `template_path` 必须是绝对路径
2. **工具名称完整**: 配置时使用完整的工具名称（含服务器前缀）
3. **数据扁平化**: 在解析函数中将嵌套数据扁平化，便于模板使用
4. **条件渲染**: 使用 `{{#field}}` 处理可选字段
5. **错误处理**: 模板中提供空状态展示
6. **响应式设计**: CSS考虑移动端适配
7. **图片容错**: 使用 `onerror` 处理图片加载失败

---

## 8. 相关文档

- [Mustache 模板语法](https://mustache.github.io/mustache.5.html)
- [Lucide 图标库](https://lucide.dev/icons)
- [MCP协议文档](https://modelcontextprotocol.io/)
