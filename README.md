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

这个项目聚焦 Agent 开发岗最核心的能力：**tool use、workflow control、state management、verification、traceability、evaluation**。

## 项目亮点

- 构建阶段化 Coding Agent workflow：`UNDERSTAND -> REPRODUCE -> LOCALIZE -> PATCH -> VERIFY -> FINAL`。
- 实现 phase-aware tool policy，限制不同阶段可调用工具，避免过早改文件、跳过复现或弱验证误报成功。
- 实现 phase/state-aware tool routing，LLM 每轮只接收当前阶段必要工具 Schema；在 `task_010` 上 token 从 `30,510` 降至 `18,553`，LLM 调用从 `7` 次降至 `5` 次。
- 实现 post-patch immediate verification：代码修改后由 runtime 自动执行 `show_diff + run_tests`，降低模型遗漏验证步骤的风险。
- 设计 Verification Quality Layer，结构化输出 `verification_evidence`、`evidence_quality`、`accepted_final_status`、`missing_evidence`，区分可信成功、本地 smoke、targeted-only、weak/static verification 和证据缺失。
- 每次 run 落盘 `trace.json`、`result.json`、`summary.md`、`patch.diff`，可复盘 Agent 的工具调用、阶段状态、token 消耗、验证证据和最终验收结论。
- 支持 OpenAI-compatible API，可接入 DeepSeek / Kimi / GLM 等模型。

## 量化结果

| 指标 | 结果 |
| --- | --- |
| 任务规模 | `66` 条 semi-real 真实 issue，覆盖 `16` 个开源生态 |
| LLM Agent 全局成功率 | `91.3%`（`149` runs，`136` success） |
| Stress subset 成功率 | `85.7%`（`14` hard tasks，`12` success） |
| Tool routing 优化 | `task_010` token `30,510 -> 18,553`，LLM 调用 `7 -> 5` |
| Agent core 回归测试 | `115 passed` |
| Frozen set 稳定性 | `frozen_40` 连续 `8` 个版本无回归 |
| 重点验证任务 | `task_048 / task_030 / task_089` 均成功 |

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

- 工具包括文件读取、代码搜索、测试执行、patch 写入、diff 查看、undo 等。
- 根据阶段和状态动态筛选 tool schema，减少无关工具暴露，降低 token 成本和工具选择噪音。
- 记录每次 run 的 tool calls、schema routing、LLM token usage，支持量化优化。

**3. Verification Quality**

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

**4. Auditability**

每次运行都会输出：

- `trace.json`：完整工具调用、阶段状态、证据 id、reflection 信息。
- `result.json`：最终状态、测试结果、token 消耗、verification evidence。
- `summary.md`：面向用户的简洁结果。
- `patch.diff`：本次修改内容。

## 快速开始

```bash
# 安装依赖
python -m pip install -r requirements.txt

# 配置模型
cp .env.example .env
# 填入 API key / base URL / model

# 运行 semi-real benchmark task
python scripts/run_issue_agent.py \
  --task benchmarks/tasks/task_010.json \
  --policy optimization/policy_versions/llm_deepseek_minimal.json

# 修复用户本地 repo
python scripts/repair_bug.py \
  --repo path/to/local_repo \
  --issue "AttributeError: 'NoneType' object has no attribute 'apply'" \
  --test "python -m pytest -q"
```

CLI 会直接打印 verification quality 字段，用户无需打开 JSON 也能判断本次结果是否可信：

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
  agent/        # LLM agent、state、policy、tool routing、verification
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

## License

MIT
