# Week Target：Agent 展示包可交付

**目标：把这个项目推到「可以放进简历 + 面试中打开给人看」的状态。**

## 背景

当前项目已经有 LLM agent 可审计成功案例、failure taxonomy、agent-first 的 README 和安全加固的代码。目标是把证据层补齐，让面试官打开项目后能快速验证「这个 agent 不是 demo，是认真做过的」。

## 4 个交付物

### 交付物 1：样本扩到 ≥25 条，补 `incomplete_reason`

起点是主样本 5 条全部成功，扩展 2 条成功 + 1 条 challenge 边界题保持 incomplete。样本量偏小且全是成功，缺乏失败诊断素材。

要做：
- 再跑其他任务，总量推到 ≥25 条
- 必须包含 ≥3 条 challenge 边界题（预期会失败或保持 incomplete）
- 在 `app/schemas/result_schema.py` 的 `Result` 中加 `incomplete_reason` 字段，枚举：`"no_patch"` / `"failed_tests"` / `"max_iterations"` / `"unverified_patch"`
- agent 循环 (`llm_agent.py`) 在非 success 结束时写入对应 reason
- 更新 `docs/agent_eval_summary.md` 的结果表

**⚠️ 不是 blind run：** 每跑完一批（5 条左右）就停下来检查 diff 质量，确认 patch 是真的修复而不是碰巧让测试通过。不要只看 `final_status` 就过。预估 17 条增量 × 每条 5-10 分钟检查 = 1.5-3 小时。

**⚠️ failure 多样性：** 跑完 challenge 后检查 `incomplete_reason` 分布。如果 3 条全是同一种 reason（比如都是 `max_iterations`），信息量低，应换一条能暴露不同失败原因的题。

### 交付物 2：case study 从 1 条补到 ≥4 条

当前 `docs/agent_case_studies.md` 只有 Case 1 有详细行为记录。

建议选取 3 条与现有 Case 1 最不相同的成功案例：
- `task_024`（jinja2 静态分析算法修复 — 需要理解控制流）
- `task_016`（click 行为回归 — 语义修复非崩溃）
- `task_093`（click ANSI 清理 — 输出处理）

每条 case study 必须包含：关键步骤序列、agent 决策关键点（为什么读那个文件、为什么选那个修复）、patch 核心改动、验证结果。

### 交付物 3：README 指标表有血有肉

当前 README Agent 能力表的数字还是 `1`。用 agent_eval_summary 里的真实数据替换。

Agent 能力表最终形态（早期示例，实际数字以当前追踪状态为准）：
```
| 可审计成功案例数 | 8 条 |
| 主样本成功率 | 80% (8/10) |
| 覆盖库数 | 4 个（rich, dateutil, jinja2, click） |
| 平均工具调用数 | 6.0 |
| 边界意识 | challenge 集 1 条正确保持 incomplete |
```

### 交付物 4：项目一键可跑 + `.env.example`

面试官 clone 下来应该能直接理解怎么跑。

要做：
- 新建 `.env.example`，包含所有 provider 需要的环境变量（注释掉值），附带说明
- 验证 `pip install -r requirements.txt` 后 `python scripts/run_issue_agent.py --task benchmarks/tasks/task_010.json --policy optimization/policy_versions/llm_deepseek_minimal.json` 能跑通
- README 快速开始段落与 `.env.example` 一致

## 验收标准

| 检查项 | 达标线 |
|--------|--------|
| LLM agent 跑过的任务数 | ≥ 25 |
| agent_eval_summary 里的成功率 | 如实（不是 100% 也不怕） |
| 失败 case 有 `incomplete_reason` | ≥ 2 种不同的 reason（不能全是同一种） |
| 所有成功 case 的 patch 已人工抽检 | diff 合理，非碰巧过测 |
| 详细 case study | ≥ 4 条 |
| README 核心指标 | 全是真实跑出来的数字，非占位符 |
| `.env.example` | 存在且内容完整 |
| focused tests | 全部通过 |
| `git status` | 干净 |

## 当前追踪状态

| 交付物 | 当前状态 | 证据 / 下一步 |
|--------|----------|---------------|
| 样本扩到 ≥25 条 | 已达标 | 当前已记录 `33` 条 LLM run（`29` success + `4` incomplete） |
| ≥3 条 challenge 边界题 | 已达标 | 当前已记录 `7` 条 challenge / boundary run：`task_126 / 127 / 130 / 131 / 132(old) / 132(new) / 133` |
| `incomplete_reason` | 已达标 | 当前已有 `no_patch` 与 `max_iterations` 两种 reason；`max_iterations` 来自 `llm_deepseek_max1` 受限策略 run |
| case study ≥4 条 | 已完成首版 | `docs/agent_case_studies.md` 已包含 `task_010 / task_024 / task_016 / task_093` 四条详细案例 |
| README 指标真实化 | 已完成首版 | README 已更新为 `33` 条真实 LLM run 指标 |
| `.env.example` | 已完成首版 | 已新增 `.env.example`，覆盖通用 OpenAI-compatible、DeepSeek、Kimi、GLM 变量 |
| README 快速开始一致性 | 已完成首版 | README 已提示复制 `.env.example` 并填 provider 配置 |
| 新增 patch 抽检 | 进行中 | 已抽检 `task_026 / 028 / 032 / 034 / 038 / 040 / 042 / 044 / 046 / 048 / 126 / 127 / 130 / 131 / 133 / 050 / 052 / 128 / 123 / 124 / 125 / 129`，未发现明显碰巧过测 |

## 不做

- 不加新的 benchmark 任务
- 不做 LLM Agent vs Rule Baseline 批量对比（小表可以保留）
- 不加 Anthropic SDK 适配器
- 不做 prompt 优化（除非跑新任务时发现明显问题）
- 不做 Reflection / multi-agent / Web UI
