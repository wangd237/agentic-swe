# Agentic SWE

<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python"></a>
<a href="https://docs.pydantic.dev/"><img src="https://img.shields.io/badge/Pydantic-v2-purple?logo=pydantic&logoColor=white" alt="Pydantic"></a>
<a href="https://docs.pytest.org/"><img src="https://img.shields.io/badge/pytest-tested-blue?logo=pytest&logoColor=white" alt="pytest"></a>
<a href="https://platform.openai.com/"><img src="https://img.shields.io/badge/OpenAI_Compatible-API-purple?logo=openai&logoColor=white" alt="OpenAI Compatible"></a>
<a href="#"><img src="https://img.shields.io/badge/Tool_Calling-enabled-green" alt="Tool Calling"></a>
<a href="#"><img src="https://img.shields.io/badge/CLI-supported-gray" alt="CLI"></a>
<a href="#"><img src="https://img.shields.io/badge/JSON_Trace-auditable-orange" alt="JSON Trace"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green" alt="MIT"></a>

面向真实代码仓库的 **AI Bug Repair Agent**。输入一个 issue 或本地 repo 的 bug 描述，Agent 会在隔离 workspace 中完成问题理解、失败复现、代码定位、补丁生成、测试验证，并输出可审计的修复结果。

核心目标是把 LLM 从“直接生成代码”约束进可控的工程闭环：**tool use、workflow control、state management、verification、traceability、evaluation**。

## 项目亮点

- 构建阶段化 Coding Agent workflow：`UNDERSTAND -> REPRODUCE -> LOCALIZE -> PATCH -> VERIFY -> FINAL`。
- 实现 phase-aware tool policy，限制不同阶段可调用工具，避免过早改文件、跳过复现或弱验证误报成功。
- 实现 phase/state-aware tool routing，LLM 每轮只接收当前阶段必要工具 Schema；在 `task_010` 上 token 从 `30,510` 降至 `18,553`，LLM 调用从 `7` 次降至 `5` 次。
- 实现 post-patch immediate verification：代码修改后由 runtime 自动执行 `show_diff + run_tests`，降低模型遗漏验证步骤的风险。
- 设计 Verification Quality Layer，结构化输出 `verification_evidence`、`evidence_quality`、`accepted_final_status`、`missing_evidence`，区分可信成功、本地 smoke、targeted-only、weak/static verification 和证据缺失。
- 接入可选 `codebase-memory-mcp` code intelligence backend，在 `LOCALIZE` 阶段提供 graph-assisted localization hints + `search_graph` agent tool（UNDERSTAND/REPRODUCE/LOCALIZE 阶段可用，单次 run 限 3 次调用，无 backend 时自动降级），并记录 graph 可用性、索引成本、候选命中、fallback 和 A/B delta。
- 增加 post-verification auto-finalize：当前 workspace generation 已 `show_diff` 且 full `run_tests` 通过后自动收束，避免模型继续发起多余 `show_diff/read_file/run_tests` 探索。
- 每次 run 落盘 `trace.json`、`result.json`、`summary.md`、`patch.diff`，可复盘 Agent 的工具调用、阶段状态、token 消耗、验证证据和最终验收结论。
- 支持 OpenAI-compatible API，可接入 DeepSeek / Kimi / GLM / Ollama / llama.cpp / LM Studio 等模型；涉及私有代码的真实 A/B 建议使用本地或受信内部 endpoint。

## 量化结果

| 指标 | 结果 |
| --- | --- |
| 任务规模 | `66` 条 semi-real 真实 issue，覆盖 `16` 个开源生态 + `10` 个 SWE-bench Lite 任务 |
| LLM Agent 全局成功率 | `91.3%`（`149` runs，`136` success） |
| Stress subset 成功率 | `85.7%`（`14` hard tasks，`12` success） |
| Tool routing 优化 | `task_010` token `30,510 -> 18,553`，LLM 调用 `7 -> 5` |
| Agent core 回归测试 | `82+ passed`（总 `367` 测试） |
| SWE-bench Lite 可运行 | `6 / 10 tasks`（覆盖 marshmallow / pydicom / astroid） |
| Frozen set 稳定性 | `frozen_40` 连续 `8` 个版本无回归 |
| 重点验证任务 | `task_048 / task_030 / task_089` 均成功 |
| v16 code intelligence | `accepted` — graph-assisted localization 量化验证通过：token `-258` avg, read_file `0`, source top1 `8/8`, fallback `0%`, 无 success/accepted regression |
| `search_graph` agent tool | 模型主动查询代码结构图；Click #2894 修复后：grep `-67%`，token `-22%`，总调用 `-24%`，稳定进入 PATCH 阶段 |

完整评测见 [docs/agent_eval_summary.md](docs/agent_eval_summary.md)，代表案例见 [docs/agent_case_studies.md](docs/agent_case_studies.md)。

## Agent Workflow

```text
issue / local repo bug report
        |
        v
UNDERSTAND    解析问题、提取失败线索、建立初始状态
        |
        v
REPRODUCE     运行测试或最小复现，记录 pre-test evidence
        |
        v
LOCALIZE      搜索、读取文件、结合失败摘要和 AST symbol index 定位候选
              可选 codebase-memory-mcp graph hints 增强候选排序
        |
        v
PATCH         生成最小补丁，受 policy 限制写入范围
        |
        v
VERIFY        自动 show_diff + run_tests，记录 post-test evidence
        |
        v
FINAL         输出 result / trace / patch / verification summary
```

核心设计不是让模型“自由聊天式修代码”，而是把修复任务拆成可约束、可验证、可审计的阶段。

## 核心能力

**1. Agent State & Control**

- 显式维护 `AgentState`：阶段、issue summary、failure signature、localization candidates、modified files、verification strength。
- `ToolPolicy` 约束工具调用顺序，禁止没有复现或定位证据时直接改文件。
- 测试失败、定位低置信、修改过宽或弱验证时记录 reflection，用于后续修复决策。

**2. Tool Use & Routing**

- 工具包括文件读取、代码搜索、测试执行、patch 写入、diff 查看、undo、**代码结构搜索（search_graph）** 等。
- 根据阶段和状态动态筛选 tool schema，减少无关工具暴露，降低 token 成本和工具选择噪音。
- 记录每次 run 的 tool calls、schema routing、LLM token usage，支持量化优化。

**3. Code Intelligence / Graph-assisted Localization**

- 默认关闭，不影响 baseline agent 行为。
- 开启后通过 `codebase-memory-mcp` CLI 对隔离 workspace 建索引，并用 `search_graph` 生成定位候选；同时向 agent 暴露 `search_graph` tool，允许在 UNDERSTAND/REPRODUCE/LOCALIZE 阶段主动查询代码结构图（单次 run 限 3 次调用，无 backend 时自动降级）。
- graph hints 只作为 localization prior，不替代源码阅读和测试验证。
- trace/result 会记录 backend、binary、version、index/query cost、fallback reason、candidate rank、compact hints 和 graph hint 是否被 patch 使用。
- 当前 v16 评测已完成：graph-assisted localization 可降低 token（avg -258）、read_file（avg 0），tool call 无系统性增加，定位质量保持 source top1 8/8，无成功退化。

**4. Verification Quality**

项目不会只依赖模型说“修好了”，而是输出结构化验收结论：

```text
final_status: success
accepted_final_status: accepted_success
verification_level: full_verification_success
evidence_quality: strong
missing_evidence: none
```

对于 SWE-bench Lite local smoke，系统会明确标记：

```text
accepted_final_status: local_smoke_success
evidence_quality: partial
missing_evidence: official_harness
```

这避免把本地 smoke 误报成 official benchmark resolved，也避免把 weak/static verification 包装成可信成功。

**5. Auditability**

每次运行都会输出：

- `trace.json`：完整工具调用、阶段状态、证据 id、reflection 信息。
- `result.json`：最终状态、测试结果、token 消耗、verification evidence。
- `summary.md`：面向用户的简洁结果。
- `patch.diff`：本次修改内容。

## 快速开始

### 1. 安装与模型配置

```bash
# 安装依赖
python -m pip install -r requirements.txt

# 配置模型
cp .env.example .env
# 填入 API key / base URL / model
```

默认策略使用 OpenAI-compatible API，示例策略为：

```text
optimization/policy_versions/llm_deepseek_minimal.json
```

如果要处理私有代码或运行真实 A/B，建议使用本地或受信内部 OpenAI-compatible endpoint。外部公网 provider 可能会因代码、trace、diff 外发而被安全策略阻断。

本机 Ollama / llama.cpp / LM Studio 示例：

```env
DEEPSEEK_BASE_URL=http://127.0.0.1:8000/v1
DEEPSEEK_MODEL=qwen2.5-coder:7b-instruct
DEEPSEEK_API_KEY=local
```

当前普通 32GB 内存、无独显机器建议先用 `Qwen2.5-Coder-7B-Instruct` 跑通流程；`14B` 更接近真实修复能力，但 CPU-only 会明显占用电脑资源，适合夜间或低负载时尝试。

### 2. 跑一个内置 benchmark task

适合快速验证 Agent 的完整链路是否可运行：

```bash
python scripts/run_issue_agent.py \
  --task benchmarks/tasks/task_010.json \
  --policy optimization/policy_versions/llm_deepseek_minimal.json
```

### 3. 运行 code intelligence A/B preflight

`codebase-memory-mcp` 是可选增强后端。正式 A/B 会调用 LLM 并可能发送 issue、代码片段、tool outputs、diff 和 trace；请先确认 `.env` 指向本地或受信内部 endpoint。

```bash
python scripts/run_code_intelligence_ab.py \
  --manifest benchmarks/manifests/real_issue_tasks_frozen_15_v1.json \
  --tasks-dir benchmarks/tasks \
  --baseline-policy optimization/policy_versions/llm_deepseek_minimal.json \
  --cohort-label v16_frozen15_local_preflight \
  --codebase-memory-binary .tools/codebase-memory-mcp/codebase-memory-mcp.exe \
  --limit 8 \
  --preflight-only \
  --confirm-external-llm-data
```

正式 A/B 通过 `--require-v16-acceptance` 启用验收 gate：

```bash
python scripts/run_code_intelligence_ab.py \
  --manifest benchmarks/manifests/real_issue_tasks_frozen_15_v1.json \
  --tasks-dir benchmarks/tasks \
  --baseline-policy optimization/policy_versions/llm_deepseek_minimal.json \
  --cohort-label v16_frozen15_local \
  --codebase-memory-binary .tools/codebase-memory-mcp/codebase-memory-mcp.exe \
  --limit 8 \
  --confirm-external-llm-data \
  --require-v16-acceptance
```

exit code 语义：

```text
0: 真实 A/B 已完成，且 v16_acceptance.accepted == true
2: preflight 阻断，未启动真实 A/B
3: 真实 A/B 已完成，但 v16_acceptance.accepted != true
```

### 4. 修复本地 repo

如果代码仓库已经在本机，直接传本地路径：

```bash
python scripts/repair_bug.py \
  --repo path/to/local_repo \
  --issue "AttributeError: 'NoneType' object has no attribute 'apply'" \
  --test "python -m pytest -q"
```

`--test` 是验证命令。若不传，脚本会尝试自动发现 pytest；如果没有测试目录或 pytest 配置，会进入 weak/static verification 路径，并在 CLI 中明确标出验证强度不足。

### 5. 修复 GitHub 远程 repo

如果要让 Agent 处理公开 GitHub 仓库，有两种常用方式。

第一种是手动提供 repo URL 和 bug 描述。脚本会先把远程仓库 clone 到 `logs/github_repos/` 下的临时目录，然后基于这份本地副本创建隔离 workspace，再执行理解、复现、定位、修改和验证流程：

```bash
python scripts/repair_bug.py \
  --repo https://github.com/owner/repo \
  --issue "Describe the bug and expected behavior" \
  --test "python -m pytest -q"
```

第二种是直接提供公开 GitHub issue URL。此时不需要额外传 `--repo`，脚本会自动：

- 解析 issue 对应的 owner / repo；
- clone 对应 GitHub repo；
- 通过 GitHub public API 拉取 issue title/body；
- 生成一次用户 repair task；
- 运行 Agent 并输出 trace/result/patch。

```bash
python scripts/repair_bug.py \
  --issue-url https://github.com/owner/repo/issues/123 \
  --test "python -m pytest -q"
```

这两种方式都不会直接 push 到原始远程仓库。修复结果会以本地运行产物的形式输出，包括 `summary.md`、`result.json`、`trace.json` 和 `patch.diff`；你可以先审查 patch，再决定是否手动提交到自己的分支或 PR。

如果 issue 描述还不够具体，也可以同时追加 `--issue` 作为额外上下文：

```bash
python scripts/repair_bug.py \
  --issue-url https://github.com/owner/repo/issues/123 \
  --issue "Additional reproduction notes or expected behavior" \
  --test "python -m pytest -q"
```

运行结束后，CLI 会打印 verification quality 字段，用户无需打开 JSON 也能判断本次结果是否可信：

```text
final_status:
accepted_final_status:
verification_strength:
verification_level:
evidence_quality:
missing_evidence:
verifier_accepted:
risk_level:
llm_total_tokens:
summary_path:
trace_path:
result_path:
```

## 代表案例

- `task_024` `pallets/jinja#2069`：模板变量在分支赋值场景下的控制流语义分析。
- `task_036` `python-jsonschema/jsonschema#1121`：从测试失败到异常回落语义修复。
- `task_048`：从 `max_iterations` 失败到成功，Agent 通过受控 `python_repl` 查询真实行为后生成最小 patch。
- `task_122` `fsspec/filesystem_spec#979`：`unstrip_protocol()` 在前缀保护场景下错误返回原路径。
- `task_128` `agronholm/anyio#82`：嵌套 task group 场景下 asyncio/curio backend 取消异常泄漏。

## 项目结构

```text
app/
  agent/        # LLM agent、state、policy、tool routing、verification、code intelligence
  runtime/      # workspace 隔离、run paths、日志落盘
  schemas/      # Task / Trace / Result schema
  tools/        # 文件、搜索、测试、写入、diff 工具
benchmarks/
  tasks/        # semi-real / SWE-bench Lite task 定义
  repos/        # benchmark repos
  manifests/    # frozen set / evaluation manifests
docs/           # 架构、评测、案例、路线图
evals/          # metrics、taxonomy、对比脚本
scripts/        # CLI、单任务运行、批量评测、用户 repo 修复
```

## 技术栈

Python · Pydantic · pytest · OpenAI-compatible API · Tool Calling · subprocess sandboxed test execution · JSON Trace · CLI

## 文档导航

- 2 分钟概要：[docs/one_pager.md](docs/one_pager.md)
- Agent 概览：[docs/agent_overview.md](docs/agent_overview.md)
- Agent Core 能力地图：[docs/agent_core_capability_map.md](docs/agent_core_capability_map.md)
- 评测摘要：[docs/agent_eval_summary.md](docs/agent_eval_summary.md)
- 案例分析：[docs/agent_case_studies.md](docs/agent_case_studies.md)
- 架构说明：[docs/architecture.md](docs/architecture.md)
- Harness 设计：[docs/harness.md](docs/harness.md)
- 任务注册表：[docs/benchmark_registry.md](docs/benchmark_registry.md)
- 当前任务状态：[currentTask.md](currentTask.md)

## License

MIT
