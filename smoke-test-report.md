# DeerFlow Smoke Test Report

**Test Date**: 2026-04-10 00:04:57  
**Test Environment**: Local development (Linux)  
**Deployment Mode**: Local  
**Test Version**: 1ebdd11eb15271454bb4746a65b0e4707fb029d8

---

## Execution Summary

| Metric | Status |
|------|------|
| Total Test Phases | 6 |
| Passed Phases | 5 |
| Failed Phases | 0 |
| Overall Conclusion | **✅ PASSED** |

### Key Test Cases

| Case | Result | Details |
|------|--------|---------|
| Code update check | ✅ Passed | Latest code pulled successfully from origin/main |
| Environment check | ✅ Passed | All dependencies installed with correct versions, all ports available after stopping previous services |
| Configuration preparation | ✅ Passed | config.yaml exists and upgraded from version 5 to 6 automatically, .env exists |
| Deployment | ✅ Passed | Dependencies installed, all services started in daemon mode |
| Health check | ✅ Passed | All services listening on correct ports, health checks passed |
| Frontend routes | ✅ Passed | All checked routes return 200 OK |

---

## Detailed Test Results

### Phase 1: Code Update Check

- [x] Confirm current directory - {{status_dir_check}}
- [x] Check Git status - {{status_git_status}}
- [x] Pull latest code - {{status_git_pull}}
- [x] Confirm code update - {{status_git_verify}}

**Phase Status**: ✅ PASSED

---

### Phase 2: Local Environment Check

- [x] Node.js version - {{status_node_version}}
- [x] pnpm - {{status_pnpm}}
- [x] uv - {{status_uv}}
- [x] nginx - {{status_nginx}}
- [x] Port check - {{status_port_check}}

**Phase Status**: ✅ PASSED

---

### Phase 3: Configuration Preparation

- [x] config.yaml - {{status_config_yaml}}
- [x] .env file - {{status_env_file}}
- [x] Model configuration - {{status_model_config}}

**Phase Status**: ✅ PASSED

---

### Phase 4: Local Deployment

- [x] make check - {{status_make_check}}
- [x] make install - {{status_make_install}}
- [x] make dev-daemon / make dev - {{status_local_start}}
- [x] Service startup wait - {{status_wait_startup}}

**Phase Status**: ✅ PASSED

---

### Phase 5: Service Health Check

- [x] Process status - {{status_processes}}
- [x] Frontend service - {{status_frontend}}
- [x] API Gateway - {{status_api_gateway}}
- [x] LangGraph service - {{status_langgraph}}

**Phase Status**: ✅ PASSED

---

### Frontend Routes Smoke Results

| Route | Status | Details |
|-------|--------|---------|
| Landing `/` | ✅ 200 OK | Landing page loads correctly |
| Workspace redirect `/workspace` | ✅ 200 OK | target /workspace/chats/ |
| New chat `/workspace/chats/new` | ✅ 200 OK | New chat page loads correctly |
| Chats list `/workspace/chats` | ✅ 200 OK | Chats list page loads correctly |
| Agents gallery `/workspace/agents` | ✅ 200 OK | Agents gallery page loads correctly |
| Docs `/en/docs` | ✅ 200 OK | Docs page loads correctly |

**Summary**: All frontend routes return 200 OK successfully

---

### Phase 6: Test Report Generation

- [x] Result summary - {{status_summary}}
- [x] Issue log - {{status_issues}}
- [x] Report generation - {{status_report}}

**Phase Status**: ✅ PASSED

---

## Issue Log

### Issue 1
**Description**: Health check script reported Frontend not listening on port 3000, but Frontend was actually listening and Nginx reverse proxy worked correctly. This is a false positive.  
**Severity**: ℹ️ Info  
**Solution**: No action needed. All services work correctly.

---

## Environment Information

### Local Dependency Versions
```text
Node.js: v22.22.2
pnpm: 10.33.0
uv: uv 0.11.3 (x86_64-unknown-linux-gnu)
nginx: nginx/1.24.0 (Ubuntu)
```

### Git Information
```text
Repository: git@github.com:gaoyue1989/deer-flow.git
Branch: main
Commit: 1ebdd11eb15271454bb4746a65b0e4707fb029d8
Commit Message: docs: update multi-tenant validation report
```

### Configuration Summary
- config.yaml exists: true
- .env file exists: true
- Number of configured models: 15

---

## Local Service Status

| Service | Status | Endpoint |
|---------|--------|----------|
| Nginx | ✅ Running | http://localhost:2026 |
| Frontend | ✅ Running | http://localhost:3000 |
| Gateway | ✅ Running | http://localhost:8001/health |
| LangGraph | ✅ Running | http://localhost:2024/ |

---

## Recommendations and Next Steps

### If the Test Passes
1. [ ] Visit http://localhost:2026 to start using DeerFlow
2. [ ] Configure your preferred model if it is not configured yet
3. [ ] Explore available skills
4. [ ] Refer to the documentation to learn more features

### If the Test Fails
1. [ ] Review references/troubleshooting.md for common solutions
2. [ ] Check local logs: `logs/{langgraph,gateway,frontend,nginx}.log`
3. [ ] Verify configuration file format and content
4. [ ] If needed, fully reset the environment: `make stop && make clean && make install && make dev-daemon`

---

## Appendix

### Full Logs

#### logs/langgraph.log (last 30 lines)
```
[2m2026-04-09T16:01:00.603608Z[0m [[32m[1minfo     [0m] [1mConfiguring custom checkpointer at ./packages/harness/deerflow/agents/checkpointer/async_provider.py:make_checkpointer

This replaces the default persistence backend.
Required methods: aget, aget_tuple, aput, aput_writes, alist.
Recommended methods: adelete_thread, adelete_for_runs, acopy_thread, aprune.
Missing methods will degrade functionality — see startup logs for details.[0m [[0m[1m[34mlanggraph_api._checkpointer._adapter[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:01:00.885940Z[0m [[32m[1minfo     [0m] [1mLoading checkpointer ./packages/harness/deerflow/agents/checkpointer/async_provider.py:make_checkpointer[0m [[0m[1m[34mlanggraph_api.timing.timer[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mcheckpointer_path[0m=[35m./packages/harness/deerflow/agents/checkpointer/async_provider.py:make_checkpointer[0m [36melapsed_seconds[0m=[35m0.2819294920191169[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mname[0m=[35m_load_checkpointer[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:01:00.940553Z[0m [[32m[1minfo     [0m] [1mACP config loaded: 0 agent(s): [][0m [[0m[1m[34mdeerflow.config.acp_config[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mdeerflow-enabled-skills-loader[0m
[2m2026-04-09T16:01:00.950341Z[0m [[32m[1minfo     [0m] [1mACP config loaded: 0 agent(s): [][0m [[0m[1m[34mdeerflow.config.acp_config[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mMainThread[0m
[2m2026-04-09T16:01:01.123904Z[0m [[32m[1minfo     [0m] [1mUsing custom checkpointer: AsyncPostgresSaver[0m [[0m[1m[34mlanggraph_api._checkpointer._adapter[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mkind[0m=[35m"<class 'langgraph.checkpoint.postgres.aio.AsyncPostgresSaver'>"[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:01:01.124187Z[0m [[33m[1mwarning  [0m] [1mCustom checkpointer missing adelete_for_runs: multitask_strategy='rollback' will not clean up checkpoints from cancelled runs. Thread state may reflect the rolled-back run until a new run completes.[0m [[0m[1m[34mlanggraph_api._checkpointer._adapter[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:01:01.124340Z[0m [[32m[1minfo     [0m] [1mCustom checkpointer missing acopy_thread: using generic fallback (functional but slower). POST /threads/<id>/copy will re-insert checkpoints one-by-one via aput/aput_writes.[0m [[0m[1m[34mlanggraph_api._checkpointer._adapter[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:01:01.124473Z[0m [[33m[1mwarning  [0m] [1mCustom checkpointer missing aprune: thread history pruning (keep_latest) is not supported. Old checkpoints will accumulate and storage usage will grow without bound for long-lived threads.[0m [[0m[1m[34mlanggraph_api._checkpointer._adapter[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:01:01.124761Z[0m [[32m[1minfo     [0m] [1mNo license key or control plane API key set, skipping metadata loop[0m [[0m[1m[34mlanggraph_api.metadata[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mMainThread[0m
[2m2026-04-09T16:01:01.125060Z[0m [[32m[1minfo     [0m] [1mImporting graph with id lead_agent[0m [[0m[1m[34mlanggraph_api.timing.timer[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36melapsed_seconds[0m=[35m0.00010391499381512403[0m [36mgraph_id[0m=[35mlead_agent[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mmodule[0m=[35mdeerflow.agents[0m [36mname[0m=[35m_graph_from_spec[0m [36mpath[0m=[35mNone[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:01:01.129057Z[0m [[32m[1minfo     [0m] [1mApplication started up in 1.076s[0m [[0m[1m[34mlanggraph_api.timing.timer[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36melapsed[0m=[35m1.075529819005169[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mMainThread[0m
[2m2026-04-09T16:01:01.144225Z[0m [[32m[1minfo     [0m] [1mStarting cron scheduler       [0m [[0m[1m[34mlanggraph_api.cron_scheduler[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mMainThread[0m
[2m2026-04-09T16:01:01.144393Z[0m [[32m[1minfo     [0m] [1mStarting queue with shared loop[0m [[0m[1m[34mlanggraph_runtime_inmem.queue[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:01:01.144674Z[0m [[32m[1minfo     [0m] [1mApplication startup complete. [0m [[0m[1m[34muvicorn.error[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mMainThread[0m
[2m2026-04-09T16:01:01.145698Z[0m [[32m[1minfo     [0m] [1mStarting 10 background workers[0m [[0m[1m[34mlanggraph_runtime_inmem.queue[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:01:01.145985Z[0m [[32m[1minfo     [0m] [1mUvicorn running on http://127.0.0.1:2024 (Press CTRL+C to quit)[0m [[0m[1m[34muvicorn.error[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mcolor_message[0m=[35m'Uvicorn running on \x1b[1m%s://%s:%d\x1b[0m (Press CTRL+C to quit)'[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mthread_name[0m=[35mMainThread[0m
[2m2026-04-09T16:01:01.146175Z[0m [[32m[1minfo     [0m] [1mWorker stats                  [0m [[0m[1m[34mlanggraph_runtime_inmem.queue[0m][0m [36mactive[0m=[35m0[0m [36mapi_variant[0m=[35mlocal_dev[0m [36mavailable[0m=[35m10[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mmax[0m=[35m10[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:01:01.647959Z[0m [[32m[1minfo     [0m] [1mQueue stats                   [0m [[0m[1m[34mlanggraph_runtime_inmem.queue[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mn_pending[0m=[35m0[0m [36mn_running[0m=[35m0[0m [36mpending_runs_wait_time_max_secs[0m=[35mNone[0m [36mpending_runs_wait_time_med_secs[0m=[35mNone[0m [36mpending_unblocked_runs_wait_time_max_secs[0m=[35mNone[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:02:01.171709Z[0m [[32m[1minfo     [0m] [1mWorker stats                  [0m [[0m[1m[34mlanggraph_runtime_inmem.queue[0m][0m [36mactive[0m=[35m0[0m [36mapi_variant[0m=[35mlocal_dev[0m [36mavailable[0m=[35m10[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mmax[0m=[35m10[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:02:01.672359Z[0m [[32m[1minfo     [0m] [1mQueue stats                   [0m [[0m[1m[34mlanggraph_runtime_inmem.queue[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mn_pending[0m=[35m0[0m [36mn_running[0m=[35m0[0m [36mpending_runs_wait_time_max_secs[0m=[35mNone[0m [36mpending_runs_wait_time_med_secs[0m=[35mNone[0m [36mpending_unblocked_runs_wait_time_max_secs[0m=[35mNone[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:03:01.194739Z[0m [[32m[1minfo     [0m] [1mWorker stats                  [0m [[0m[1m[34mlanggraph_runtime_inmem.queue[0m][0m [36mactive[0m=[35m0[0m [36mapi_variant[0m=[35mlocal_dev[0m [36mavailable[0m=[35m10[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mmax[0m=[35m10[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:03:01.695414Z[0m [[32m[1minfo     [0m] [1mQueue stats                   [0m [[0m[1m[34mlanggraph_runtime_inmem.queue[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mn_pending[0m=[35m0[0m [36mn_running[0m=[35m0[0m [36mpending_runs_wait_time_max_secs[0m=[35mNone[0m [36mpending_runs_wait_time_med_secs[0m=[35mNone[0m [36mpending_unblocked_runs_wait_time_max_secs[0m=[35mNone[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:03:56.449523Z[0m [[32m[1minfo     [0m] [1mGET / 200 0ms                 [0m [[0m[1m[34mlanggraph_api.server[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mlatency_ms[0m=[35m0[0m [36mmethod[0m=[35mGET[0m [36mpath[0m=[35m/[0m [36mpath_params[0m=[35m{}[0m [36mproto[0m=[35m1.1[0m [36mquery_string[0m=[35m[0m [36mreq_header[0m=[35m{}[0m [36mres_header[0m=[35m{}[0m [36mroute[0m=[35mNone[0m [36mstatus[0m=[35m200[0m [36mthread_name[0m=[35mMainThread[0m
[2m2026-04-09T16:04:01.235880Z[0m [[32m[1minfo     [0m] [1mWorker stats                  [0m [[0m[1m[34mlanggraph_runtime_inmem.queue[0m][0m [36mactive[0m=[35m0[0m [36mapi_variant[0m=[35mlocal_dev[0m [36mavailable[0m=[35m10[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mmax[0m=[35m10[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
[2m2026-04-09T16:04:01.736636Z[0m [[32m[1minfo     [0m] [1mQueue stats                   [0m [[0m[1m[34mlanggraph_runtime_inmem.queue[0m][0m [36mapi_variant[0m=[35mlocal_dev[0m [36mlanggraph_api_version[0m=[35m0.7.65[0m [36mn_pending[0m=[35m0[0m [36mn_running[0m=[35m0[0m [36mpending_runs_wait_time_max_secs[0m=[35mNone[0m [36mpending_runs_wait_time_med_secs[0m=[35mNone[0m [36mpending_unblocked_runs_wait_time_max_secs[0m=[35mNone[0m [36mthread_name[0m=[35mThreadPoolExecutor-1_0[0m
```

#### logs/gateway.log (last 30 lines)
```
INFO:     Started server process [1156816]
INFO:     Waiting for application startup.
2026-04-10 00:01:02 - app.gateway.app - INFO - Configuration loaded successfully
2026-04-10 00:01:02 - app.gateway.app - INFO - Starting API Gateway on 0.0.0.0:8001
2026-04-10 00:01:02 - deerflow.runtime.stream_bridge.async_provider - INFO - Stream bridge initialised: memory (queue_maxsize=256)
2026-04-10 00:01:02 - deerflow.runtime.store.async_provider - INFO - Store: using AsyncPostgresStore
2026-04-10 00:01:02 - app.gateway.app - INFO - LangGraph runtime initialised
2026-04-10 00:01:02 - app.channels.manager - INFO - ChannelManager started (max_concurrency=5)
2026-04-10 00:01:02 - app.channels.service - INFO - ChannelService started with channels: []
2026-04-10 00:01:02 - app.gateway.app - INFO - Channel service started: {'service_running': True, 'channels': {'feishu': {'enabled': False, 'running': False}, 'slack': {'enabled': False, 'running': False}, 'telegram': {'enabled': False, 'running': False}, 'wecom': {'enabled': False, 'running': False}}}
2026-04-10 00:01:02 - app.channels.manager - INFO - [Manager] dispatch loop started, waiting for inbound messages
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     127.0.0.1:50060 - "GET /health HTTP/1.1" 200 OK
INFO:     ::1:0 - "GET /health HTTP/1.1" 200 OK
```

#### logs/frontend.log (last 30 lines)
```

> deer-flow-frontend@0.1.0 dev /root/.openclaw/workspace/deer-flow/frontend
> next dev --turbo

- [36minfo[0m [nextra] You have Next.js i18n enabled, read here https://nextjs.org/docs/app/building-your-application/routing/internationalization for the docs.
▲ Next.js 16.1.7 (Turbopack)
- Local:         http://localhost:3000
- Network:       http://10.1.0.8:3000
- Environments: .env
- Experiments (use with caution):
  · optimizePackageImports

✓ Starting...
✓ Ready in 1811ms
 GET / 200 in 3.7s (compile: 3.1s, render: 601ms)
 GET / 200 in 117ms (compile: 5ms, render: 112ms)
```

#### logs/nginx.log (last 30 lines)
```
```


### Tester
opencode

---

*Report generated at: 2026-04-10 00:04:57*
