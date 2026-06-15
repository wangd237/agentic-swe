# Target 1 Stress Test Report

日期：2026-06-15

目标：把当前 LLM coding agent 推到能力边界，确认哪些任务已经稳定可解、哪些失败来自模型能力、哪些失败可以通过 harness/prompt 改进缓解。

## 结论摘要

本轮使用 `llm_deepseek_minimal` 策略运行 `docs/weekTarget.md` 中列出的 14 条硬任务。早期草稿曾写作 15 条，但实际任务清单为 14 条，现已同步为 14 条口径。

- validation_id: `target1_stress_deepseek_14_002`
- policy_id: `llm_deepseek_minimal`
- listed tasks: `14`
- success: `12`
- incomplete: `2`
- error: `0`
- success rate: `85.71%`
- raw summary: `logs/summaries/target1_stress_deepseek_14_002.json`

最重要的信号：`task_132` 从历史上的 `incomplete/no_patch` 边界题变成了本轮成功修复，说明 git 工作区、planning、grep、智能截断等 harness 升级确实改善了 agent 的真实修复能力。

## 完整结果

| Task | 类型 | 状态 | Tool calls | 结果摘要 |
|------|------|------|------------|----------|
| `task_132` | rich Windows 编码边界 | success | 13 | 成功修改 `rich_windows_rule_repo/console.py`，目标测试通过 |
| `task_133` | rich Windows no_color | success | 6 | legacy Windows + no_color 分支修复，测试通过 |
| `task_075` | jinja2 async repr | success | 6 | 避免 async `length` 属性触发 coroutine warning，测试通过 |
| `task_089` | jinja2 map default | success | 7 | 区分 `default=None` 与未提供 default，测试通过 |
| `task_115` | pytest expression scanner | success | 6 | 只检查字符串字面量内部反斜杠，测试通过 |
| `task_101` | tomlkit out-of-order table | success | 7 | 重复 array table 聚合为列表，测试通过 |
| `task_030` | tomlkit inline table | incomplete | 13 | 已 patch，但格式多出换行，验证失败并触达 max iterations |
| `task_056` | sqlite-utils delete_where | success | 7 | delete 后自动 commit，测试通过 |
| `task_057` | pydantic validator 继承 | success | 9 | 父类/子类 validator 串联执行，测试通过 |
| `task_058` | attrs alias 字段转换 | success | 6 | transformer 前回填默认 alias，测试通过 |
| `task_097` | click progressbar | success | 7 | 完成态始终显示最终进度，测试通过 |
| `task_105` | pytest caplog filter | success | 7 | filter 引用计数支持嵌套，测试通过 |
| `task_109` | packaging name normalization | success | 6 | 正则匹配 canonicalize 输出，测试通过 |
| `task_048` | packaging specifier | incomplete | 13 | 已 patch 但误解 `Version.base_version`，验证失败并触达 max iterations |

## 失败分析

### 1. `task_030`：修复阶段失败

- run: `logs/trajectories/task_030/run_20260615T053708905100Z_0543/`
- final_status: `incomplete`
- incomplete_reason: `max_iterations`
- post_test_summary: `tests/test_formatter.py::InlineTableFormatterTests::test_append_key_preserves_spacing_in_dotted_inline_table`

Agent 很快定位到缺少 `, ` 分隔符，也正确把 `broken_body` 改为 `fixed_body`。失败点在修复细节：返回值被写成：

```python
return f"{prefix}{fixed_body}\n{suffix}\n"
```

而测试期望是单行 inline table：

```python
"a = {b.c = 1, d = 2}\n"
```

判定：模型修复阶段失误，主要是实现细节边界，不是定位能力问题。

Harness 信号：`run_tests` 摘要只给出了失败测试和行号，缺少断言实际值。模型没有马上看到“多出来的换行和 `}`”这种关键差异，浪费了后续轮次。

改进优先级：P1。已改进 `run_tests` 的 `failure_summary`，新增 `output_excerpt`，保留失败输出尾部片段，让 unittest/pytest 的实际值差异能回喂给模型。

### 2. `task_048`：模型语义理解失败 + 临时文件污染

- run: `logs/trajectories/task_048/run_20260615T053902344484Z_3006/`
- final_status: `incomplete`
- incomplete_reason: `max_iterations`
- modified_files: `debug.py`, `packaging_specifier_repo/specifiers.py`
- post_test_summary: `tests/test_specifiers.py::SpecifierContainsTests::test_larger_dev_with_local_is_greater`

Agent 识别到了 `local` version 的特殊分支，但误以为 `Version(...).base_version` 能表达 dev 段大小。实际 `base_version` 会丢掉 prerelease/dev/local 细节，因此 `4.1.0a2.dev1235+local` 与 `4.1.0a2.dev1234` 的 base_version 都会退化到 `4.1.0`，导致修复仍然返回 `False`。

判定：核心是模型对 packaging 版本语义的理解不足；同时 harness/prompt 暴露两个可改点。

Harness 信号：
- 失败摘要缺少 `AssertionError: False is not true` 等短上下文，不利于模型快速看到实际返回值。
- Agent 创建了 `debug.py` 探针文件，但没有清理，导致最终 patch 带上无关文件。

改进优先级：P1/P2。已完成两项改进：
- `run_tests` failure summary 增加 `output_excerpt`。
- system prompt 明确要求不要把 `debug.py`、`tmp.py`、`scratch.py` 等临时调试文件留在最终 patch 中；若写入临时探针，应尽快 `undo`。

### 3. `task_132` 早期 no_patch：验证/状态判定边界

- failed run: `logs/trajectories/task_132/run_20260615T053313434663Z_7142/`
- later success run: `logs/trajectories/task_132/run_20260615T053443547474Z_9294/`

同一压力测试阶段中，`task_132` 先出现一次 `incomplete/no_patch`：测试通过但没有 patch，agent 认为代码已经满足需求，于是未生成变更。随后复跑成功生成 `rich_windows_rule_repo/console.py` patch，目标测试通过。

判定：这是验证阶段/状态判定边界，不应把“测试已经通过但没有实际改动”标成 success。当前分类保持保守是正确的。

Harness 信号：这个案例对面试展示很有价值。它说明 agent 的 success 不是只看测试绿，而是同时要求有 patch 和当前 generation 的验证证据。后续可以把它写入 case study，说明项目对“假阳性成功”的防御。

改进优先级：P2。无需立即修改成功判定；需要在报告和展示层明确这类边界。

## 能力边界

当前 agent 对以下场景表现好：

- 单文件、小范围语义 bug：`task_089`, `task_097`, `task_109`
- 测试驱动的明确回归：`task_056`, `task_058`, `task_105`
- 需要读测试 + 读目标实现 + 精确 edit 的任务：多数 6-9 tool calls 完成
- 历史 hard case 突破：`task_132`

当前 agent 的边界主要在：

- 需要精确理解领域库语义的任务：`task_048` 的 packaging version 规则
- 输出格式非常精细的任务：`task_030` 的 inline table 单行格式
- 失败摘要过短时，模型容易在错误实现上反复验证，直到 max iterations
- 临时调试文件需要更强约束，否则会污染最终 patch

## 已落地改进

本轮压力测试后已完成一项 harness 改进和一项 prompt 改进：

1. `app/tools/run_tests.py`
   - `failure_summary` 增加 `output_excerpt`
   - 保留失败输出尾部片段，补足 unittest/pytest 断言实际值
   - 相关测试：`test_build_failure_summary_includes_output_excerpt_for_unittest_failures`

2. `app/agent/llm_prompts.py`
   - 明确约束临时调试文件不得留在最终 patch 中
   - 指导 agent 写入临时探针后用 `undo` 清理
   - 相关测试：`test_system_prompt_discourages_leaking_scratch_files`

验证命令：

```powershell
python -m pytest tests\test_runtime_diagnostics.py tests\test_llm_agent.py -q --basetemp .pytest_tmp_target1_narrow
```

结果：`26 passed`

## 后续方向

Target 1 还剩两个收口动作：

- 跑全量 `pytest -q`，确保 harness 改动没有回归。
- 将本轮发现追加到本地 `docs/agent_evolution.md`，并保持该文件不进入 Git。

Target 2 应继续围绕“agent 模型无关”推进：实现多模型批量脚本，使用 DeepSeek/Kimi/GLM 跑 frozen_40，产出跨模型对比，而不是继续扩 benchmark 数量。
