# DeerFlow 多租户功能文档

> **功能**: 多租户认证与用户隔离 (Multi-tenant Authentication and User Isolation)
> **状态**: ✅ 已实现并通过验证

---

## 一、架构概览

### 1.1 数据流

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (Browser/SDK)                      │
│   ┌──────────┐  ┌──────────┐  ┌──────────────────────────────┐  │
│   │  Bearer  │  │ HttpOnly │  │  No Auth (single-tenant)     │  │
│   │  Token   │  │  Cookie  │  │  → user_id="default"         │  │
│   └────┬─────┘  └────┬─────┘  └──────────────┬───────────────┘  │
└───────┼───────────────┼───────────────────────┼──────────────────┘
        │               │                       │
        ▼               ▼                       ▼
┌───────────────────────────────────────────────────────────────────┐
│              UserContextMiddleware (FastAPI)                       │
│  从 Authorization Header 或 Cookie 中提取 JWT → 解码 →           │
│  注入 request.state.user_id                                        │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                     隔离层 (Isolation Layer)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Threads  │  │ Memory   │  │ Agents   │  │ User Profiles    │  │
│  │ metadata │  │ per-user │  │ metadata │  │ per-user         │  │
│  │ user_id  │  │ file     │  │ user_id  │  │ file             │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

### 1.2 核心设计原则

| 原则 | 实现方式 |
|------|---------|
| **向后兼容** | 单租户模式下 `enabled=false`，所有请求使用 `user_id="default"` |
| **无状态认证** | JWT 自包含用户信息，服务端无需 session 存储 |
| **双通道认证** | Bearer Token (API) + HttpOnly Cookie (浏览器) |
| **线程级隔离** | LangGraph thread metadata 注入 `user_id` |
| **记忆级隔离** | 每用户独立文件 `memory/user_{user_id}/memory.json` |
| **Agent 级隔离** | `metadata.json` 记录归属，CRUD 时校验 |
| **Profile 级隔离** | 每用户独立文件 `user_profiles/user_{user_id}.md` |

### 1.3 认证流程

```
注册: Client → POST /api/v1/auth/register {email, password}
     → 检查邮箱 → 生成 UUID → bcrypt 哈希 → 持久化 users.json
     → 生成 JWT Token → 设置 HttpOnly Cookie → 返回 TokenResponse

登录: Client → POST /api/v1/auth/login {email, password}
     → 查找用户 → bcrypt 验证 → 生成 JWT → 返回 TokenResponse

API 请求: Client → GET /api/xxx (Authorization: Bearer <token>)
     → UserContextMiddleware 提取 user_id
     → 注入 request.state.user_id
     → 各 Router 按 user_id 过滤/校验归属
```

---

## 二、配置说明

### 2.1 config.yaml 多租户配置

```yaml
multi_tenant:
  enabled: true                       # 是否启用多租户模式
  jwt_secret: "your-secret-key"       # JWT 签名密钥 (或 DEER_FLOW_JWT_SECRET 环境变量)
  token_expire_minutes: 10080         # Token 过期时间 (分钟)，默认 7 天
  algorithm: "HS256"                  # JWT 算法: HS256 / RS256
  default_user_id: "default"          # 单租户模式下的默认用户 ID
```

### 2.2 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEER_FLOW_JWT_SECRET` | JWT 签名密钥 | `change-this-secret-key-in-production` |
| `DEER_FLOW_JWT_ALGORITHM` | JWT 算法 | `HS256` |
| `DEER_FLOW_CHECKPOINTER_CONNECTION_STRING` | PG 连接字符串 | - |

### 2.3 依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| `pyjwt` | >=2.8.0 | JWT Token 创建与验证 |
| `bcrypt` | >=4.0.0 | 密码哈希 |
| `email-validator` | >=2.0.0 | 邮箱格式验证 |
| `langgraph-checkpoint-postgres` | >=2.0.0 | PG checkpointer |
| `psycopg[binary]` | >=3.0.0 | PG 驱动 |
| `psycopg-pool` | >=3.0.0 | PG 连接池 |

---

## 三、数据模型

### 3.1 用户存储 (users.json)

```json
{
  "users": {
    "<uuid>": {
      "user_id": "<uuid>",
      "email": "user@example.com",
      "hashed_password": "$2b$12$...",
      "role": "user",
      "created_at": "2026-04-04T10:00:00",
      "quota_limits": { "max_threads": 10, "max_sandboxes": 5, "max_storage_mb": 1024 }
    }
  },
  "by_email": { "user@example.com": { <user object> } }
}
```

### 3.2 线程元数据 (PostgreSQL Store)

| 字段 | 类型 | 说明 |
|------|------|------|
| `thread_id` | string | 唯一标识 |
| `status` | string | idle/busy/interrupted/error |
| `metadata.user_id` | string | 归属用户 ID |
| `metadata.title` | string | 对话标题 |

### 3.3 记忆存储 (per-user)

```
{base_dir}/memory/user_{user_id}/memory.json
```

### 3.4 Agent 元数据 (metadata.json)

```json
{
  "user_id": "<uuid>",
  "created_at": 1775319629.8466828
}
```

### 3.5 用户 Profile (per-user)

```
{base_dir}/user_profiles/user_{user_id}.md
```

### 3.6 PostgreSQL 数据库表

| 表名 | 用途 |
|------|------|
| `checkpoints` | 检查点记录 (线程状态快照) |
| `checkpoint_blobs` | 通道值二进制存储 (消息内容) |
| `checkpoint_writes` | 检查点写入记录 |
| `store` | Store 数据 (线程元数据等) |
| `checkpoint_migrations` | 检查点迁移版本 |
| `store_migrations` | Store 迁移版本 |

---

## 四、API 参考

> **基础 URL**: `http://localhost:8001` (Gateway) 或 `http://localhost:2026` (Nginx)
> **认证**: `Authorization: Bearer <token>`
> **Content-Type**: `application/json`

### 4.1 完整调用流程

```
1. 用户注册 → POST /api/v1/auth/register
2. 用户登录 → POST /api/v1/auth/login → 获取 access_token
3. 创建线程 → POST /api/threads → 获取 thread_id (自动注入 user_id)
4. 发送消息 → POST /api/threads/{thread_id}/runs/wait → 获取 AI 回复
5. 获取记忆 → GET /api/memory → 返回当前用户的记忆数据
6. 搜索线程 → POST /api/threads/search → 仅返回当前用户的线程
7. 创建 Agent → POST /api/agents → 创建专属 Agent (自动记录 user_id)
8. 设置 Profile → PUT /api/user-profile → 设置用户画像
9. 用户登出 → POST /api/v1/auth/logout
```

### 4.2 认证 API

#### POST /api/v1/auth/register

注册新用户并返回 JWT Token。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `email` | string (Email) | 是 | 用户邮箱 |
| `password` | string (min 8) | 是 | 密码 |
| `role` | string | 否 | 角色，默认 `"user"` |

**响应** (201):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": "a1b2c3d4-...",
  "email": "user@example.com",
  "role": "user"
}
```

**错误**: `400` (邮箱已注册), `422` (验证失败)

#### POST /api/v1/auth/login

验证凭据并返回 JWT Token。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `email` | string (Email) | 是 | 用户邮箱 |
| `password` | string | 是 | 密码 |

**响应** (200): 同注册响应
**错误**: `401` (凭据无效)

#### GET /api/v1/auth/me

获取当前用户信息。无需认证时返回默认用户。

**响应** (200):
```json
{
  "user_id": "a1b2c3d4-...",
  "email": "user@example.com",
  "role": "user",
  "quota_limits": { "max_threads": 10, "max_sandboxes": 5, "max_storage_mb": 1024 }
}
```

#### POST /api/v1/auth/logout

登出当前用户。

**响应** (200): `{"message": "Successfully logged out"}`

### 4.3 线程 API

> 所有线程 API 受多租户隔离保护。创建时自动注入 `user_id`，搜索/访问/修改/删除时自动校验归属。

#### POST /api/threads

创建新线程。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `thread_id` | string | 否 | 自定义 ID，不传则自动生成 |
| `metadata` | object | 否 | 自定义元数据 (`user_id` 自动注入) |

**响应** (200):
```json
{
  "thread_id": "e142d249-...",
  "status": "idle",
  "created_at": "1775319629.8466828",
  "updated_at": "1775319629.8466828",
  "metadata": { "title": "My Chat", "user_id": "a1b2c3d4-..." },
  "values": {},
  "interrupts": {}
}
```

#### POST /api/threads/search

搜索当前用户的线程。**自动按 user_id 过滤**。

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `metadata` | object | 否 | `{}` | 元数据精确过滤 |
| `limit` | int | 否 | `100` | 最大结果 (1-1000) |
| `offset` | int | 否 | `0` | 分页偏移 |
| `status` | string | 否 | `null` | 状态过滤 |

**响应** (200): `ThreadResponse[]`

#### GET /api/threads/{thread_id}

获取线程详情。**仅允许访问自己的线程**。
**错误**: `403` (不属于当前用户), `404` (不存在)

#### PATCH /api/threads/{thread_id}

更新线程元数据。**`user_id` 不可篡改**。

#### DELETE /api/threads/{thread_id}

删除线程及所有数据。

#### GET /api/threads/{thread_id}/state

获取线程最新状态。

#### POST /api/threads/{thread_id}/state

更新线程状态 (human-in-the-loop 恢复)。

#### POST /api/threads/{thread_id}/history

获取检查点历史记录。

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `limit` | int | 否 | `10` | 最大条目 (1-100) |
| `before` | string | 否 | `null` | 分页游标 |

### 4.4 对话运行 API

#### POST /api/threads/{thread_id}/runs/wait

发送消息并等待 AI 回复。

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `assistant_id` | string | 否 | `"lead_agent"` | 助手 ID |
| `input` | object | 否 | `{"messages": []}` | 输入 |
| `config` | object | 否 | `{}` | 运行配置 |
| `context` | object | 否 | `{}` | 运行上下文 |
| `multitask_strategy` | string | 否 | `"reject"` | 多任务策略 |

**响应** (200):
```json
{
  "messages": [
    {"type": "human", "content": "你好"},
    {"type": "ai", "content": "你好！我是 DeerFlow AI 助手..."}
  ]
}
```

#### POST /api/threads/{thread_id}/runs/stream

发送消息并接收 SSE 流式回复。

#### POST /api/runs/wait

无状态同步运行 (自动创建临时线程)。

#### POST /api/runs/stream

无状态流式运行。

### 4.5 记忆 API

> 所有记忆 API 按 `user_id` 隔离。存储路径: `memory/user_{user_id}/memory.json`

#### GET /api/memory

获取当前用户的记忆数据。

**响应** (200):
```json
{
  "version": "1.0",
  "lastUpdated": "2026-04-04T15:41:23.310650Z",
  "user": {
    "workContext": {"summary": "", "updatedAt": ""},
    "personalContext": {"summary": "", "updatedAt": ""},
    "topOfMind": {"summary": "", "updatedAt": ""}
  },
  "history": {
    "recentMonths": {"summary": "", "updatedAt": ""},
    "earlierContext": {"summary": "", "updatedAt": ""},
    "longTermBackground": {"summary": "", "updatedAt": ""}
  },
  "facts": [
    {
      "id": "fact_22d84e97",
      "content": "User prefers TypeScript",
      "category": "preference",
      "confidence": 0.9,
      "createdAt": "2026-04-04T15:41:23.310213Z",
      "source": "manual"
    }
  ]
}
```

#### POST /api/memory/facts

创建记忆事实。

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `content` | string (min 1) | 是 | - | 事实内容 |
| `category` | string | 否 | `"context"` | 分类 |
| `confidence` | float (0-1) | 否 | `0.5` | 置信度 |

#### PATCH /api/memory/facts/{fact_id}

更新记忆事实。

#### DELETE /api/memory/facts/{fact_id}

删除记忆事实。

#### DELETE /api/memory

清空当前用户所有记忆。

#### GET /api/memory/export

导出当前用户记忆。

#### POST /api/memory/import

导入并覆盖当前用户记忆。

#### GET /api/memory/config

获取记忆系统配置 (无需认证)。

**响应** (200):
```json
{
  "enabled": true,
  "storage_path": "memory.json",
  "debounce_seconds": 30,
  "max_facts": 100,
  "fact_confidence_threshold": 0.7,
  "injection_enabled": true,
  "max_injection_tokens": 2000
}
```

#### GET /api/memory/status

获取记忆配置 + 当前用户数据。

### 4.6 Agent 管理 API

> 所有 Agent API 受多租户隔离保护。创建时写入 `metadata.json` 记录 `user_id`，列表/访问/修改/删除时自动校验归属。

#### GET /api/agents

列出当前用户可见的 Agent。**自动按 user_id 过滤**。

**响应** (200):
```json
{
  "agents": [
    {
      "name": "my-researcher",
      "description": "My Research Agent",
      "model": null,
      "tool_groups": null,
      "soul": null
    }
  ]
}
```

#### POST /api/agents

创建自定义 Agent。自动写入 `metadata.json`。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 名称 (`^[A-Za-z0-9-]+$`) |
| `description` | string | 否 | 描述 |
| `model` | string | 否 | 专属模型 |
| `tool_groups` | list[string] | 否 | 工具组白名单 |
| `soul` | string | 否 | SOUL.md 内容 |

**响应** (201):
```json
{
  "name": "my-researcher",
  "description": "My Research Agent",
  "model": null,
  "tool_groups": null,
  "soul": "I am a research specialist..."
}
```

#### GET /api/agents/{name}

获取 Agent 详情 (含 SOUL.md)。**仅允许访问自己的 Agent**。
**错误**: `403` (不属于当前用户), `404` (不存在)

#### PUT /api/agents/{name}

更新 Agent 配置/SOUL.md。**`user_id` 不可篡改**。

#### DELETE /api/agents/{name}

删除 Agent 及所有文件。**仅允许删除自己的 Agent**。

#### GET /api/agents/check?name={name}

检查 Agent 名称是否可用。

#### GET /api/user-profile

获取当前用户的 profile 内容。**按用户隔离存储**。

**响应** (200): `{"content": "# User Profile\nI am a software engineer."}`

#### PUT /api/user-profile

设置当前用户的 profile。存储为 `user_profiles/user_{user_id}.md`。

### 4.7 文件上传 API

> 所有上传 API 受多租户隔离保护。通过校验线程归属来确保用户只能操作自己的线程文件。

#### POST /api/threads/{thread_id}/uploads

上传文件 (multipart/form-data, `files` 字段)。**仅允许上传到自己拥有的线程**。
**错误**: `403` (不属于当前用户)

**响应** (200):
```json
{
  "success": true,
  "files": [{"filename": "doc.pdf", "size": "1024", "path": "/mnt/user-data/uploads/doc.pdf", "virtual_path": "/mnt/user-data/uploads/doc.pdf", "artifact_url": "/api/threads/{thread_id}/artifacts/mnt/user-data/uploads/doc.pdf"}],
  "message": "Successfully uploaded 1 file(s)"
}
```

#### GET /api/threads/{thread_id}/uploads/list

列出上传文件。**仅允许查看自己拥有的线程文件**。

#### DELETE /api/threads/{thread_id}/uploads/{filename}

删除上传文件。**仅允许删除自己拥有的线程文件**。

#### GET /api/threads/{thread_id}/artifacts/{path}

获取工件文件。**仅允许访问自己拥有的线程工件**。

### 4.8 其他 API (无需认证)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/models` | GET | 模型列表 |
| `/api/models/{name}` | GET | 模型详情 |
| `/api/skills` | GET | 技能列表 |
| `/api/mcp/config` | GET | MCP 配置 |
| `/api/threads/{thread_id}/suggestions` | POST | 对话建议 |
| `/api/threads/{thread_id}/artifacts/{path}` | GET | 工件文件 |

### 4.9 完整调用示例

```bash
BASE_URL="http://localhost:8001"

# 1. 注册
RESP=$(curl -s -X POST $BASE_URL/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "DemoPass123!"}')
TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
USER_ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['user_id'])")

# 2. 创建线程
THREAD=$(curl -s -X POST $BASE_URL/api/threads \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"title": "Demo Chat"}}')
THREAD_ID=$(echo "$THREAD" | python3 -c "import sys,json; print(json.load(sys.stdin)['thread_id'])")

# 3. 发送消息
curl -s -X POST $BASE_URL/api/threads/$THREAD_ID/runs/wait \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "human", "content": "你好"}]}, "assistant_id": "lead_agent"}'

# 4. 获取记忆
curl -s $BASE_URL/api/memory -H "Authorization: Bearer $TOKEN"

# 5. 搜索线程
curl -s -X POST $BASE_URL/api/threads/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'

# 6. 创建 Agent
curl -s -X POST $BASE_URL/api/agents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-researcher", "description": "Research Agent", "soul": "I am a researcher"}'

# 7. 设置 Profile
curl -s -X PUT $BASE_URL/api/user-profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "# My Profile\nI am a developer."}'

# 8. 登出
curl -s -X POST $BASE_URL/api/v1/auth/logout -H "Authorization: Bearer $TOKEN"
```

---

## 五、隔离矩阵

| 资源 | 隔离维度 | 存储位置 | 隔离机制 |
|------|---------|---------|---------|
| **线程** | user_id | PostgreSQL Store + Checkpointer | 创建时注入 metadata，搜索时过滤，访问时校验归属 |
| **记忆** | user_id | `memory/user_{user_id}/memory.json` | MemoryMiddleware 提取 user_id，Storage 按用户路径读写 |
| **Agent** | user_id | `agents/{name}/metadata.json` | 创建时写入 metadata.json，列表/访问/修改/删除时校验归属 |
| **Profile** | user_id | `user_profiles/user_{user_id}.md` | Router 提取 user_id 读写对应文件 |
| **上传文件** | thread_id (归属校验) | `threads/{thread_id}/user-data/uploads/` | 通过校验线程归属实现隔离 |
| **工件文件** | thread_id (归属校验) | `threads/{thread_id}/user-data/outputs/` | 通过校验线程归属实现隔离 |
| **线程数据** | thread_id | `threads/{thread_id}/` | 每个线程独立目录 (workspace/uploads/outputs) |

---

## 六、向后兼容

| 场景 | 行为 |
|------|------|
| 单租户模式 (`enabled=false`) | 所有隔离函数返回全部数据，不做过滤 |
| 无认证请求 | `user_id=None` → 回退到 `default_user_id` |
| 旧线程 (无 user_id metadata) | 视为无主线程，所有用户可见 (渐进迁移) |
| 旧 Agent (无 metadata.json) | 多租户模式下对任何用户不可见 (安全优先) |
| 旧 USER.md | 无 user_id 时回退到全局 `{base_dir}/USER.md` |
| 用户尝试篡改 user_id | 自动过滤，拒绝更新 |

---

## 七、文件目录结构

```
backend/
├── pyproject.toml                              # 依赖声明
├── app/gateway/
│   ├── app.py                                  # 中间件 + auth router 注册
│   ├── auth/
│   │   ├── __init__.py                         # 模块导出
│   │   ├── jwt.py                              # JWT 工具 (create/decode/verify)
│   │   └── models.py                           # TokenData, User, UserRole
│   ├── middleware/
│   │   ├── __init__.py                         # 模块导出
│   │   └── user_context.py                     # 用户上下文中间件
│   ├── routers/
│   │   ├── auth.py                             # 认证端点
│   │   ├── threads.py                          # 线程 CRUD (含隔离)
│   │   ├── memory.py                           # 记忆 API (含隔离)
│   │   └── agents.py                           # Agent CRUD (含隔离)
│   └── users/
│       ├── __init__.py                         # 模块导出
│       └── store.py                            # JSON 文件用户存储
├── packages/harness/deerflow/
│   ├── config/
│   │   ├── app_config.py                       # 加载 multi_tenant 配置
│   │   ├── multi_tenant_config.py              # 多租户配置模型
│   │   ├── agents_config.py                    # Agent 配置 + filter_agents_by_user
│   │   └── paths.py                            # 路径配置 + user_md_file(user_id)
│   ├── agents/
│   │   ├── thread_metadata.py                  # get_thread_metadata, filter_threads_by_user
│   │   ├── memory/
│   │   │   ├── queue.py                        # user_id 字段 + 传递
│   │   │   ├── storage.py                      # per-user 路径
│   │   │   └── updater.py                      # user_id 参数
│   │   └── middlewares/
│   │       ├── memory_middleware.py            # 提取并传递 user_id
│   │       └── dynamic_memory_middleware.py    # 运行时内存注入
│   └── utils/
│       └── file_helpers.py                     # 原子写入工具
└── tests/
    ├── test_auth_jwt.py                        # 17 tests
    ├── test_auth_router.py                     # 10 tests
    ├── test_user_store.py                      # 18 tests
    ├── test_multi_tenant_config.py             # 12 tests
    ├── test_thread_metadata.py                 # 8 tests
    ├── test_thread_metadata_integration.py     # 2 tests
    ├── test_user_context_middleware.py         # 6 tests
    └── test_file_helpers.py                    # 13 tests
```

---

## 八、验证

### 8.1 单元测试

```bash
cd backend
PYTHONPATH=. uv run pytest \
  tests/test_auth_jwt.py \
  tests/test_auth_router.py \
  tests/test_user_store.py \
  tests/test_multi_tenant_config.py \
  tests/test_thread_metadata.py \
  tests/test_thread_metadata_integration.py \
  tests/test_user_context_middleware.py \
  tests/test_file_helpers.py \
  -v
```

### 8.2 API 集成测试验证清单

| 测试项 | 预期 | 结果 |
|--------|------|------|
| 用户注册 | 201 + JWT | ✅ |
| 用户登录 | 200 + JWT | ✅ |
| 获取用户信息 (认证) | 200 + 真实 user_id | ✅ |
| 获取用户信息 (无认证) | 200 + default | ✅ |
| 重复邮箱注册 | 400 | ✅ |
| 错误密码登录 | 401 | ✅ |
| 无效 Token | 401 | ✅ |
| 线程创建 (user_id 注入) | 200 + metadata.user_id | ✅ |
| 线程搜索 (用户隔离) | 仅返回自己的线程 | ✅ |
| 线程访问 (跨用户) | 403 | ✅ |
| 线程更新 (防篡改 user_id) | user_id 不变 | ✅ |
| 线程删除 (跨用户) | 403 | ✅ |
| 记忆获取 (用户隔离) | 仅返回自己的记忆 | ✅ |
| 记忆创建 (用户隔离) | 写入 user_{id}/memory.json | ✅ |
| Agent 创建 (metadata.json) | 201 + metadata.json | ✅ |
| Agent 列表 (用户隔离) | 仅返回自己的 Agent | ✅ |
| Agent 访问 (跨用户) | 403 | ✅ |
| Agent 更新 (跨用户) | 403 | ✅ |
| Agent 删除 (跨用户) | 403 | ✅ |
| User-Profile (用户隔离) | 各自独立文件 | ✅ |
| 文件上传 (跨用户) | 403 | ✅ |
| 文件列出 (跨用户) | 403 | ✅ |
| 文件删除 (跨用户) | 403 | ✅ |
| 文件上传 (本人) | 200 | ✅ |
| 文件列出 (本人) | 200 | ✅ |
| 文件删除 (本人) | 200 | ✅ |
| 工件获取 (跨用户) | 403 | ✅ |
| 工件获取 (本人) | 200 | ✅ |
