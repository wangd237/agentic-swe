# Failure Analysis — 失败 run 归因

> 目的：对失败 run 做逐条归因，识别可复现的失败模式，为下一步改进提供依据。
> 纪律：每条归因标注验证深度（trace 级 / summary 级），不夸大结论。

## 1. 真实 GitHub issue 失败：pallets/click#3449

**验证深度：trace 级**（逐 step 读取 `trace.json`）

### Run 概况

| 指标 | 值 |
| --- | --- |
| task | `user_repo_i_o_operation_on_closed_file_err_20260830T065747Z` |
| issue | [pallets/click#3449](https://github.com/pallets/click/issues/3449)（CliRunner + `echo_via_pager` 报 "I/O operation on closed file"） |
| final_status | `incomplete / max_iterations` |
| LLM 轮次 | 16 / 16（打满） |
| 工具调用 | 24 次：`read_file` ×17，`grep` ×5，`list_files` ×1，`search_code` ×1 |
| `run_tests` 调用 | **0 次** |
| 写入调用 | 0 次 |
| token | 198,917 |
| phase 轨迹 | understand → reproduce → patch（step 9）→ final |

### 定位层工作正常

模型读取的三个文件——`src/click/testing.py`、`src/click/termui.py`、`src/click/_termui_impl.py`——正是该 bug 的全部现场（issue 指出的 `get_pager_file` 位于 `_termui_impl.py`）。初始候选排序（`initial_candidate_ranking`）第一步就命中 `src/click/testing.py`。

### 失败模式：探索预算耗尽（"完美主义读者"）

16 轮全部用于读代码，没有一次跑测试、没有一次写入。issue 正文自带 reproducer，模型未用 `python_repl` 执行，也未用 `run_tests` 验证——`has_reproduction_evidence` 全程为 `False`。模型试图在写 patch 前完全理解 `CliRunner.isolation`、`echo_via_pager`、`get_pager_file` 三者的交互语义，预算耗尽在理解完成之前。

### 系统级发现（三个缺口 + 一个小 bug）

1. **phase hint 单次注入，模型无视**。step 9 的 `read_file` 触发 reproduce → patch 转换，hint 拼进当轮 tool_result 发给模型（已验证代码路径：`llm_agent.py:1628-1639`）。此后模型又读了 12 轮文件。对比写入侧的反循环检测（连续 3 次相似写操作触发提醒），**读操作没有任何节流机制**。
2. **重叠读无检测**。`testing.py` 被读取 6 段：317-596、399-596、460-596、520-596、596-660、660-742——前四段几乎完全重叠；`_termui_impl.py` 同样存在重叠区间。系统对重复 search 有去重（`searched_queries`），对重叠读没有。17 次 `read_file` 是 19.9 万 token 的主要去向。
3. **无预算告警**。第 12/16 轮时 0 次写入，系统没有"停止探索、总结发现、立即写 patch"的升级干预。模型探索到死。
4. **附带小 bug**：`code_locator.py:200` 的 `reason=f"existing:{candidate.reason}"` 每次刷新再包一层前缀，trace 中 reason 字段出现 `existing:` 前缀重复 24 次。无害，但污染 trace 可读性。

### Verification layer 行为正确

`evidence_quality: missing`、`accepted_final_status: not_accepted`、`risk_level: high`、`missing_evidence: patch, pre_test, post_test, full_verification`。系统没有把 19.9 万 token 的空转包装成任何形式的"部分成功"——失败得诚实。

### 与 SWE-bench 失败的交叉印证

`sqlfluff__sqlfluff-1625`（16 轮全部用于读代码，未产出 patch）与本次 click#3449 构成**同一失败模式的两个独立实例**。这不是偶然，是当前系统在真实仓库上的稳定失败模式。

## 2. SWE-bench Lite 官方 harness 失败归因

**验证深度：summary 级**（来自 `evidence/swebench_lite_official/README.md` 与官方报告，未逐条读 trace）

| Instance | 结果 | 归因（summary 级） |
| --- | --- | --- |
| `pydicom__pydicom-1139` | unresolved | 修复引入 pass_to_pass 回归（`test_next` 挂）。本地 smoke 通过但官方判回归——verification quality layer 区分 local smoke 与 official 的设计在此得到验证 |
| `pvlib__pvlib-python-1072` | unresolved | 修复不完整 |
| `pylint-dev__astroid-1196` | unresolved | 修复不完整 |
| `pylint-dev__astroid-1268` | unresolved | 修复不完整 |
| `pylint-dev__astroid-1866` | error | 官方环境镜像构建失败（repo 自身 setup 问题），非 agent 责任 |
| `pyvista__pyvista-4315` | 未提交 | 3 次修改均被 reflection 判 `wrong_file` 回滚，未产出 patch。待 trace 级确认：reflection 误判还是真 wrong_file |
| `sqlfluff__sqlfluff-1625` | 未提交 | 16 轮全部用于读代码，未产出 patch。**与 click#3449 同模式** |

## 3. 失败模式分类

| 模式 | 实例 | 根因层 | 状态 |
| --- | --- | --- | --- |
| 探索预算耗尽 | click#3449、sqlfluff-1625 | 系统缺口（读无节流/无预算告警） | 已归因，待改进 |
| 修复引入回归 | pydicom-1139 | 模型能力（patch 质量不足） | 已被 verification layer 正确标记 |
| 修复不完整 | pvlib-1072、astroid-1196、astroid-1268 | 模型能力 | 待 trace 级归因 |
| reflection 回滚误判？ | pyvista-4315 | 待定（reflection 判定质量） | 待 trace 级归因 |
| 环境失败 | astroid-1866 | 官方镜像 | 非 agent 责任 |

## 4. 改进方向（按优先级）

1. **读操作节流**：连续 N 次读操作后注入提醒（对称于写入侧反循环检测），约 20-30 行。
2. **重叠读检测**：对与已读区间高度重叠的 `read_file` 注入提示或直接返回缓存摘要，约 30-40 行。
3. **预算升级干预**：轮次达 75% 且 0 写入时，注入"总结发现 + 立即写 patch"的强制指令，约 20 行。
4. **reason 前缀修复**：`code_locator.py:200` 改为不重复包裹，1 行。

改进前提：先在更多真实 issue 上验证"探索预算耗尽"模式的稳定性（当前 2 个独立实例），避免单例驱动开发。

## 5. 已实施的改进（2026-08-30）

基于三次真实 issue 失败的 trace 级归因，实施三个改进（commit 见 git log）：

| 改进 | 背景 | 实现 | 回归测试 |
| --- | --- | --- | --- |
| **环境预检** | jsonschema#1328 run3 烧 29.7 万 token 才发现 attrs 缺失 | `repair_bug.py` 启动时跑 `pytest --collect-only`，失败直接报错退出；exit=5（no tests）不拦截（weak fallback 合法路径） | `test_preflight_test_command_*` ×3 |
| **重复搜索拦截** | run3 中同一 pattern 在相同 glob 下搜 2 次、不同 glob 共 4 次 | `ToolExecutor` 维护 `(工具, pattern, glob)` 缓存，重复调用返回拦截提醒 + 上次命中文件 | `test_llm_agent_intercepts_duplicate_search_queries` |
| **预算升级干预** | click#3449 与 run3 共同模式：前 25% 预算理解根因，剩余 75% 探索到死 | 轮次 ≥75% 且 0 写入时，拼入最后一条 user 消息：强制总结根因 + 立即写 patch | `test_llm_agent_injects_budget_escalation_at_75_percent_without_writes` |

设计决策记录：

- 预算升级消息拼进最后一条 user 消息尾部而非新增独立消息——避免 user→user 连续消息（部分 API 不容忍），也避免隔断 assistant(tool_calls) 与 tool_result 配对（war story 6 教训）。
- 重复搜索拦截在 ToolExecutor 层而非 policy 层——它是性能优化不是行为约束，且需要携带上次结果。
- 环境预检对非 pytest 命令跳过——无法通用判断"命令能否跑"，只拦截可确定的失败。

待验证：在 jsonschema#1328（装完 attrs 后）和 click#3449 上重跑，对比改进前后的 token 消耗与 patch 产出。
