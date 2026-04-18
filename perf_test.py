#!/usr/bin/env python3
"""
性能测试脚本: 测试 langgraph-compat API 在 10 并发下的性能瓶颈
自动注册/登录获取多租户 Token
"""

import asyncio
import aiohttp
import json
import time
import statistics
import os
import sys
import uuid
import random
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict
import argparse


# ==================== 配置区 ====================
BASE_URL = "http://42.194.213.236:2026"

class Config:
    CONCURRENCY = 10
    ROUNDS = 3
    STREAM_TIMEOUT = 60
    REQUESTS_PER_ROUND = 30
    NUM_TENANTS = 3

# 测试用的 thread IDs (需要预先存在)
THREAD_IDS = [
    "cc6bf816-8f68-4d13-87a0-86b8cecaf620",
    "e07550ac-bc8c-4807-bf0a-48afb2fc3450",
]

# ==================== 数据结构 ====================
@dataclass
class RequestResult:
    endpoint: str
    tenant: str
    status_code: int
    latency_ms: float
    ttfb_ms: Optional[float] = None
    error: Optional[str] = None
    response_size: int = 0


@dataclass
class TestReport:
    results: list = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0

    def add(self, result: RequestResult):
        self.results.append(result)

    def summary(self) -> dict:
        if not self.results:
            return {}

        by_endpoint = defaultdict(list)
        by_tenant = defaultdict(list)
        errors = []

        for r in self.results:
            key = f"{r.tenant}/{r.endpoint}"
            by_endpoint[key].append(r)
            by_tenant[r.tenant].append(r)
            if r.error:
                errors.append(r)

        total_time = self.end_time - self.start_time
        total_requests = len(self.results)
        success_requests = [r for r in self.results if r.error is None]
        error_requests = [r for r in self.results if r.error is not None]

        all_latencies = [r.latency_ms for r in success_requests]
        sorted_latencies = sorted(all_latencies) if all_latencies else [0]

        def percentile(data, p):
            if not data:
                return 0
            idx = int(len(data) * p / 100)
            idx = min(idx, len(data) - 1)
            return data[idx]

        summary = {
            "total_time_sec": round(total_time, 2),
            "total_requests": total_requests,
            "success": len(success_requests),
            "errors": len(error_requests),
            "error_rate": f"{len(error_requests)/total_requests*100:.1f}%" if total_requests else "0%",
            "throughput_rps": round(total_requests / total_time, 2) if total_time > 0 else 0,
            "latency_ms": {
                "min": round(min(all_latencies), 2) if all_latencies else 0,
                "max": round(max(all_latencies), 2) if all_latencies else 0,
                "avg": round(statistics.mean(all_latencies), 2) if all_latencies else 0,
                "p50": round(percentile(sorted_latencies, 50), 2),
                "p95": round(percentile(sorted_latencies, 95), 2),
                "p99": round(percentile(sorted_latencies, 99), 2),
            },
            "by_endpoint": {},
            "by_tenant": {},
            "stream_ttfb_ms": {},
            "errors_detail": [],
        }

        for key, results in by_endpoint.items():
            latencies = [r.latency_ms for r in results if r.error is None]
            errs = [r for r in results if r.error]
            ttfbs = [r.ttfb_ms for r in results if r.ttfb_ms is not None]
            summary["by_endpoint"][key] = {
                "count": len(results),
                "success": len(results) - len(errs),
                "errors": len(errs),
                "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
                "p95_latency_ms": round(percentile(sorted(latencies), 95), 2) if latencies else 0,
                "avg_ttfb_ms": round(statistics.mean(ttfbs), 2) if ttfbs else None,
            }

        for tenant, results in by_tenant.items():
            latencies = [r.latency_ms for r in results if r.error is None]
            errs = [r for r in results if r.error]
            summary["by_tenant"][tenant] = {
                "count": len(results),
                "success": len(results) - len(errs),
                "errors": len(errs),
                "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
            }

        # 流式 TTFB 统计
        stream_results = [r for r in self.results if r.endpoint == "stream" and r.ttfb_ms]
        if stream_results:
            ttfbs = [r.ttfb_ms for r in stream_results]
            sorted_ttfbs = sorted(ttfbs)
            summary["stream_ttfb_ms"] = {
                "min": round(min(ttfbs), 2),
                "max": round(max(ttfbs), 2),
                "avg": round(statistics.mean(ttfbs), 2),
                "p50": round(percentile(sorted_ttfbs, 50), 2),
                "p95": round(percentile(sorted_ttfbs, 95), 2),
            }

        for e in errors[:20]:
            summary["errors_detail"].append({
                "endpoint": e.endpoint,
                "tenant": e.tenant,
                "error": e.error,
            })

        return summary


# ==================== 认证 ====================
async def register_and_login(email: str, password: str) -> Optional[str]:
    """注册并登录获取 Bearer Token"""
    async with aiohttp.ClientSession() as session:
        # 尝试注册
        try:
            async with session.post(
                f"{BASE_URL}/api/v1/auth/register",
                json={"email": email, "password": password, "role": "user"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                if resp.status == 201 or resp.status == 200:
                    print(f"  注册成功: {email}")
                elif resp.status == 400:
                    print(f"  用户已存在: {email}")
                else:
                    print(f"  注册失败 ({resp.status}): {data}")
        except Exception as e:
            print(f"  注册异常: {e}")

        # 登录获取 token
        try:
            async with session.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"email": email, "password": password},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                if resp.status == 200:
                    token = data.get("access_token")
                    print(f"  登录成功: {email}, token: {token[:20]}...")
                    return token
                else:
                    print(f"  登录失败 ({resp.status}): {data}")
                    return None
        except Exception as e:
            print(f"  登录异常: {e}")
            return None


async def setup_tenants(num_tenants: int) -> list:
    """创建多个租户并获取 Token"""
    tenants = []
    for i in range(num_tenants):
        email = f"perftest{i+1}_{uuid.uuid4().hex[:6]}@test.com"
        password = "PerfTest123!"
        print(f"准备租户 {i+1}: {email}")

        token = await register_and_login(email, password)
        if token:
            tenants.append({
                "name": f"tenant_{i+1}",
                "token": token,
                "thread_id": THREAD_IDS[i % len(THREAD_IDS)],
            })
        else:
            print(f"  警告: 租户 {i+1} 获取 token 失败，将使用无认证模式")
            tenants.append({
                "name": f"tenant_{i+1}",
                "token": "",
                "thread_id": THREAD_IDS[i % len(THREAD_IDS)],
            })

    return tenants


# ==================== 请求函数 ====================
async def test_search(session, tenant, report, semaphore):
    """测试搜索线程接口"""
    url = f"{BASE_URL}/api/langgraph-compat/threads/search"
    headers = {"Content-Type": "application/json"}
    if tenant["token"]:
        headers["Authorization"] = f"Bearer {tenant['token']}"

    body = {
        "limit": 50,
        "offset": 0,
        "sort_by": "updated_at",
        "sort_order": "desc",
        "select": ["thread_id", "updated_at", "values", "metadata"],
    }

    async with semaphore:
        start = time.monotonic()
        try:
            async with session.post(url, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.text()
                latency = (time.monotonic() - start) * 1000
                report.add(RequestResult(
                    endpoint="search",
                    tenant=tenant["name"],
                    status_code=resp.status,
                    latency_ms=latency,
                    response_size=len(data),
                ))
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            report.add(RequestResult(
                endpoint="search",
                tenant=tenant["name"],
                status_code=0,
                latency_ms=latency,
                error=str(e),
            ))


async def test_history(session, tenant, report, semaphore):
    """测试获取历史消息接口"""
    thread_id = tenant["thread_id"]
    url = f"{BASE_URL}/api/langgraph-compat/threads/{thread_id}/history"
    headers = {"Content-Type": "application/json"}
    if tenant["token"]:
        headers["Authorization"] = f"Bearer {tenant['token']}"
    body = {"limit": 1}

    async with semaphore:
        start = time.monotonic()
        try:
            async with session.post(url, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.text()
                latency = (time.monotonic() - start) * 1000
                report.add(RequestResult(
                    endpoint="history",
                    tenant=tenant["name"],
                    status_code=resp.status,
                    latency_ms=latency,
                    response_size=len(data),
                ))
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            report.add(RequestResult(
                endpoint="history",
                tenant=tenant["name"],
                status_code=0,
                latency_ms=latency,
                error=str(e),
            ))


async def test_stream(session, tenant, report, semaphore):
    """测试流式对话接口"""
    thread_id = tenant["thread_id"]
    url = f"{BASE_URL}/api/langgraph-compat/threads/{thread_id}/runs/stream"
    headers = {"Content-Type": "application/json"}
    if tenant["token"]:
        headers["Authorization"] = f"Bearer {tenant['token']}"

    body = {
        "input": {
            "messages": [{
                "type": "human",
                "content": [{"type": "text", "text": "你好，性能测试"}],
                "additional_kwargs": {},
            }]
        },
        "config": {"recursion_limit": 1000},
        "context": {
            "model_name": "qwen3.5-plus",
            "mode": "flash",
            "reasoning_effort": "medium",
            "thinking_enabled": False,
            "is_plan_mode": False,
            "subagent_enabled": False,
            "thread_id": thread_id,
        },
        "stream_mode": ["messages-tuple", "values", "updates", "custom", "events"],
        "stream_subgraphs": True,
        "stream_resumable": True,
        "assistant_id": "lead_agent",
        "on_disconnect": "continue",
    }

    async with semaphore:
        start = time.monotonic()
        ttfb = None
        response_size = 0
        try:
            async with session.post(url, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=Config.STREAM_TIMEOUT)) as resp:
                first_chunk = True
                async for chunk in resp.content.iter_any():
                    if first_chunk:
                        ttfb = (time.monotonic() - start) * 1000
                        first_chunk = False
                    response_size += len(chunk)

                latency = (time.monotonic() - start) * 1000
                report.add(RequestResult(
                    endpoint="stream",
                    tenant=tenant["name"],
                    status_code=resp.status,
                    latency_ms=latency,
                    ttfb_ms=round(ttfb, 2) if ttfb else None,
                    response_size=response_size,
                ))
        except asyncio.TimeoutError:
            latency = (time.monotonic() - start) * 1000
            report.add(RequestResult(
                endpoint="stream",
                tenant=tenant["name"],
                status_code=0,
                latency_ms=latency,
                ttfb_ms=round(ttfb, 2) if ttfb else None,
                error="Timeout",
            ))
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            report.add(RequestResult(
                endpoint="stream",
                tenant=tenant["name"],
                status_code=0,
                latency_ms=latency,
                ttfb_ms=round(ttfb, 2) if ttfb else None,
                error=str(e),
            ))


# ==================== 测试执行 ====================
async def run_round(round_num, tenants, report, semaphore):
    """执行一轮测试"""
    print(f"\n{'='*60}")
    print(f"第 {round_num} 轮测试开始")
    print(f"{'='*60}")

    tasks = []
    pass  # run_round is deprecated, use run_round_v2
    async with aiohttp.ClientSession(connector=connector) as session:
        # 重新绑定 session
        bound_tasks = []
        for task in tasks:
            # 任务已经在创建时绑定了参数，这里直接执行
            bound_tasks.append(task)

        start = time.monotonic()
        await asyncio.gather(*bound_tasks, return_exceptions=True)
        round_time = time.monotonic() - start

        completed = len([r for r in report.results if r.latency_ms > 0])
        print(f"第 {round_num} 轮完成: {completed} 个请求, 耗时 {round_time:.2f}s")


async def run_round_v2(round_num, tenants, report, semaphore):
    """执行一轮测试 (修正版 - 正确传递 session)"""
    print(f"\n{'='*60}")
    print(f"第 {round_num} 轮测试开始")
    print(f"{'='*60}")

    connector = aiohttp.TCPConnector(limit=Config.CONCURRENCY, limit_per_host=Config.CONCURRENCY)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        req_per_tenant = max(1, Config.REQUESTS_PER_ROUND // len(tenants) // 2)

        for tenant in tenants:
            for _ in range(req_per_tenant):
                tasks.append(test_search(session, tenant, report, semaphore))
                tasks.append(test_history(session, tenant, report, semaphore))
            tasks.append(test_stream(session, tenant, report, semaphore))

        random.shuffle(tasks)

        start = time.monotonic()
        await asyncio.gather(*tasks, return_exceptions=True)
        round_time = time.monotonic() - start

        completed = len([r for r in report.results])
        print(f"第 {round_num} 轮完成: {completed} 个请求, 耗时 {round_time:.2f}s")


def print_report(report):
    """打印测试报告"""
    summary = report.summary()

    print(f"\n{'='*60}")
    print("性能测试报告")
    print(f"{'='*60}")
    print(f"总耗时:        {summary['total_time_sec']}s")
    print(f"总请求数:      {summary['total_requests']}")
    print(f"成功:          {summary['success']}")
    print(f"失败:          {summary['errors']}")
    print(f"错误率:        {summary['error_rate']}")
    print(f"吞吐量:        {summary['throughput_rps']} req/s")
    print(f"\n延迟分布 (ms):")
    print(f"  最小:        {summary['latency_ms']['min']}")
    print(f"  最大:        {summary['latency_ms']['max']}")
    print(f"  平均:        {summary['latency_ms']['avg']}")
    print(f"  P50:         {summary['latency_ms']['p50']}")
    print(f"  P95:         {summary['latency_ms']['p95']}")
    print(f"  P99:         {summary['latency_ms']['p99']}")

    if summary.get("stream_ttfb_ms"):
        print(f"\n流式 TTFB 分布 (ms):")
        for k, v in summary["stream_ttfb_ms"].items():
            print(f"  {k}: {v}")

    print(f"\n按接口统计:")
    for endpoint, stats in summary['by_endpoint'].items():
        ttfb_info = f", TTFB: {stats['avg_ttfb_ms']}ms" if stats.get('avg_ttfb_ms') else ""
        print(f"  {endpoint}:")
        print(f"    请求数: {stats['count']}, 成功: {stats['success']}, 失败: {stats['errors']}")
        print(f"    平均延迟: {stats['avg_latency_ms']}ms, P95: {stats['p95_latency_ms']}ms{ttfb_info}")

    print(f"\n按租户统计:")
    for tenant, stats in summary['by_tenant'].items():
        print(f"  {tenant}:")
        print(f"    请求数: {stats['count']}, 成功: {stats['success']}, 失败: {stats['errors']}")
        print(f"    平均延迟: {stats['avg_latency_ms']}ms")

    if summary['errors_detail']:
        print(f"\n错误详情 (最多20条):")
        for err in summary['errors_detail']:
            print(f"  [{err['tenant']}] {err['endpoint']}: {err['error']}")


async def main():
    parser = argparse.ArgumentParser(description="API 性能测试")
    parser.add_argument("--concurrency", type=int, default=Config.CONCURRENCY, help="并发数")
    parser.add_argument("--rounds", type=int, default=Config.ROUNDS, help="测试轮数")
    parser.add_argument("--requests", type=int, default=Config.REQUESTS_PER_ROUND, help="每轮总请求数")
    parser.add_argument("--tenants", type=int, default=Config.NUM_TENANTS, help="租户数量")
    parser.add_argument("--tokens", type=str, nargs="+", help="直接使用已有的 Bearer Token 列表")
    parser.add_argument("--threads", type=str, nargs="+", help="Thread ID 列表")
    parser.add_argument("--skip-auth", action="store_true", help="跳过认证，直接测试")
    args = parser.parse_args()

    Config.CONCURRENCY = args.concurrency
    Config.ROUNDS = args.rounds
    Config.REQUESTS_PER_ROUND = args.requests
    Config.NUM_TENANTS = args.tenants

    print(f"配置:")
    print(f"  目标地址: {BASE_URL}")
    print(f"  并发数:   {Config.CONCURRENCY}")
    print(f"  测试轮数: {Config.ROUNDS}")
    print(f"  每轮请求: {Config.REQUESTS_PER_ROUND}")

    # 获取租户
    if args.skip_auth:
        print(f"  模式:     无认证")
        tenants = [{"name": f"tenant_{i+1}", "token": "", "thread_id": THREAD_IDS[i % len(THREAD_IDS)]} for i in range(Config.NUM_TENANTS)]
    elif args.tokens:
        print(f"  模式:     指定 Token")
        thread_ids = args.threads or THREAD_IDS
        tenants = [{"name": f"tenant_{i+1}", "token": t, "thread_id": thread_ids[i % len(thread_ids)]} for i, t in enumerate(args.tokens)]
    else:
        print(f"  模式:     自动注册/登录")
        print(f"  租户数:   {Config.NUM_TENANTS}")
        tenants = await setup_tenants(Config.NUM_TENANTS)

    if not tenants:
        print("错误: 没有可用的租户配置")
        sys.exit(1)

    print(f"\n使用 {len(tenants)} 个租户进行测试:")
    for t in tenants:
        token_preview = f"{t['token'][:20]}..." if t['token'] else "(无)"
        print(f"  - {t['name']}: token={token_preview}, thread={t['thread_id'][:8]}...")

    report = TestReport()
    semaphore = asyncio.Semaphore(Config.CONCURRENCY)

    report.start_time = time.monotonic()

    for round_num in range(1, Config.ROUNDS + 1):
        await run_round_v2(round_num, tenants, report, semaphore)

    report.end_time = time.monotonic()

    print_report(report)

    # 保存报告
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"perf_report_{timestamp}.json"
    with open(report_file, "w") as f:
        json.dump(report.summary(), f, indent=2, ensure_ascii=False)
    print(f"\n报告已保存到: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
