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

## 6. 验证闭环：jsonschema#1328 四次 run 对比（2026-08-30）

同一 issue、同一测试命令，四次 run 完整记录了"失败→归因→修复→验证"的全过程：

| Run | 状态 | 根因 | 责任层 | 结果 |
| --- | --- | --- | --- | --- |
| 1 | 测试命令指向不存在的文件（exit 4） | 用户输入错误 | 用户 | incomplete，reflection 在无效验证下误判 wrong_file 回滚 |
| 2 | API 400：空 assistant 消息 | 代码 bug（协议违规） | 系统 | 崩溃，trace 未落盘 |
| 3 | attrs 未安装（exit 2） | 环境依赖缺失 | 环境 | incomplete，模型 16 轮探测注定失败的验证环境 |
| 4 | **全部修复就位** | — | — | **success / accepted_success / full_verification_success** |

### Run 4 详情（首个完整成功）

- token：301,850；工具调用 22 次（grep ×8，read_file ×7，edit_file ×2，run_tests ×2）
- phase 轨迹：understand → reproduce → patch → verify → final
- patch：`ErrorTree._contents` 从 `defaultdict(self.__class__)` 改为普通 `dict`，构造循环显式创建子树——正是 issue 根因
- 语义验证（人工跑 issue 复现代码）：`list(tree)=[0]` ✓、`1 in tree=False` ✓、访问后不再污染 ✓
- 全量回归：7881 passed, 631 skipped，零回归
- 已知瑕疵：`tree[1]`（访问无错误但 instance 存在的索引）从"返回空子树"变为抛 `KeyError`——核心 bug 修对，访问语义有行为变化；官方 main 至今未修此 issue，无对照标准

### 三个机制在成功 run 中的表现

1. **预算升级生效**：iter 12 注入告警，iter 13 模型立即响应"我已经完全理解了问题"+根因总结+修复方案，iter 14-16 完成写入→验证→success。对比 #1257（告警被无视）：**预算升级对有明确答案的任务有效，对开放设计任务无效**——边界发现。
2. **PATCH gate 正确拦截**：iter 14 模型直接 edit_file 被挡（无复现证据），模型正确应对：先跑 run_tests 建基线 → 基线通过（bug 无回归测试覆盖）→ 说明静态复现证据 → 重新写入。约束引导了正确流程而非阻碍修复。
3. **自动验证闭环**：edit_file → show_diff → full run_tests → auto_finalize，最后 5 步零额外轮次。

### token 消耗说明

Run 4（30.2 万）略高于 Run 3（29.8 万）——改进目标不是省 token，是**把注定失败的 run 变成能成功的 run**。token 经济性是下一阶段优化目标（重叠读检测仍未实施，#1257 中 55% 读取冗余）。

## 7. 补充失败样本：jsonschema#1257（设计讨论类 issue）

**验证深度：trace 级**

- 状态：incomplete/max_iterations，25.5 万 token，0 写入，0 run_tests
- 预算升级在 iter 12 注入但被无视（模型继续读代码 4 轮）
- 重叠读：`test_exceptions.py` 8 段共 1149 行，去重 519 行，**55% 冗余**
- **根因：issue 选错**。标题 "Mitigate undesired side effect ... with alternative proposal"——这是设计讨论类 issue，不是 bug fix：无失败断言、无 FAIL_TO_PASS、正确答案开放（作者提出"替代方案"）。模型 16 轮试图理解需要设计决策的问题，预算根本不够"理解+设计+实现"。

### 失败模式三层分类（更新）

| 层 | 失败 | 实例 | 状态 |
| --- | --- | --- | --- |
| 基础设施层 | 协议违规、环境依赖 | 400×3、attrs 缺失 | ✅ 全部修复 |
| 系统行为层 | 探索无节流、重叠读、告警强度不足 | click#3449、#1257 | ⚠️ 部分（搜索拦截✓，读侧✗） |
| 任务适配层 | issue 类型与 agent 能力错配 | #1257（设计讨论） | ❌ 无防御 |

### 待改进（更新后优先级）

1. **换对 issue 重跑建立基线**（零代码）：找真正的 bug fix 类 issue（有 traceback、失败断言、明确预期），验证现有改进在正确任务上的效果。
2. **预算告警升级为硬约束**（~40 行）：75% 后收窄工具列表只留 edit_file/write_file/run_tests——符合"约束优于提示"的项目哲学，与 phase gate 对称。
3. **重叠读检测**（~40 行）：数据已两次确认（click#3449 57%、#1257 55%）。
4. **任务预分类**（可选，~30 行）：issue 文本含 proposal/design/RFC 信号时警告用户，不阻断。启发式可能误伤，优先级最低。
