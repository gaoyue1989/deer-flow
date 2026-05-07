# 对话历史同步 API

## 概述

对话历史同步API允许将外部agent或其他系统的对话历史导入到当前thread中，实现跨agent协作、对话迁移和历史导入等功能。

### 核心功能

- **消息追加**：外部消息追加到目标thread的消息列表末尾
- **自动去重**：使用LangGraph的`add_messages` reducer自动处理消息ID和去重
- **权限隔离**：基于user_id的多租户隔离，确保用户只能同步自己的对话
- **元数据记录**：记录同步来源、时间和数量等元数据信息

### 适用场景

- 跨agent协作：将一个agent的对话历史传递给另一个agent
- 对话迁移：从其他系统导入对话历史到DeerFlow
- 上下文共享：在多个thread之间共享部分对话上下文
- 历史恢复：从备份或外部存储恢复对话历史

### API端点

```
POST /api/threads/{thread_id}/sync-messages
```

---

## 快速开始

### 最简调用示例

```bash
curl -X POST http://localhost:2026/api/threads/my-thread/sync-messages \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "帮我分析这个数据"},
      {"role": "assistant", "content": "好的，我来帮你分析"}
    ]
  }'
```

### 基本响应示例

```json
{
  "success": true,
  "thread_id": "my-thread",
  "synced_count": 2,
  "total_messages": 2
}
```

### 一分钟快速上手

1. **准备目标thread**：确保thread已创建（可通过 `POST /api/threads` 创建）
2. **构造消息数组**：按照 `{role, content}` 格式准备要同步的消息
3. **调用API**：发送POST请求到 `/api/threads/{thread_id}/sync-messages`
4. **验证结果**：检查响应中的 `synced_count` 和 `total_messages`

---

## 详细说明

### 端点信息

| 项目 | 说明 |
|------|------|
| **URL** | `/api/threads/{thread_id}/sync-messages` |
| **方法** | POST |
| **认证** | Bearer Token 或 Session Cookie |
| **Content-Type** | application/json |

### 请求参数

#### URL参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `thread_id` | string | 是 | 目标thread的唯一标识符 |

#### Request Body

```json
{
  "messages": [
    {
      "role": "user",
      "content": "消息内容"
    }
  ],
  "source": "external-agent-name",
  "metadata": {
    "original_thread_id": "thread-123",
    "synced_at": "2026-01-01T00:00:00"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `messages` | array | 是 | 要同步的外部消息数组 |
| `source` | string | 否 | 来源标识（如外部agent名称），便于追溯 |
| `metadata` | object | 否 | 附加元数据，可存储原始对话ID、时间等信息 |

### 消息格式规范

#### ExternalMessage 结构

每条消息必须包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `role` | string | 是 | 消息角色，可选值：`user`、`assistant`、`system` |
| `content` | string | 是 | 消息文本内容 |

#### 支持的角色类型

- **user**：用户消息，转换为 `HumanMessage`
- **assistant**：助手消息，转换为 `AIMessage`
- **system**：系统消息，转换为 `SystemMessage`

#### 示例请求

```json
{
  "messages": [
    {"role": "user", "content": "请帮我分析这份报告"},
    {"role": "assistant", "content": "好的，我来分析这份报告的主要内容..."},
    {"role": "user", "content": "重点关注财务数据"},
    {"role": "assistant", "content": "根据报告，财务数据显示..."}
  ],
  "source": "report-analysis-agent",
  "metadata": {
    "original_conversation_id": "conv-789",
    "agent_version": "2.0"
  }
}
```

### 响应格式

#### 成功响应（200 OK）

```json
{
  "success": true,
  "thread_id": "target-thread-id",
  "synced_count": 4,
  "total_messages": 10
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 操作成功标识，始终为 `true` |
| `thread_id` | string | 目标thread ID |
| `synced_count` | integer | 本次同步的消息数量 |
| `total_messages` | integer | 同步后thread中的总消息数 |

---

## 错误处理

### 错误码对照表

| HTTP状态码 | 错误说明 | 可能原因 |
|-----------|---------|---------|
| **400** | 请求格式错误 | 缺少必填字段、消息格式无效、messages数组为空 |
| **403** | 权限拒绝 | thread属于其他用户，无权访问 |
| **404** | 资源不存在 | 指定的thread_id不存在 |
| **500** | 服务器内部错误 | checkpoint读取失败、checkpoint写入失败 |

### 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "detail": "错误详细说明"
}
```

### 常见错误示例

#### 400 - 消息数组为空

```json
{
  "detail": "No messages provided for sync"
}
```

**解决方案**：确保 `messages` 数组至少包含一条消息。

#### 403 - 权限拒绝

```json
{
  "detail": "Access denied: thread belongs to another user"
}
```

**解决方案**：检查thread的归属，确保使用正确的认证信息。

#### 404 - Thread不存在

```json
{
  "detail": "Thread thread-123 not found"
}
```

**解决方案**：先通过 `POST /api/threads` 创建thread，或检查thread_id是否正确。

#### 500 - Checkpoint操作失败

```json
{
  "detail": "Failed to read thread state"
}
```

或

```json
{
  "detail": "Failed to sync messages"
}
```

**解决方案**：检查数据库连接，查看服务器日志获取详细错误信息。

---

## 使用示例

### 基础示例：同步简单对话

#### cURL

```bash
curl -X POST http://localhost:2026/api/threads/my-thread/sync-messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好"},
      {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
    ]
  }'
```

#### Python (requests)

```python
import requests

url = "http://localhost:2026/api/threads/my-thread/sync-messages"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
}
data = {
    "messages": [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
    ]
}

response = requests.post(url, json=data, headers=headers)
result = response.json()
print(f"同步成功：{result['synced_count']}条消息，总计{result['total_messages']}条")
```

#### Python (DeerFlowClient)

```python
from deerflow.client import DeerFlowClient

client = DeerFlowClient()

# 直接使用底层的HTTP API
response = client._post(
    "/api/threads/my-thread/sync-messages",
    json={
        "messages": [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
        ]
    }
)
print(response)
```

#### JavaScript (fetch)

```javascript
const response = await fetch('http://localhost:2026/api/threads/my-thread/sync-messages', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    messages: [
      { role: 'user', content: '你好' },
      { role: 'assistant', content: '你好！有什么可以帮助你的吗？' }
    ]
  })
});

const result = await response.json();
console.log(`同步成功：${result.synced_count}条消息，总计${result.total_messages}条`);
```

#### JavaScript (axios)

```javascript
const axios = require('axios');

const response = await axios.post(
  'http://localhost:2026/api/threads/my-thread/sync-messages',
  {
    messages: [
      { role: 'user', content: '你好' },
      { role: 'assistant', content: '你好！有什么可以帮助你的吗？' }
    ]
  },
  {
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN'
    }
  }
);

console.log(`同步成功：${response.data.synced_count}条消息`);
```

### 进阶示例

#### 带来源标识的同步

```bash
curl -X POST http://localhost:2026/api/threads/my-thread/sync-messages \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "分析数据"},
      {"role": "assistant", "content": "分析完成"}
    ],
    "source": "data-analysis-agent"
  }'
```

**说明**：`source` 字段会记录在checkpoint的metadata中，便于追溯消息来源。

#### 同步大量历史消息

```python
import requests

# 分批同步，每批50条
messages = [...]  # 假设有200条消息
batch_size = 50

for i in range(0, len(messages), batch_size):
    batch = messages[i:i+batch_size]
    response = requests.post(
        "http://localhost:2026/api/threads/my-thread/sync-messages",
        json={"messages": batch, "source": "batch-import"},
        headers={"Authorization": "Bearer YOUR_TOKEN"}
    )
    print(f"批次 {i//batch_size + 1}: {response.json()['synced_count']}条")
```

**建议**：单次同步建议不超过50条消息，大量历史应分批处理。

#### 从其他系统导入对话

```python
import requests

# 假设从其他系统导出的对话格式
external_conversation = {
    "id": "conv-123",
    "messages": [
        {"sender": "user", "text": "问题1"},
        {"sender": "bot", "text": "回答1"},
        {"sender": "user", "text": "问题2"},
        {"sender": "bot", "text": "回答2"}
    ],
    "timestamp": "2026-01-01T00:00:00"
}

# 转换为DeerFlow格式
deerflow_messages = []
for msg in external_conversation["messages"]:
    role = "user" if msg["sender"] == "user" else "assistant"
    deerflow_messages.append({
        "role": role,
        "content": msg["text"]
    })

# 同步到DeerFlow
response = requests.post(
    "http://localhost:2026/api/threads/my-thread/sync-messages",
    json={
        "messages": deerflow_messages,
        "source": "external-system",
        "metadata": {
            "original_id": external_conversation["id"],
            "original_timestamp": external_conversation["timestamp"]
        }
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

#### 包含系统消息的同步

```bash
curl -X POST http://localhost:2026/api/threads/my-thread/sync-messages \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "你是一个数据分析助手"},
      {"role": "user", "content": "分析这份报告"},
      {"role": "assistant", "content": "好的，我来分析..."}
    ]
  }'
```

---

## 最佳实践

### 消息格式建议

#### ✅ 推荐做法

- 确保 `role` 字段使用正确的小写值：`user`、`assistant`、`system`
- `content` 字段使用纯文本，避免包含过多特殊字符或格式化代码
- 单条消息建议不超过10KB，超大消息应考虑拆分或使用文件上传

#### ❌ 避免的做法

- 不要使用未定义的 `role` 值（如 `"bot"`、`"ai"`）
- 不要在 `content` 中嵌入二进制数据或超大文本
- 不要同步包含敏感信息（密码、密钥等）的对话

### 性能优化

#### 单次同步数量

- **推荐**：单次同步 10-50 条消息
- **上限**：单次最多不超过 100 条
- **原因**：避免请求体过大，减少网络传输时间和服务器处理压力

#### 分批同步策略

```python
def sync_large_conversation(thread_id, all_messages, batch_size=50):
    """分批同步大量对话历史"""
    for i in range(0, len(all_messages), batch_size):
        batch = all_messages[i:i+batch_size]
        # 同步当前批次
        sync_messages(thread_id, batch)
        # 可选：添加延迟避免请求过快
        time.sleep(0.1)
```

#### 异步调用

对于大量同步任务，建议使用异步调用避免阻塞主线程：

```python
import asyncio
import aiohttp

async def async_sync_messages(thread_id, messages):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://localhost:2026/api/threads/{thread_id}/sync-messages",
            json={"messages": messages},
            headers={"Authorization": "Bearer YOUR_TOKEN"}
        ) as response:
            return await response.json()

# 并发同步多个thread
await asyncio.gather(
    async_sync_messages("thread-1", messages_1),
    async_sync_messages("thread-2", messages_2),
)
```

### 数据安全

#### 用户隔离

- 系统强制执行基于 `user_id` 的thread归属检查
- 无法同步到其他用户的thread
- 多租户模式下，不同用户的数据完全隔离

#### 敏感信息处理

```python
def sanitize_messages(messages):
    """清理消息中的敏感信息"""
    sanitized = []
    for msg in messages:
        content = msg["content"]
        # 移除可能的敏感信息
        content = remove_passwords(content)
        content = remove_api_keys(content)
        sanitized.append({"role": msg["role"], "content": content})
    return sanitized
```

### 元数据管理

#### 推荐的元数据结构

```json
{
  "source": "agent-name",
  "metadata": {
    "original_thread_id": "thread-123",
    "original_conversation_id": "conv-456",
    "synced_at": "2026-01-01T00:00:00",
    "agent_version": "2.0",
    "sync_reason": "cross-agent-collaboration"
  }
}
```

#### 元数据用途

- **追溯来源**：通过 `source` 和 `original_thread_id` 追踪消息来源
- **版本管理**：记录 `agent_version` 便于问题排查
- **审计日志**：`synced_at` 和 `sync_reason` 用于审计和分析

---

## 技术细节

### 消息合并机制

#### LangGraph add_messages Reducer

系统使用LangGraph的 `add_messages` reducer来合并消息：

```python
from langgraph.graph.message import add_messages

# 现有消息
existing_messages = [HumanMessage(content="问题1"), AIMessage(content="回答1")]

# 新消息
new_messages = [HumanMessage(content="问题2"), AIMessage(content="回答2")]

# 合并（自动处理ID和去重）
merged = add_messages(existing_messages, new_messages)
# 结果：[问题1, 回答1, 问题2, 回答2]
```

#### 消息ID处理

- LangChain消息需要唯一ID
- 如果未提供，系统自动生成UUID
- `add_messages` 根据ID自动去重，相同ID的消息不会重复添加

#### 消息顺序

- 新消息始终追加到现有消息列表末尾
- 保持原始对话的时间顺序
- 不会重新排序或打乱现有消息

### Checkpoint机制

#### Checkpoint不可变性

- 每次同步创建新的checkpoint
- 历史checkpoint保持不变，可随时回溯
- 支持时间旅行（通过 `GET /api/threads/{thread_id}/history`）

#### Metadata记录

同步操作会在checkpoint的metadata中记录：

```python
metadata = {
    "updated_at": 1704067200.0,  # Unix时间戳
    "sync_source": "external-agent",  # 来源标识
    "synced_count": 4,  # 同步的消息数量
    "sync_metadata": {  # 用户自定义元数据
        "original_id": "conv-123",
        "agent_version": "2.0"
    }
}
```

#### 查看同步历史

```bash
# 获取thread的checkpoint历史
curl http://localhost:2026/api/threads/my-thread/history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

每个checkpoint的 `metadata` 字段会包含同步操作的记录。

### 权限验证

#### Thread归属检查

系统通过 `_check_thread_ownership` 函数验证权限：

1. 从thread的metadata中获取 `user_id`
2. 与当前请求的认证用户ID比较
3. 如果不匹配，返回403错误

#### 多租户隔离

- 每个thread在创建时记录 `user_id`
- 所有操作（读取、更新、同步）都验证归属
- Legacy thread（无 `user_id`）允许所有用户访问（向后兼容）

---

## 常见问题（FAQ）

### Q1: 同步后消息会重复吗？

**A**: 不会。系统使用LangGraph的 `add_messages` reducer，会根据消息ID自动去重。如果尝试同步的消息ID已存在，该消息会被跳过。

### Q2: 可以同步其他用户的消息吗？

**A**: 不可以。系统强制执行基于 `user_id` 的thread归属检查。尝试同步到其他用户的thread会返回403错误。

### Q3: 同步的消息包含tool_calls吗？

**A**: 当前版本仅支持文本消息，不包含tool_calls、artifacts等复杂结构。如需同步完整消息对象，需要扩展API支持。

### Q4: 如何查看已同步消息的来源？

**A**: 可以通过以下方式查看：

1. **查看checkpoint历史**：
   ```bash
   curl http://localhost:2026/api/threads/{thread_id}/history
   ```
   每个checkpoint的 `metadata` 包含 `sync_source` 和 `sync_metadata`。

2. **查看thread状态**：
   ```bash
   curl http://localhost:2026/api/threads/{thread_id}/state
   ```
   最新的checkpoint metadata会显示最近的同步信息。

### Q5: 同步失败如何处理？

**A**: 建议按以下步骤排查：

1. **检查错误响应**：根据 `detail` 字段判断具体原因
2. **验证消息格式**：确保每条消息都有 `role` 和 `content` 字段
3. **检查权限**：确认thread归属和认证信息
4. **查看日志**：服务器日志包含详细的错误堆栈
5. **重试**：临时性错误（如数据库连接）可重试

### Q6: 同步的消息会影响agent的上下文吗？

**A**: 会。同步的消息会追加到thread的消息列表中，agent在后续对话中可以看到这些历史消息。这正是跨agent协作的基础。

### Q7: 可以删除已同步的消息吗？

**A**: 当前API不支持删除单条消息。如需清理，可以：

1. **回滚checkpoint**：使用 `POST /api/threads/{thread_id}/state` 恢复到之前的checkpoint
2. **删除thread**：使用 `DELETE /api/threads/{thread_id}` 删除整个thread

### Q8: 同步大量消息会影响性能吗？

**A**: 会有一定影响。建议：

- 单次同步不超过50条消息
- 大量历史分批处理
- 使用异步调用避免阻塞
- 在低峰期执行大批量同步

---

## 相关API

### Thread管理

| API | 说明 |
|-----|------|
| `POST /api/threads` | 创建新thread |
| `GET /api/threads/{thread_id}` | 查看thread详情 |
| `DELETE /api/threads/{thread_id}` | 删除thread及其数据 |
| `POST /api/threads/search` | 搜索和列出threads |

### 消息操作

| API | 说明 |
|-----|------|
| `GET /api/threads/{thread_id}/state` | 获取thread当前状态（包含消息列表） |
| `POST /api/threads/{thread_id}/state` | 更新thread状态 |
| `GET /api/threads/{thread_id}/history` | 查看checkpoint历史 |
| `POST /api/threads/{thread_id}/sync-messages` | 同步外部对话历史 |

### Run操作

| API | 说明 |
|-----|------|
| `POST /api/threads/{thread_id}/runs` | 创建新的对话run |
| `POST /api/threads/{thread_id}/runs/stream` | 创建run并流式返回 |
| `GET /api/threads/{thread_id}/runs` | 列出thread的所有runs |

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v1.0 | 2026-05-07 | 初始版本，支持基本消息同步功能 |

---

## 附录

### 数据模型定义

#### TypeScript定义

```typescript
/**
 * 外部消息格式
 */
interface ExternalMessage {
  /** 消息角色 */
  role: "user" | "assistant" | "system";
  /** 消息内容 */
  content: string;
}

/**
 * 同步消息请求
 */
interface SyncMessagesRequest {
  /** 要同步的消息数组 */
  messages: ExternalMessage[];
  /** 来源标识（可选） */
  source?: string;
  /** 附加元数据（可选） */
  metadata?: Record<string, any>;
}

/**
 * 同步消息响应
 */
interface SyncMessagesResponse {
  /** 操作成功标识 */
  success: boolean;
  /** 目标thread ID */
  thread_id: string;
  /** 本次同步的消息数量 */
  synced_count: number;
  /** 同步后的总消息数 */
  total_messages: number;
}
```

#### Python定义

```python
from pydantic import BaseModel, Field
from typing import Any, Literal

class ExternalMessage(BaseModel):
    """外部消息格式"""
    role: Literal["user", "assistant", "system"]
    content: str

class SyncMessagesRequest(BaseModel):
    """同步消息请求"""
    messages: list[ExternalMessage]
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class SyncMessagesResponse(BaseModel):
    """同步消息响应"""
    success: bool
    thread_id: str
    synced_count: int
    total_messages: int
```

### HTTP状态码速查表

| 状态码 | 类别 | 说明 | 常见原因 |
|--------|------|------|---------|
| **200** | 成功 | 操作成功 | - |
| **400** | 客户端错误 | 请求格式错误 | 缺少必填字段、格式无效 |
| **403** | 客户端错误 | 权限拒绝 | thread属于其他用户 |
| **404** | 客户端错误 | 资源不存在 | thread_id不存在 |
| **500** | 服务器错误 | 内部错误 | checkpoint操作失败 |

### 参考链接

- [LangGraph消息机制文档](https://langchain-ai.github.io/langgraph/)
- [DeerFlow架构说明](../../backend/docs/ARCHITECTURE.md)
- [Thread管理API文档](../../backend/docs/API.md)
- [Checkpoint机制说明](../../backend/docs/STREAMING.md)

---

## 反馈与支持

如有问题或建议，请通过以下方式反馈：

- **GitHub Issues**: [DeerFlow Issues](https://github.com/bytedance/deer-flow/issues)
- **文档贡献**: 欢迎提交PR改进文档
