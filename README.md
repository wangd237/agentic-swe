# Agentic SWE

<img src="https://img.shields.io/badge/Python-3.10-blue" alt="Python">

![Pydantic](https://img.shields.io/badge/Pydantic-v2-purple)
![pytest](https://img.shields.io/badge/pytest-tested-blue)
![OpenAI Compatible](https://img.shields.io/badge/OpenAI_Compatible-API-purple)
![Tool Calling](https://img.shields.io/badge/Tool_Calling-enabled-green)
![CLI](https://img.shields.io/badge/CLI-supported-gray)
![JSON Trace](https://img.shields.io/badge/JSON_Trace-auditable-orange)
[![MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

一个面向真实 repo 的 bug repair coding agent —— 接收软件问题描述，在隔离 workspace 中理解问题、复现失败、定位代码、生成补丁、验证修复，并输出可审计结果。

## 核心结果

| 指标 | 结果 |
| --- | --- |
| Agent Core v1 状态 | `complete`，见 [currentTask.md](currentTask.md) |
| 核心工作流 | `UNDERSTAND -> REPRODUCE -> LOCALIZE -> PATCH -> VERIFY -> FINAL` |
| Agent core 回归测试 | `110 passed` |
| 用户入口验证 | `repair_bug.run_repair_bug()` 已覆盖 full verification 与 weak/static verification |
| 正式真实任务数 | `66` 条，覆盖 `16` 个开源生态 |
| 规则版 baseline 成功率 / 测试通过率 | `100%` / `100%`（策略 `improved_v71`） |
| LLM agent 全局成功率 | `91.3%`（`149` runs, `136` success） |
| Target 1 压力测试（stress subset） | `85.7%`（`14` hard tasks, `12` success） |
| Target 2 重点验证 | `3 / 3` success（`task_048 / task_030 / task_089`） |
| `frozen_40` 连续无回归版本数 | `8` |
| 展示案例 | `4` 条 case study，均有 trace / result / patch |

关键突破：`task_048` 从 `max_iterations` 领域语义盲区转为 success —— agent 通过受控 `python_repl` 查询真实行为后再做最小 patch。

完整评测见 [docs/agent_eval_summary.md](docs/agent_eval_summary.md)，case study 见 [docs/agent_case_studies.md](docs/agent_case_studies.md)。

## 与 SWE-bench 的区别

本项目不是 SWE-bench 的复现或包装。核心差异：

- **任务来源**：`66` 条 semi-real 任务来自多个开源生态的真实 issue，不是 SWE-bench 的离线数据集
- **可审计性**：每次 run 落盘 `trace.json` / `result.json` / `patch.diff`，可复盘 agent 每一步决策
- **baseline 对照**：规则版 baseline（`improved_v71`）作为稳定下限与 LLM agent 对比，不是只用 LLM 打分
- **回归保护**：冻结集 `frozen_40` + 稳定性复跑，保证策略迭代不会悄悄退化

## Agent Core v1

当前项目主线是 coding agent 本体，而不是 GitHub crawler、PR 自动化或 benchmark dashboard。Agent Core v1 已将原来的松散 ReAct tool loop 收束为阶段化状态机：

```text
UNDERSTAND -> REPRODUCE -> LOCALIZE -> PATCH -> VERIFY -> FINAL
```

核心能力：

- **显式 AgentState**：记录当前阶段、issue summary、failure signature、localization candidates、hypotheses、modified files、verification strength。
- **phase-aware tool policy**：不同阶段限制可用工具，禁止过早 `edit_file` / `write_file`，要求 patch 前具备复现或弱/静态证据和定位候选。
- **代码定位**：结合任务提示、失败摘要、搜索命中、AST symbol index、测试与实现 import 关系，产出候选文件和证据。
- **分级验证**：区分 `none` / `weak` / `targeted` / `full`，弱验证不能被报告为普通成功。
- **反思与自我纠错**：测试失败、定位低置信、修改过宽或弱验证时记录结构化 reflection，必要时自动 undo。
- **可审计 trace/metrics**：trace step 携带 `phase`、`state_snapshot`、`evidence_ids`、`reflection_type`、`verification_strength`，并输出 agent-core metrics。

## 用户入口

本地 repo bug repair 可以直接使用 `scripts/repair_bug.py`：

```bash
python scripts/repair_bug.py --repo path/to/local_repo --issue "描述你遇到的 bug" --test "python -m pytest -q"
```

如果不传 `--test`，脚本会自动发现 pytest；若没有测试目录或 pytest 配置，会进入 weak/static verification 路径。CLI summary 会明确打印：

```text
final_status:
verification_strength:
incomplete_reason:
pre_test_exit_code:
post_test_exit_code:
summary_path:
trace_path:
result_path:
```

这意味着 full verification 成功会与 `success_weak_verification` 明确区分，agent 不会把弱验证包装成普通成功。

## Agent Run Loop

```text
local repo + issue text / semi-real task / GitHub issue input
          |
          v
   task definition
          |
          v
   repo workspace 隔离复制
          |
          v
   phased agent loop（understand / reproduce / localize / patch / verify / final）
          |
          v
   轨迹与结果落盘（task.json / trace.json / result.json / patch.diff）
```

## 项目特点

**可审计的修复过程**
- 每次 run 落盘 `trace.json` / `result.json` / `patch.diff`，可复盘每一步决策
- 成功判定依赖 `run_tests` 和 `final_status`，不是让模型自称完成
- 测试失败后 agent 会看到 `context_diff`，避免只凭 pytest 断言盲改
- trace 中记录阶段、状态快照、证据 id、反思类型和验证强度

**工程严谨性**
- harness 一等公民：工作区隔离、路径边界、产物契约、批量复现
- 策略版本化到 `improved_v71`，冻结集 `frozen_40` 连续 `8` 个版本无回归
- 性能治理支持环境基线快照，拆分"环境变慢"和"策略变慢"
- challenge 集独立管理，不污染正式 benchmark 口径

**真实任务 & 多维度评测**
- 任务来自 `16` 个开源生态的真实 issue，非 synthetic demo
- 评测维度包括成功率、taxonomy、耗时、步数、稳定性复跑和 maturity 审计
- 规则版 baseline 作为稳定下限与 LLM agent 对照

**灵活的 LLM 接入**
- 通过 OpenAI-compatible tool calling 调用现有工具，当前使用 DeepSeek
- 可切换到 Kimi、GLM 等兼容服务
- 受控 `python_repl`：只允许单表达式，拒绝 import、分号、多行和 dunder

## 代表性案例

- `task_024` `pallets/jinja#2069` — 模板变量在分支赋值场景下的控制流语义分析
- `task_036` `python-jsonschema/jsonschema#1121` — 从"测试失败"到"异常回落语义修复"的典型优化路径
- `task_122` `fsspec/filesystem_spec#979` — `unstrip_protocol()` 在前缀保护场景下错误返回原路径
- `task_128` `agronholm/anyio#82` — 嵌套 task group 场景下 asyncio/curio backend 取消异常泄漏

完整任务索引见 [docs/benchmark_registry.md](docs/benchmark_registry.md)，challenge 集见 [docs/challenge_set.md](docs/challenge_set.md)。

## 快速开始

```bash
# 安装依赖
python -m pip install -r requirements.txt

# 配置 LLM provider
cp .env.example .env  # 填入 API key / base URL / model

# 运行 LLM agent
python scripts/run_issue_agent.py --task benchmarks/tasks/task_010.json --policy optimization/policy_versions/llm_deepseek_minimal.json

# 用户本地 repo bug repair
python scripts/repair_bug.py --repo path/to/local_repo --issue "AttributeError: 'NoneType' object has no attribute 'apply'" --test "python -m pytest -q"

# 规则版 baseline（对照用）
python scripts/run_single_task.py --task benchmarks/tasks/task_128.json --policy optimization/policy_versions/improved_v71.json

# 批量评测 + 稳定性检查 + maturity 审计
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v71.json --run-label frozen20_v71 --stability-check --stability-repetitions 3
```

说明：LLM agent 已接入阶段化 tool-use 闭环，输出预算默认 `8000` tokens。支持 DeepSeek / Kimi / GLM 等 OpenAI-compatible 服务，通过 `.env` 或环境变量配置。规则版入口仍保留用于 baseline 对照。

## 项目结构

```text
app/
  agent/        # agent loop、policy、patch strategy
  runtime/      # harness、workspace 隔离、批量运行
  schemas/      # Task / Trace / Result 的 pydantic schema
  tools/        # 文件、搜索、测试、写入、diff 工具
benchmarks/
  manifests/    # 正式集、challenge 集、冻结集
  repos/        # semi-real benchmark 仓库
  tasks/        # 任务定义
docs/           # 架构、评测、案例、路线图
evals/          # metrics、taxonomy、compare
logs/           # 运行轨迹与评测产物
optimization/   # policy 版本与优化记录
scripts/        # 单任务、批量评测、稳定性复跑等脚本
```

## 文档导航

- 2 分钟概要：[docs/one_pager.md](docs/one_pager.md)
- Agent 概览：[docs/agent_overview.md](docs/agent_overview.md)
- Agent 小样本评测：[docs/agent_eval_summary.md](docs/agent_eval_summary.md)
- Agent 案例：[docs/agent_case_studies.md](docs/agent_case_studies.md)
- 架构说明：[docs/architecture.md](docs/architecture.md)
- Harness 设计：[docs/harness.md](docs/harness.md)
- 任务注册表：[docs/benchmark_registry.md](docs/benchmark_registry.md)
- Challenge 说明：[docs/challenge_set.md](docs/challenge_set.md)
- 实验摘要：[docs/experiment_summary.md](docs/experiment_summary.md)
- V2 路线图：[docs/v2_roadmap.md](docs/v2_roadmap.md)
- 实施指南：[GUIDE.md](GUIDE.md)

## 技术栈

Python · Pydantic · pytest · OpenAI-compatible Chat Completions · subprocess 测试执行 · 文件级 patch/diff · manifest 驱动的 benchmark 管理

## 当前阶段

项目主角已切到 LLM coding agent core：它能在隔离 workspace 里读 issue、复现失败、定位候选、改文件、查看 diff、跑 targeted/full tests、落盘 trace。benchmark / frozen / stability 体系的角色是给 agent 提供可信验证层和 baseline 参照：

- ✅ LLM tool-use agent
- ✅ Agent Core v1 phase workflow
- ✅ full vs weak/static verification 区分
- ✅ 用户本地 repo repair 入口 smoke
- ✅ case study trace / result / patch 证据
- ✅ 正式集 + 冻结集 + 策略版本化
- ✅ 批量评测 + 稳定性复跑 + maturity 审计

后续重点：更多真实本地 repo 修复案例、精简 `llm_agent.py` 中重复的 post-patch verification 逻辑、以及在不偏离 agent core 的前提下扩展任务难度。

## License

MIT
