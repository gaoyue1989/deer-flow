# PR #1127 多租户功能实施方案

## 概述
将 PR #1127 (feat: add multi-tenant authentication and user isolation) 的代码合并到本地 main 分支，实现 JWT 认证、用户隔离、多租户配置等功能。

## 已完成的工作

### 已创建的新文件 (11个)
1. `backend/app/gateway/auth/__init__.py` - 认证模块导出
2. `backend/app/gateway/auth/jwt.py` - JWT 工具（已修复 bcrypt 兼容性）
3. `backend/app/gateway/auth/models.py` - 认证模型
4. `backend/app/gateway/middleware/__init__.py` - 中间件导出
5. `backend/app/gateway/middleware/user_context.py` - 用户上下文中间件
6. `backend/app/gateway/routers/auth.py` - 认证端点
7. `backend/app/gateway/users/__init__.py` - 用户模块导出
8. `backend/app/gateway/users/store.py` - 用户存储
9. `backend/packages/harness/deerflow/config/multi_tenant_config.py` - 多租户配置
10. `backend/packages/harness/deerflow/utils/file_helpers.py` - 文件工具
11. `backend/packages/harness/deerflow/agents/thread_metadata.py` - 线程元数据工具

### 已修改的文件 (3个)
1. `backend/app/gateway/app.py` - 添加 UserContextMiddleware 和 auth router
2. `backend/app/channels/manager.py` - 在 _create_thread 和 /new 命令中注入 user_id metadata
3. `backend/packages/harness/deerflow/config/app_config.py` - 添加 multi_tenant 配置加载
4. `backend/pyproject.toml` - 添加 pyjwt, passlib[bcrypt], email-validator 依赖

### 已创建的测试文件 (8个)
1. `tests/test_thread_metadata.py` - 8 tests
2. `tests/test_thread_metadata_integration.py` - 2 integration tests
3. `tests/test_user_context_middleware.py` - 6 tests
4. `tests/test_multi_tenant_config.py` - 12 tests
5. `tests/test_auth_jwt.py` - 17 tests
6. `tests/test_user_store.py` - 18 tests
7. `tests/test_auth_router.py` - 10 tests
8. `tests/test_file_helpers.py` - 13 tests

## 仍需修改的文件 (关键缺失)

### 1. `packages/harness/deerflow/agents/memory/queue.py`
**需要添加 user_id 支持:**
- `ConversationContext` dataclass 添加 `user_id: str | None = None`
- `add()` 方法添加 `user_id` 参数
- `_process_queue()` 中调用 `updater.update_memory()` 时传递 `user_id`

### 2. `packages/harness/deerflow/agents/memory/storage.py`
**需要添加 user_id 支持:**
- `MemoryStorage` 抽象类的 `load()`, `reload()`, `save()` 添加 `user_id` 参数
- `FileMemoryStorage` 实现 per-user 内存文件路径 (`.deer-flow/memory/user_{user_id}/memory.json`)
- `_get_memory_file_path()` 支持 user_id
- `_memory_cache` 使用 `(agent_name, user_id)` 元组作为 key

### 3. `packages/harness/deerflow/agents/memory/updater.py`
**需要添加 user_id 支持:**
- `get_memory_data()`, `reload_memory_data()`, `import_memory_data()`, `clear_memory_data()` 添加 `user_id` 参数
- `create_memory_fact()`, `delete_memory_fact()`, `update_memory_fact()` 添加 `user_id` 参数
- `MemoryUpdater.update_memory()` 添加 `user_id` 参数
- `update_memory_from_conversation()` 添加 `user_id` 参数
- 所有调用 `get_memory_storage().load/save()` 时传递 `user_id`

### 4. `packages/harness/deerflow/agents/middlewares/memory_middleware.py`
**需要添加 user_id 支持:**
- `after_agent()` 中从 thread metadata 提取 `user_id`
- 调用 `queue.add()` 时传递 `user_id`

### 5. `packages/harness/deerflow/agents/middlewares/dynamic_memory_middleware.py` (NEW)
**需要创建:**
- LangGraph middleware that injects user-isolated memory into system prompt at runtime
- 从 thread metadata 提取 user_id
- 调用 `get_memory_data(agent_name=, user_id=)` 获取用户隔离内存

### 6. `packages/harness/deerflow/agents/lead_agent/prompt.py`
**需要修改:**
- 内存上下文注入时添加 user_id 信息

### 7. 修复测试失败
- `test_multi_tenant_config.py::test_jwt_secret_from_env` - env var 解析问题
- 依赖: 将 `passlib[bcrypt]` 替换为 `bcrypt` (passlib 1.7.4 与 bcrypt 5.0.0 不兼容)

## 执行顺序
1. 修改 `pyproject.toml` - 将 `passlib[bcrypt]` 替换为 `bcrypt`
2. 修改 `queue.py` - 添加 user_id
3. 修改 `storage.py` - 添加 user_id + per-user paths
4. 修改 `updater.py` - 添加 user_id 到所有函数
5. 修改 `memory_middleware.py` - 提取并传递 user_id
6. 创建 `dynamic_memory_middleware.py`
7. 修改 `prompt.py` - 添加 user_id
8. 修复测试
9. 运行 `make test` 验证
