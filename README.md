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
- 实现 post-patch immediate auto-verification：代码修改后由 runtime 自动执行 `show_diff + targeted tests + full tests`，根据测试结果自动反思（reflection）并决定是否 undo，无需模型手动发起。
- 实现 auto-finalize：diff 已观察且 full `run_tests` 通过后自动退出 LLM 循环，避免冗余工具调用。
- 设计 Verification Quality Layer，结构化输出 `verification_evidence`、`evidence_quality`、`accepted_final_status`、`missing_evidence`，区分可信成功、本地 smoke、targeted-only、weak/static verification 和证据缺失。
- 双策略上下文工程：microCompact（单个超大 tool result 前置截断）+ 全量摘要压缩，在爆窗之前就控制上下文。
- 接入可选 `codebase-memory-mcp` code intelligence backend，在 `LOCALIZE` 阶段提供 graph-assisted localization hints + `search_graph` agent tool（UNDERSTAND/REPRODUCE/LOCALIZE 阶段可用，单次 run 限 3 次调用，无 backend 时自动降级），并记录 graph 可用性、索引成本、候选命中、fallback 和 A/B delta。
- 测试失败信息结构化提取 `failure_summary`（failed tests、断言位置、异常类型、possible symbols）+ 自动引导符号搜索，让模型不看完整日志也能定位根因。
- 反循环检测：连续 3 次类似写操作时自动注入提醒，避免模型在同方向上空转。
- 每次 run 落盘 `trace.json`、`result.json`、`summary.md`、`patch.diff`，可复盘 Agent 的工具调用、阶段状态、token 消耗、验证证据和最终验收结论。
- 支持 OpenAI-compatible API，可接入 DeepSeek / Kimi / GLM / Ollama / llama.cpp / LM Studio 等模型；涉及私有代码的真实 A/B 建议使用本地或受信内部 endpoint。

## 量化结果

| 指标 | 结果 |
| --- | --- |
| 任务规模 | `132` 条 semi-real 真实 issue + `10` 个 SWE-bench Lite 任务，覆盖 `25+` 开源生态 |
| LLM Agent 评测管道 | 4 级冻结集（15/18/20/40） + `evals/` 聚合/对比/错误分类 + `stability_recheck` flaky 验证 + `analyze_benchmark_maturity` 回归门禁 |
| 回归测试 | `367` passes |
| SWE-bench Lite 可运行 | `6 / 10 tasks`（覆盖 marshmallow / pydicom / astroid / pvlib / sqlfluff / pyvista）|
| Frozen set 稳定性 | `frozen_40` 连续 `72+` 个策略版本无回归 |
| Tool routing 优化 | `task_010` token `30,510 -> 18,553`，LLM 调用 `7 -> 5` |
| Auto-verification & reflection | 写入后自动执行 show_diff + targeted tests + full tests；失败时自动 failure-signature 比较 + 可选 undo |
| Anti-loop 检测 | 连续 3 次相似写操作时注入提醒 |
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
              （自动提取 failure_summary + 引导符号搜索）
        |
        v
LOCALIZE      搜索、读取文件、结合失败摘要和 AST symbol index 定位候选
              可选 codebase-memory-mcp graph hints 增强候选排序
        |
        v
PATCH         生成最小补丁，受 policy 限制写入范围
        |_______ (写入后自动验证 ←→ 失败时 reflection + undo)
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
- RunContext dataclass 封装全部 17 个局部变量 + 11 个闭包迁移为可测试的类方法（`auto_undo_after_reflection`、`run_immediate_auto_verification`、`compress_context_if_needed` 等）。
- 测试失败、定位低置信、修改过宽或弱验证时记录 reflection，用于后续修复决策。
- 反循环检测：连续 3 次相似写操作时注入提醒，防止模型在同一方向上空转。
- 阶段跳转提示：进入 PATCH 阶段时自动注入提示，提醒模型从”搜索理解”切换到”动手修改”。

**2. Tool Use & Routing**

- 工具包括文件读取、代码搜索、测试执行、patch 写入、diff 查看、undo、**代码结构搜索（search_graph）**、**受控 Python REPL（python_repl）**等。
- 根据阶段和状态动态筛选 tool schema，减少无关工具暴露，降低 token 成本和工具选择噪音。
- 工具属性（只读、并发安全、写入）在 `tool_definitions.py` 中单一数据源声明，`llm_agent`、`tool_policy`、`run_metrics` 从此导出，加新工具无需修改多个文件。
- 记录每次 run 的 tool calls、schema routing、LLM token usage，支持量化优化。

**3. 上下文工程**

- 双策略上下文压缩：在总字符超限前，对单个超大工具结果做前置截断（microCompact），再 fall through 到现有全量摘要压缩。
- 测试失败信息内置 `failure_summary` 结构化提取（failed tests、断言位置、异常类型、possible symbols），让模型不看完整日志也能定位失败根因。
- 自动引导失败搜索：从测试失败输出中提取符号名自动执行补充搜索，无需模型主动发起。

**4. Verification Quality**

项目不会只依赖模型说”修好了”，而是输出结构化验收结论：

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

### Verifier judgment pipeline

- `build_verification_evidence()`：收集 patch、pre-test、post-test、official harness 等维度
- `assess_evidence_quality()`：分类 evidence_quality 为 strong / partial / weak / missing
- `build_verifier_report()`：综合 verdict（risk_level + acceptance + caveats）
- `accepted_final_status_from_report()`：映射为产品可读的最终状态

### Auto-verification loop

写入工具成功后，runtime 自动执行三级验证链：

1. `show_diff` — 立即查看当前改动
2. `targeted run_tests` — 只跑之前失败过的测试（符号级定位）
3. `full run_tests` — 跑完整测试套件

验证结果与写入结果在同一轮回喂给模型。如果失败，系统自动比较 failure signature delta：

| delta | 判定 | 行为 |
|-------|------|------|
| unchanged | wrong_hypothesis / wrong_file | 自动 undo + 回 LOCALIZE |
| changed | partial_fix | 保留 patch，继续 PATCH |
| 新失败 | overfit / low_confidence | 建议缩小范围 |

**5. Code Intelligence / Graph-assisted Localization**

- 默认关闭，不影响 baseline agent 行为。
- 开启后通过 `codebase-memory-mcp` CLI 对隔离 workspace 建索引，并用 `search_graph` 生成定位候选；同时向 agent 暴露 `search_graph` tool，允许在 UNDERSTAND/REPRODUCE/LOCALIZE 阶段主动查询代码结构图（单次 run 限 3 次调用，无 backend 时自动降级）。
- graph hints 只作为 localization prior，不替代源码阅读和测试验证。
- trace/result 会记录 backend、binary、version、index/query cost、fallback reason、candidate rank、compact hints 和 graph hint 是否被 patch 使用。
- 当前 v16 评测已完成：graph-assisted localization 可降低 token（avg -258）、read_file（avg 0），tool call 无系统性增加，定位质量保持 source top1 8/8，无成功退化。

**6. Auditability**

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

- `task_010` `Textualize/rich#4090`：CRLF 跨平台换行符归一化，ANSI 行解析修复。
- `task_024` `pallets/jinja#2069`：模板变量在分支赋值场景下的控制流语义分析。
- `task_036` `python-jsonschema/jsonschema#1121`：从测试失败到异常回落语义修复。
- `task_048` `pypa/packaging#886`：从 `max_iterations` 失败到成功，Agent 通过受控 `python_repl` 查询真实行为后生成最小 patch。
- `task_093` `pallets/click#3572`：`color=False` 时复用 ANSI 清理逻辑，修复 confirm 输出泄漏控制码。
- `task_122` `fsspec/filesystem_spec#979`：`unstrip_protocol()` 在前缀保护场景下错误返回原路径。
- `task_128` `agronholm/anyio#82`：嵌套 task group 场景下 asyncio/curio backend 取消异常泄漏。
- `task_054` `pydantic/pydantic#9582`：edit_file + 结构化失败摘要帮助模型从中间错误收敛到正确 patch（`incomplete/max_iterations` → `success`）。

完整案例列表见 [docs/agent_case_studies.md](docs/agent_case_studies.md)。

## 项目结构

```text
app/
  agent/        # LLM agent、state、policy、tool routing、verification、reflection、code intelligence
    run_context.py    # 17 个局部变量 + 11 个闭包封装为 dataclass 方法
    verifier.py       # Verification Quality Layer：evidence / report / assessment
    run_metrics.py    # 行为指标计算（phase completion、pre-repro、undo recovery 等）
    summary.py        # CLI 摘要格式化
  runtime/      # workspace 隔离、run paths、日志落盘、git 工作区管理
  schemas/      # Task / Trace / Result schema
  tools/        # 文件、搜索、测试、写入、diff、python REPL 工具
benchmarks/
  tasks/        # 132 条 semi-real + 10 条 SWE-bench Lite task 定义
  repos/        # benchmark repos（含 swebench_lite 子目录）
  manifests/    # frozen set / evaluation manifests（9 个）
optimization/
  policy_versions/  # 80 个 policy 版本（baseline v1 ~ v72 + LLM 配置模板）
docs/           # 架构、评测、案例、路线图
evals/          # 批量评测、错误分类、指标计算、对比脚本
scripts/        # 60+ CLI 脚本：单任务运行、批量评测、本地/GitHub repo 修复、AB 实验、分析
.tools/         # codebase-memory-mcp binary（可选 code intelligence 后端）
logs/           # 运行轨迹、结果、patch、agent memory
third_project/  # 第三方任务源代码
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
