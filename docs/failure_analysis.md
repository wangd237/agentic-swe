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

## 8. click#3449 重跑验证：三个改进未改变结局（2026-09-08）

**验证深度：trace 级**。同模型（deepseek-v4-flash）、同 policy、同 repo、同测试命令，对第 5 节三个改进做对照重跑。

### 结果对比

| 指标 | 基线（08-30） | 重跑（09-08） |
| --- | --- | --- |
| final_status | incomplete / max_iterations | incomplete / max_iterations |
| 工具调用 | 24（read_file×17） | 24（read_file×17） |
| token | 198,917 | 206,151（+3.6%） |
| patch | 0 | 0 |
| 预算升级 | 不存在 | **iter 12 注入，被无视** |

### Trace 级归因

1. **预算升级已注入但被无视**：step 35（iter 12）注入告警后，模型继续 grep×3、read_file×3 直到耗尽。与 #1257 同模式——至此该模式已有三个独立实例（click#3449×2、#1257），**提示式干预对探索型失败无效**的结论可以定案。
2. **重叠读仍在**：17 次 read_file 共 1882 行，去重 1163 行，**冗余 38%**（基线 57%，#1257 55%——三次数据一致指向同一缺口）。
3. **重复搜索拦截未触发**：本次 5 次 grep 均为不同 pattern/glob 组合，拦截器无机会生效——它治的是重复，不治发散。
4. **环境预检通过**：45 tests collected，环境层无问题，失败纯在行为层。

### 结论：改进方向修正

三个改进中，环境预检（治环境层）与搜索拦截（治重复）在各自责任层有效，但 click#3449 的失败在**行为层**——模型对“何时停止探索”没有内部信号，提示无法改变行为。下一步应实施第 7 节待改进 #2：**预算告警升级为硬约束**（75% 后收窄工具列表只留 edit_file/write_file/run_tests）——约束优于提示，与 phase gate 哲学一致。重叠读检测（待改进 #3）数据已三次确认，可并行实施。

## 9. 硬约束验证：机制生效，但模型以空响应“罢工”（2026-09-08）

**验证深度：trace 级**。同任务/同模型/同 policy 第三次 run，唯一变量是预算硬约束（commit 89245d0）。

### 三次 run 对比

| 指标 | Run 1 基线 | Run 2 提示式告警 | Run 3 硬约束 |
| --- | --- | --- | --- |
| final_status | incomplete | incomplete | incomplete |
| 工具调用 | 24（read×17） | 24（read×17） | 22（read×14, **run_tests×1**） |
| token | 198,917 | 206,151 | 208,041 |
| patch | 0 | 0 | 0 |
| 告警后行为 | — | 无视，继续读 | **波拦截后连续 3 轮空响应** |

### 硬约束机制全部按设计工作（trace 证据）

1. **Schema 层收窄生效**：iter 12 起 `tool_schema_names: [run_tests, write_file, edit_file, show_diff]`，探索工具从模型视野物理消失。
2. **Policy 层拦截生效**：iter 12 模型仍试图 `read_file` + `grep`（并行组），两者均返回 `tool_policy_violation`，探索被物理阻止。
3. **PATCH gate 升序正确**：iter 11 模型自发跑了 `run_tests`（发现测试全过——bug 无回归测试覆盖），gate 已开，写入通道肠通。

### 新失败模式：剥夺探索工具后模型“罢工”

被拦截后，模型连续 3 轮返回空响应（`content_block_count: 0`），两次 `EMPTY_RESPONSE_NOTICE` 重试均无效，run 终止。iter 12 的 planning 显示模型当时正在合法调查中途：“测试全过说明现有测试抓不到 bug，让我看 testing.py 的 isolation 理解流机制”——它还没合成根因，破逼写入只会产出猜测 patch。它选择了放弃而不是写最佳假设。

### 归因：这不是系统 bug，是任务类别与模型能力的双重边界

1. **任务侧**：click#3449 无失败测试锚点（测试命令全过），修复需要跨 3 个文件理解流语义。issue 正文自带 reproducer，但三次 run 模型都未用 `python_repl` 执行它——错过最短路径。
2. **模型侧**：deepseek-v4-flash 在被约束后选择空响应而非邨守“写最佳假设”指令。这是模型行为边界，不是系统能修的。
3. **系统侧**：三次 run 系统行为全部正确——诚实失败、无虚假成功、约束机制按设计工作。Run 3 相比 Run 1/2 多了一次 run_tests（verification_strength 从 none 升到 targeted），说明模型在约束下至少开始验证了。

### 第四次 run：python_repl 加入后（af35a01）

escalation 集合加入 `python_repl`（修复了交集 bug：patch phase 默认集合不含它，交集会静默挡掉）后重跑：

| 指标 | Run 3 硬约束 | Run 4 +python_repl |
| --- | --- | --- |
| 工具调用 | 22 | 22 |
| token | 208,041 | 204,743 |
| patch | 0 | 0 |
| 告警后行为 | 3 轮空响应 | 配合 1 轮（run_tests）→ 2 次读被拦 → 2 轮空响应 |

行为变化：模型这次**理解并配合了约束**（planning："Exploration tools are now budget-limited, so I'll base the patch on the code I've already read plus run tests"），escalation 后主动跑了 run_tests。但它随后两次试图读 `_nullpager` 函数体（它判断需要这个函数体才能写 patch）被拦截，之后空响应。`python_repl` 在 schema 里可用，但模型没有用它跑 issue 自带的 reproducer。

### 四次 run 终局归因（2026-09-08）

| Run | 干预 | 结果 | 模型告警后行为 |
| --- | --- | --- | --- |
| 1 | 无 | incomplete，0 patch | — |
| 2 | 提示式告警 | incomplete，0 patch | 无视，继续读 |
| 3 | 硬约束（4 工具） | incomplete，0 patch | 被拦后罢工（3 轮空响应） |
| 4 | 硬约束（5 工具，+python_repl） | incomplete，0 patch | 配合 1 轮→读被拦→罢工（2 轮空响应） |

**结论：系统侧已无低成本改进空间。** 硬约束机制（schema 收窄、policy 拦截、gate 升序）四 run 全部按设计工作；模型侧的边界清晰：deepseek-v4-flash 在“无失败测试锚点 + 需跨文件流语义理解 + 16 轮预算”的任务上不收敛，被约束后选择空响应而非写最佳假设。click#3449 定性为**任务透型边界样本**，不再投入。后续验证应换有失败测试锚点的 issue（第 7 节待改进 #1）。


**验证深度：trace 级**。同模型（deepseek-v4-flash）、同 policy、同 repo、同测试命令，对第 5 节三个改进做对照重跑。

### 结果对比

| 指标 | 基线（08-30） | 重跑（09-08） |
| --- | --- | --- |
| final_status | incomplete / max_iterations | incomplete / max_iterations |
| 工具调用 | 24（read_file×17） | 24（read_file×17） |
| token | 198,917 | 206,151（+3.6%） |
| patch | 0 | 0 |
| 预算升级 | 不存在 | **iter 12 注入，被无视** |

### Trace 级归因

1. **预算升级已注入但被无视**：step 35（iter 12）注入告警后，模型继续 grep×3、read_file×3 直到耗尽。与 #1257 同模式——至此该模式已有三个独立实例（click#3449×2、#1257），**提示式干预对探索型失败无效**的结论可以定案。
2. **重叠读仍在**：17 次 read_file 共 1882 行，去重 1163 行，**冗余 38%**（基线 57%，#1257 55%——三次数据一致指向同一缺口）。
3. **重复搜索拦截未触发**：本次 5 次 grep 均为不同 pattern/glob 组合，拦截器无机会生效——它治的是重复，不治发散。
4. **环境预检通过**：45 tests collected，环境层无问题，失败纯在行为层。

### 结论：改进方向修正

三个改进中，环境预检（治环境层）与搜索拦截（治重复）在各自责任层有效，但 click#3449 的失败在**行为层**——模型对“何时停止探索”没有内部信号，提示无法改变行为。下一步应实施第 7 节待改进 #2：**预算告警升级为硬约束**（75% 后收窄工具列表只留 edit_file/write_file/run_tests）——约束优于提示，与 phase gate 哲学一致。重叠读检测（待改进 #3）数据已三次确认，可并行实施。

### 待改进（更新后优先级）

> 2026-09-08 更新：#2 已实施并验证（见第 9 节）；#1 仍是最优先——click#3449 三次 run 已充分归因，继续投入性价比低。

1. **换对 issue 重跑建立基线**（零代码）：找真正的 bug fix 类 issue（有 traceback、失败断言、明确预期），验证现有改进在正确任务上的效果。
2. ~~**预算告警升级为硬约束**~~（已完成，见第 9 节：机制生效，但暴露模型空响应罢工边界）。
3. **重叠读检测**（~40 行）：数据已三次确认（click#3449 57%/38%、#1257 55%）。
4. **任务预分类**（可选，~30 行）：issue 文本含 proposal/design/RFC 信号时警告用户，不阻断。启发式可能误伤，优先级最低。
