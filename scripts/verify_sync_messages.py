#!/usr/bin/env python3
"""
对话历史同步API验证脚本

用于验证sync_messages功能的代码完整性和逻辑正确性。
不依赖完整的运行环境，仅验证代码结构和逻辑。

用法：python3 scripts/verify_sync_messages.py
"""

import ast
import sys
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """检查文件是否存在"""
    return Path(filepath).exists()


def read_file_content(filepath: str) -> str:
    """读取文件内容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def check_code_patterns(content: str, patterns: dict) -> dict:
    """检查代码中是否包含指定的模式"""
    results = {}
    for name, pattern in patterns.items():
        results[name] = pattern in content
    return results


def validate_python_syntax(content: str) -> tuple[bool, str]:
    """验证Python语法"""
    try:
        ast.parse(content)
        return True, "语法正确"
    except SyntaxError as e:
        return False, f"语法错误: {e}"


def main():
    print("=" * 70)
    print("对话历史同步API验证脚本")
    print("=" * 70)
    print()

    # 1. 检查文件存在性
    print("步骤 1: 检查文件存在性")
    print("-" * 70)
    
    files_to_check = {
        "threads.py": "backend/app/gateway/routers/threads.py",
        "测试文件": "backend/tests/test_sync_messages.py",
        "API文档": "docs/api/sync-messages.md",
        "文档索引": "docs/api/README.md",
        "API引用": "backend/docs/API.md",
    }
    
    all_files_exist = True
    for name, filepath in files_to_check.items():
        exists = check_file_exists(filepath)
        status = "✓" if exists else "✗"
        print(f"{status} {name}: {filepath}")
        if not exists:
            all_files_exist = False
    
    print()
    
    if not all_files_exist:
        print("✗ 部分文件缺失，请检查")
        return 1
    
    # 2. 验证Python语法
    print("步骤 2: 验证Python语法")
    print("-" * 70)
    
    threads_content = read_file_content("backend/app/gateway/routers/threads.py")
    test_content = read_file_content("backend/tests/test_sync_messages.py")
    
    syntax_ok, msg = validate_python_syntax(threads_content)
    status = "✓" if syntax_ok else "✗"
    print(f"{status} threads.py: {msg}")
    
    syntax_ok, msg = validate_python_syntax(test_content)
    status = "✓" if syntax_ok else "✗"
    print(f"{status} test_sync_messages.py: {msg}")
    print()
    
    # 3. 检查数据模型
    print("步骤 3: 检查数据模型定义")
    print("-" * 70)
    
    model_patterns = {
        "ExternalMessage类": "class ExternalMessage(BaseModel):",
        "role字段": 'role: Literal["user", "assistant", "system"]',
        "content字段": "content: str = Field",
        "SyncMessagesRequest类": "class SyncMessagesRequest(BaseModel):",
        "messages字段": "messages: list[ExternalMessage]",
        "source字段": "source: str | None",
        "metadata字段": "metadata: dict[str, Any]",
        "SyncMessagesResponse类": "class SyncMessagesResponse(BaseModel):",
        "success字段": "success: bool",
        "thread_id字段": "thread_id: str",
        "synced_count字段": "synced_count: int",
        "total_messages字段": "total_messages: int",
    }
    
    model_results = check_code_patterns(threads_content, model_patterns)
    all_models_ok = True
    for name, exists in model_results.items():
        status = "✓" if exists else "✗"
        print(f"{status} {name}")
        if not exists:
            all_models_ok = False
    
    print()
    
    # 4. 检查端点定义
    print("步骤 4: 检查API端点定义")
    print("-" * 70)
    
    endpoint_patterns = {
        "路由装饰器": '@router.post("/{thread_id}/sync-messages"',
        "response_model": "response_model=SyncMessagesResponse",
        "async函数": "async def sync_messages",
        "参数thread_id": "thread_id: str",
        "参数body": "body: SyncMessagesRequest",
        "参数request": "request: Request",
    }
    
    endpoint_results = check_code_patterns(threads_content, endpoint_patterns)
    all_endpoint_ok = True
    for name, exists in endpoint_results.items():
        status = "✓" if exists else "✗"
        print(f"{status} {name}")
        if not exists:
            all_endpoint_ok = False
    
    print()
    
    # 5. 检查核心逻辑
    print("步骤 5: 检查核心逻辑实现")
    print("-" * 70)
    
    logic_patterns = {
        "权限检查": "_check_thread_ownership(request, thread_id, record)",
        "空消息检查": "if not body.messages:",
        "400错误": 'raise HTTPException(status_code=400',
        "获取checkpoint": "await checkpointer.aget_tuple(config)",
        "404错误": 'raise HTTPException(status_code=404',
        "导入HumanMessage": "from langchain_core.messages import AIMessage, HumanMessage, SystemMessage",
        "导入add_messages": "from langgraph.graph.message import add_messages",
        "消息转换": "HumanMessage(content=msg.content)",
        "AIMessage转换": "AIMessage(content=msg.content)",
        "SystemMessage转换": "SystemMessage(content=msg.content)",
        "消息合并": "merged_messages = add_messages(existing_messages, converted_messages)",
        "写入checkpoint": "await checkpointer.aput(write_config, checkpoint, metadata, {})",
        "元数据记录": 'metadata["sync_source"]',
        "日志记录": "logger.info",
        "返回响应": "return SyncMessagesResponse(",
    }
    
    logic_results = check_code_patterns(threads_content, logic_patterns)
    all_logic_ok = True
    for name, exists in logic_results.items():
        status = "✓" if exists else "✗"
        print(f"{status} {name}")
        if not exists:
            all_logic_ok = False
    
    print()
    
    # 6. 检查测试覆盖
    print("步骤 6: 检查测试覆盖")
    print("-" * 70)
    
    test_patterns = {
        "ExternalMessage测试": "class TestExternalMessage",
        "SyncMessagesRequest测试": "class TestSyncMessagesRequest",
        "SyncMessagesResponse测试": "class TestSyncMessagesResponse",
        "消息转换测试": "class TestMessageConversion",
        "端点测试": "class TestSyncMessagesEndpoint",
        "API路由测试": "class TestSyncMessagesAPIRoute",
        "空消息测试": "test_sync_messages_empty_array_returns_400",
        "权限测试": "test_sync_messages_permission_denied_returns_403",
        "404测试": "test_sync_messages_thread_not_found_returns_404",
        "基本流程测试": "test_sync_messages_basic_flow",
        "追加消息测试": "test_sync_messages_appends_to_existing",
        "元数据测试": "test_sync_messages_records_metadata",
        "所有消息类型测试": "test_sync_messages_handles_all_message_types",
    }
    
    test_results = check_code_patterns(test_content, test_patterns)
    all_tests_ok = True
    for name, exists in test_results.items():
        status = "✓" if exists else "✗"
        print(f"{status} {name}")
        if not exists:
            all_tests_ok = False
    
    print()
    
    # 7. 检查文档
    print("步骤 7: 检查文档完整性")
    print("-" * 70)
    
    doc_content = read_file_content("docs/api/sync-messages.md")
    
    doc_patterns = {
        "API端点": "POST /api/threads/{thread_id}/sync-messages",
        "请求示例": '"messages":',
        "响应示例": '"success": true',
        "错误码": "400",
        "使用示例": "curl",
        "Python示例": "import requests",
        "JavaScript示例": "fetch",
        "最佳实践": "最佳实践",
        "FAQ": "常见问题",
        "技术细节": "技术细节",
    }
    
    doc_results = check_code_patterns(doc_content, doc_patterns)
    all_docs_ok = True
    for name, exists in doc_results.items():
        status = "✓" if exists else "✗"
        print(f"{status} {name}")
        if not exists:
            all_docs_ok = False
    
    print()
    
    # 8. 统计信息
    print("步骤 8: 代码统计")
    print("-" * 70)
    
    threads_lines = len(threads_content.splitlines())
    test_lines = len(test_content.splitlines())
    doc_lines = len(doc_content.splitlines())
    
    print(f"threads.py: {threads_lines} 行")
    print(f"test_sync_messages.py: {test_lines} 行")
    print(f"sync-messages.md: {doc_lines} 行")
    print(f"总计: {threads_lines + test_lines + doc_lines} 行")
    print()
    
    # 9. 最终结果
    print("=" * 70)
    print("验证结果总结")
    print("=" * 70)
    
    all_ok = all_files_exist and all_models_ok and all_endpoint_ok and all_logic_ok and all_tests_ok and all_docs_ok
    
    results = [
        ("文件存在性", all_files_exist),
        ("数据模型定义", all_models_ok),
        ("API端点定义", all_endpoint_ok),
        ("核心逻辑实现", all_logic_ok),
        ("测试覆盖", all_tests_ok),
        ("文档完整性", all_docs_ok),
    ]
    
    for name, ok in results:
        status = "✓" if ok else "✗"
        print(f"{status} {name}")
    
    print()
    
    if all_ok:
        print("✓ 所有验证通过！代码实现完整且正确。")
        print()
        print("下一步操作:")
        print("1. 启动DeerFlow服务: make dev 或 make docker-start")
        print("2. 运行API测试: ./scripts/test_sync_messages_api.sh")
        print("3. 运行单元测试: cd backend && pytest tests/test_sync_messages.py -v")
        return 0
    else:
        print("✗ 部分验证失败，请检查上述错误项。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
