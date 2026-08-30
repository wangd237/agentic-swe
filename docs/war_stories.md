# War Stories — 开发 Agent 过程中踩过的坑

> 本文档记录的不是"agent 修好了什么 bug"，而是**开发这个 agent 时我修的 bug**——每一条都是"跑 → 发现异常 → 定位 → 修复 → 验证"的完整闭环。每个案例按固定结构组织：现象、排查、根因、修复与验证、一句话总结、常见疑问，附证据链接（commit / trace / 官方报告）。

## 目录

1. [search_graph 三连 bug：把基础设施故障误诊成模型问题](#案例-1)
2. [reasoning 模型空响应：任务假死与韧性重试](#案例-2)
3. [token 优化收益被抵消：从"省 schema"转向"省轮次"](#案例-3)
4. [phase 死锁：真实仓库永远进不了 PATCH](#案例-4)
5. [tool_router None 崩溃：签名说可选，实现说必填](#案例-5)
6. [OpenAI 协议双违规：宽松网关掩盖了两个真 bug](#案例-6)
7. [Windows 上跑官方 harness：三个平台 bug 连环坑](#案例-7)
8. [三个潜伏的协议违规：真实 issue 如何连环暴露低频路径 bug](#案例-8)
9. [从未校准的阈值：字符估算在 1M 窗口下浪费了 96% 的余量](#案例-9)

---

## 案例 1 <a name="案例-1"></a>

## search_graph 三连 bug：把基础设施故障误诊成模型问题

**时间**：2026-06-29 ~ 06-30 ｜ **这是全项目最好的一课**

### 现象

给 agent 暴露了新的 `search_graph` 工具（查询代码结构图，替代 grep 文本搜索）。基础设施全部就位：schema、backend、rate limit、82 个测试全过。但 **26 次 agent run，模型一次都没调用过这个工具**。

### 排查（错误的方向）

当时的判断是"模型不探索新工具"。于是做了 **4 轮 prompt 干预**：

| 轮次 | 干预 | 结果 |
|---|---|---|
| 1 | 软引导：description 里写"优先于 grep 使用" | 0 调用 |
| 2 | 强制条件：system prompt 写"必须先调用 search_graph" | 0 调用 |
| 3 | few-shot：给调用示例 | 0 调用 |
| 4 | 结论 commit：*"不是代码问题，是模型行为问题，等更强的模型吧"* | — |

### 根因（第二天推翻了自己）

回头读代码，发现 **3 个真实 bug**，任何一个都足以让工具永远失败：

1. **死代码**：`_indexed_project` 的赋值写在 `return` 语句**之后**——永远执行不到。模型每次调用都收到 `index_not_ready` 错误
2. **Phase gate 挡路**：`search_graph` 只在 LOCALIZE/REPRODUCE 阶段暴露，但带 `weak_static` 元数据的任务直接跳进 PATCH——模型从头到尾**根本看不到**这个工具
3. **字段名不匹配**：`search_graph_query` 返回 `results` 字段，`summarize_for_model` 读的是 `matches`——**数据一直都在，模型看到的是空数组**

模型不是"不探索"，是每次探索都撞墙，然后理性地放弃了。

### 修复与验证

修完 3 个 bug（commit `ea74904`）：

```
marshmallow_1359:  0 → 2 次 search_graph 调用
总工具调用:        -37%
LLM 调用:          -50%
grep:              -67%
search_code:       -50%
read_file:         -57%
```

同时删掉了 v16.6.3 的误诊文档（commit `d3f1754`），承认 4 轮 prompt 干预是在修不存在的问题。

### 一句话总结

> "我给 agent 加了个新工具，模型 26 次运行一次都没用。我先怪模型，做了四轮 prompt 干预全部失败，最后发现是三个代码 bug——其中一个是返回字段名和读取字段名不匹配，数据一直都在，模型看到的是空数组。教训：**模型'不配合'时，先验证基础设施真的在工作**。"

### 常见疑问

- **"为什么不一开始就检查？"** —— 工具的单元测试全过（82 passed），测试只覆盖了"调用后返回什么"，没覆盖"模型视角看到什么"。之后我把"端到端从模型视角验证"加进了流程
- **"怎么避免再犯？"** —— 修完后专门写了 commit message 记录误诊过程，并删除错误结论的文档。承认错误比留着错误结论重要

### 证据

- `git show ea74904`（3 bug 修复 + 量化结果）
- `git show 287a2cb`（错误的"等更强模型"结论）
- `git show d3f1754`（撤回误诊文档）

---

## 案例 2 <a name="案例-2"></a>

## reasoning 模型空响应：任务假死与韧性重试

**时间**：2026-08-29 ｜ **换新模型（kimi-k2.5）后立刻暴露**

### 现象

13 个代表任务验证中，task_093 **连续两次** `incomplete/no_patch`——agent 只调了 1 次工具（`list_files`）就"结束"了，连测试都没跑。

### 排查

读 trace 发现异常组合：

```
iter 1: content_block_count=2, tokens=1857   ← 正常：文本 + 工具调用
iter 2: content_block_count=0, tokens=1795   ← 异常：0 个内容块，但烧了 1795 token
```

**有 token 消耗但没有输出**——这是 reasoning 模型的特征。写最小复现脚本：构造相同消息序列直接调 API，确认 `finish_reason=stop`、`content=""`、`tool_calls=None`，全部输出烧在了 `reasoning_content` 里。同输入重试 3 次，1 次空响应——**约 1/3 概率的模型行为，不是代码 bug**。

### 根因

kimi-k2.5 偶发"思考完就停"：reasoning_content 有内容，但 content 和 tool_calls 双空。而 agent 主循环把"无文本无工具调用"解释为**模型主动结束任务**，直接 finalize——一次模型抽风就废掉整个 run。

### 修复与验证

空响应时不再放弃：注入一条系统提醒（"你上一轮没有返回内容，任务尚未完成，请继续"）并重试，上限 2 次（`max_empty_response_retries`），每次重试记录为 trace 里的 `empty_response_retry` 步骤。

```
task_093: incomplete/no_patch → success/accepted_success
```

commit `c123e11`。

### 一句话总结

> "换 reasoning 模型后任务随机假死。trace 显示有 token 消耗但零输出——我先用最小脚本复现，确认是模型 1/3 概率的空响应行为而非代码 bug，然后在 agent 层加韧性重试而不是改 prompt。**先归因，再修复**。"

### 常见疑问

- **"为什么重试而不是改 temperature？"** —— 空响应是模型偶发行为不是采样问题；temperature=0 下依然发生。重试是最小侵入的解法
- **"为什么上限 2 次？"** —— 防止模型持续空响应导致无限循环烧 token；2 次覆盖了 1/3 概率下连续失败的概率（约 1/9）
- **"怎么确认不是你的消息构造有问题？"** —— 复现脚本绕开了 agent 全部代码，直接用 openai SDK 构造相同消息序列，问题依旧

### 证据

- `git show c123e11`（修复 + 复现数据）
- `evidence/task_093/`（修复后的成功 run）
- 修复前失败 run 的 trace：iter2 `content_block_count=0, tokens=1795`

---

## 案例 3 <a name="案例-3"></a>

## token 优化收益被抵消：从"省 schema"转向"省轮次"

**时间**：2026-06-23 ~ 06-24 ｜ **方法论转折点**

### 现象

工具路由 v1（按 phase 过滤工具 schema）在 task_010 上效果显著：token 降 14.6%。但扩展到 5 个任务验证时，**2/5 任务 token 反而上升**。

### 排查数据

| 任务 | baseline | v2 | 变化 | LLM 调用次数 |
|---|---:|---:|---:|---|
| task_013 | 27,289 | 23,826 | -12.7% | 7 → 7 |
| task_016 | 25,831 | 27,233 | **+5.4%** | 7 → **8** |
| task_017 | 26,702 | 22,868 | -14.4% | 7 → 7 |
| task_019 | 28,284 | 29,361 | **+3.8%** | 7 → **8** |
| task_022 | 29,832 | 25,666 | -14.0% | 7 → 7 |

规律清晰：**token 上升的两个任务，恰好是 LLM 调用次数从 7 涨到 8 的两个**。schema 省下的 token，被多出来的一整轮调用（system prompt + 全部历史消息重发）吃掉了。

### 根因

优化方向错了。每轮 LLM 调用的成本 = schema + **全部累积上下文**，后者随轮次线性增长。省 schema 是省小头；**调用次数才是大头**。而调用次数高的原因是：大量确定性流程（改完看 diff、看完 diff 跑测试）还在让模型一步步决策。

### 修复与验证

**换方向**（v3）：把写入后的验证流程下沉到 runtime——`write_file/edit_file` 成功后自动执行 `show_diff + targeted tests + full tests`，结果同轮回喂。模型不再需要 3 轮决策做 1 件确定性的事。

v3 在同样 5 个扩展任务上相比 baseline **降低约 27.4% token**，且无任务反升。

后续 v4（失败上下文自动加载）验证不稳定（v4.1 比 v3 多 2,738 tokens），**主动回退到 v3** 并在改进记录里写明回退原因。

### 一句话总结

> "我的 token 优化第一版只在一个任务上验证就下了结论，扩展到五个任务后发现两个反升——省下的 schema token 被多出的调用轮次抵消。这个发现让我把优化方向从'省每轮的 schema'换成'减少调用轮次'，把确定性验证流程从 LLM 决策层下沉到 runtime，最终稳定降 27%。**单任务验证会骗人，扩展验证 + 敢于回退才可靠**。"

### 常见疑问

- **"为什么 v1 时不多跑几个任务？"** —— 当时图快。这个教训直接催生了后来的 frozen set 回归门禁：任何策略改动必须在冻结任务集上全量验证
- **"27.4% 怎么测的？"** —— 同一批任务、同一模型、只改策略参数，对比总 token 消耗；数据在改进记录 v3 章节

### 证据

- 改进记录 v2 扩展验证章节（本地 `../agentic-swe-local/项目1改进记录.md`）
- 改进记录"当前代码基线声明：回退到 v3"章节
- v3 机制现存于 `app/agent/llm_agent.py` 的 `run_immediate_auto_verification()`

---

## 案例 4 <a name="案例-4"></a>

## phase 死锁：真实仓库永远进不了 PATCH

**时间**：2026-06-30

### 现象

用 `repair_bug.py` 修真实 GitHub 仓库时，agent 能正确定位文件，但**永远卡在 reproduce 阶段**——`write_file`/`edit_file` 从未出现在工具列表里，14+ 轮空转后超时。

### 排查

benchmark 任务全部正常，只有真实仓库触发——差异在元数据。读 `next_phase_after_tool()` 的状态机逻辑：

```python
# 进入 patch 阶段要求 has_reproduction_evidence == True
```

benchmark 任务带 `weak_static` 元数据，启动时自动标记复现证据；真实仓库任务没有这个元数据，`has_reproduction_evidence` 只有在 `run_tests` 成功执行后才置 True——但真实仓库的测试命令往往跑不起来（环境没装依赖），于是**永远凑不齐进 PATCH 的条件**。

### 根因

状态机的一个隐含假设（"总有可运行的测试来提供复现证据"）在真实场景不成立。设计时只考虑了 benchmark 场景。

### 修复与验证

在 `next_phase_after_tool()` 加 fallback：reproduce 阶段且已有定位候选时，允许无复现证据也进入 patch。真正的写入门闩仍由 `ToolPolicy.can_patch()` 把守（复现证据 + 定位候选双条件），**放宽的是阶段流转，不是写入安全**。

验证：agent 在第 13 步进入 patch 阶段（之前永远卡在 reproduce），write_file/edit_file 出现在 schema 中。commit `3b8053d`。

### 一句话总结

> "agent 在 benchmark 上好好的，一到真实仓库就死锁。根因是状态机隐含假设'总有测试可跑'，真实仓库不满足。修复时我特意只放宽阶段流转、不放宽写入门闩——**修死锁不能顺手拆安全机制**。"

### 常见疑问

- **"放宽后不会导致乱改文件吗？"** —— 不会。`ToolPolicy.can_patch()` 仍然要求定位候选非空才允许写；改的只是"模型能不能看到写工具"
- **"为什么 benchmark 没暴露？"** —— benchmark 任务都带测试命令，隐含假设恒成立。这是"测试环境单一化"的典型盲区

### 证据

- `git show 3b8053d`
- `app/agent/tool_policy.py` 的 `next_phase_after_tool()` fallback 分支

---

## 案例 5 <a name="案例-5"></a>

## tool_router None 崩溃：签名说可选，实现说必填

**时间**：2026-08-29 ｜ **小案例，适合当开场**

### 现象

接手两个月没碰的项目，跑全量测试：**2 failed**。README 声称 367 全过。

### 排查

```
app/agent/tool_router.py:54: AttributeError: 'NoneType' object has no attribute 'name'
```

`build_tools_for_state()` 的签名声明 `code_intelligence_backend` 可选（默认 `None`），但 search_graph 的 adaptive gate 直接解引用 `backend.name`——**签名承诺了实现没兑现的事**。这是两个月前 search_graph 那次提交引入的回归，CI 当时没拦住（该路径只有特定调用方式才触发）。

### 修复与验证

`None` 视为"backend 不可用"，隐藏 search_graph——这本来就是 gate 的设计意图。3 行修复，367 全绿。commit `318f17c`。

### 一句话总结

> "接手老项目第一件事是跑测试，发现 README 声称的数字和实际不符。根因是一个'签名说可选、实现说必填'的参数——修复只用了三行，但**让仓库的每条声明重新变得可信**，这比修复本身更重要。"

### 证据

- `git show 318f17c`

---

## 案例 6 <a name="案例-6"></a>

## OpenAI 协议双违规：宽松网关掩盖了两个真 bug

**时间**：2026-08-29 ｜ **换模型立刻暴露**

### 现象

从内部网关（kimi-k2.5）切换到 DeepSeek 官方 API 后，agent 第一轮就报 400：
`An assistant message with 'tool_calls' must be followed by tool messages responding to each 'tool_call_id'`。

之前用 kimi 网关跑了 13 个任务全部成功——**同样的代码，换个 API 就崩**。

### 排查

写最小复现脚本直接调 `_messages_to_openai()`，构造消息序列看转换结果，找到两处违规：

1. **auto_finalize 提前 break**：写入后自动验证通过时，循环在 `messages.append(tool_results)` **之前** break——assistant 的 tool_calls 进了 messages，配对的 tool_result 没进
2. **phase_hint 插错位置**：阶段切换提示作为独立 user 消息，插在 assistant(tool_calls) 和 tool_result **中间**，隔断了配对

### 根因

两个都是违反 OpenAI 协议的消息构造 bug。**kimi 网关不严格校验配对，默默容忍了它们**；DeepSeek 官方 API 严格校验，直接拒绝。bug 一直都在，只是之前的运行环境把它藏住了。

### 修复与验证

Bug 1：break 前先 append tool_results。Bug 2：phase_hint 改为拼进 tool_result 内容，不再作为独立消息。

验证：marshmallow-1343 从启动即 400 → 跑完 35 次工具调用产出 patch。commit `969c2a6`。

### 一句话总结

> "换了个 LLM 提供商，agent 立刻崩。根因是两个违反 OpenAI 协议的消息构造 bug——之前的网关不严格校验，默默容忍了它们。**宽松环境会掩盖协议违规，换严格环境才暴露**。这也是为什么集成测试要贴近生产环境。"

### 常见疑问

- **"为什么之前没发现？"** —— 13 个任务全在宽松网关上跑，行为正确性恰好不依赖被违反的约束。教训：依赖协议细节的代码，要在最严格的实现上测
- **"怎么防再犯？"** —— 最小复现脚本直接测 `_messages_to_openai` 的输出序列，不依赖真实 API

### 证据

- `git show 969c2a6`

---

## 案例 7 <a name="案例-7"></a>

## Windows 上跑官方 harness：三个平台 bug 连环坑

**时间**：2026-08-30 ｜ **拿到 resolved 3/8 的最后一公里**

### 现象

SWE-bench 官方 harness（swebench 2.1.8）在 Windows 上完全跑不起来：第一轮 8 个 instance **全部 error**，而且错误信息晦涩（`ValueError: No escaped character`）。

### 排查（三轮连环）

**坑 1：Windows 路径渗进容器命令**。`copy_to_container` 里 `Path("/eval.sh")` 在 Windows 上是 `WindowsPath`，f-string 拼出 `tar -xf \eval.sh.tar -C \`——尾随反斜杠被 shlex 当成不完整的转义符。修复：强制 `PurePosixPath`。

**坑 2：eval.sh 写成 CRLF**。Windows 文本模式默认写 CRLF，容器里 bash 把 `\r` 当命令一部分：`conda activate testbed\r` 报 "No such file or directory"。修复：`write_text(..., newline="\n")`。

**坑 3：patch.diff 同样 CRLF**。`git apply` 在容器里报 trailing whitespace + patch does not apply。同上修复。

三个坑的共同模式：**宿主机是 Windows，容器是 Linux，任何“文本/路径”跨边界传递都是雷区**。

### 修复与验证

三个补丁固化成 `patches/swebench/apply_windows_patches.sh`（幂等，可重复运行），换机器可重放。

验证：同一批 prediction 从 **0/8 全 error → resolved 3/8**。

### 一句话总结

> “官方 harness 在 Windows 上全挂，错误信息是 shlex 的 'No escaped character'。根因是三个 Windows/Linux 边界 bug：路径分隔符、两处 CRLF 换行。修复后从 0/8 到 resolved 3/8。**跨平台工具链的坑都在边界上**。”

### 常见疑问

- **“为什么不用 WSL/Linux？”** —— 合理选择，但当时环境已就绪；且把补丁固化后 Windows 也能稳定跑，反而成了可复现资产
- **“补丁打在 site-packages 里，升级 swebench 会丢？”** —— 所以固化成了仓库里的 shell 脚本，幂等可重放；swebench 5.x 已修这些 bug，升级时脚本会自动 skip

### 证据

- `patches/swebench/apply_windows_patches.sh`
- `evidence/swebench_lite_official/`（官方报告 + 3 个 resolved 的 patch）

---

## 案例 8 <a name="案例-8"></a>

## 三个潜伏的协议违规：真实 issue 如何连环暴露低频路径 bug

**时间**：2026-08-30 ｜ **一天内三个 400，全部来自同一类根因**

### 现象

拿真实 GitHub issue 验证 agent 能力，一天内连续撞上三个不同的 400 错误：

```text
400 #1: An assistant message with 'tool_calls' must be followed by tool messages...
400 #2: Invalid assistant message: content or tool_calls must be set
400 #3: Messages with role 'tool' must be a response to a preceding message with 'tool_calls'
```

三个错误信息不同，但都在说同一件事：**发给 API 的消息序列违反了 OpenAI 协议**。

### 排查（三个 bug，三条路径）

**Bug 1（重试路径从未被真实触发）**：reasoning 模型偶发返回 content/tool_calls 双空。空响应重试机制（案例 2 的修复）本身是对的，但它把空 assistant 消息留在了历史里——重试注定失败。**修复机制自己制造了下一个 bug**。上次 13 个任务全跑在宽松网关上，重试路径从未在严格 API 上被真实执行过。

**Bug 2（压缩边界切断配对）**：上下文压缩的 `keep_recent=3` 边界恰好落在 `assistant(tool_calls)` 和它的 `tool_result` 之间——assistant 进了摘要区被替换成 system 消息，tool_result 留在 recent 区。下一个请求直接被拒。**压缩功能上线以来从未在"测试输出大到触发压缩"的场景下跑过**。

**Bug 3（预检自身的报错提取 bug）**：环境预检第一次实战拦截了依赖缺失，但报错显示的是 pytest 的 `=== ERRORS ===` 分隔线而不是真正的 `ModuleNotFoundError`——关键词匹配顺序问题，分隔线抢先匹配。

### 根因

三个 bug 的共同点：**都在低频路径上，都被之前的运行环境掩盖**。

| Bug | 触发条件 | 潜伏时长 |
|---|---|---|
| 空 assistant 消息 | reasoning 模型偶发空响应 | 重试机制上线以来 |
| 压缩切断配对 | 首次触发上下文压缩 | 压缩功能上线以来 |
| 预检报错提取 | 首次真实拦截 | 预检上线当天 |

### 修复与验证

每个修复都带回归测试（374 全绿）：

- Bug 1：主循环不 append 空 assistant_blocks + `_messages_to_openai` 协议兑底填充（两层防御）
- Bug 2：压缩切分前边界向后回退，配对完整性成为压缩不变量
- Bug 3：两级优先级提取，ModuleNotFoundError 优先于 pytest 包装行

验证：同一 issue（jsonschema#1328）从三次失败到第四次完整成功——`success / accepted_success / full_verification_success`，7881 测试零回归。

### 一句话总结

> "我拿真实 issue 验证 agent，一天撞了三个 400。归因发现三个 bug 全在低频路径上：重试路径从未被真实触发过、压缩从未在大输出下跑过、预检从未实战过。**低频路径的 bug 只能靠真实负载暴露——单测覆盖的是"调用后返回什么"，覆盖不了"真实序列下会发生什么"**。"

### 常见疑问

- **"为什么单测没拦住？"** —— 单测构造的消息序列都是"正常"的。协议违规发生在特定时序（空响应后重试、压缩边界落点）下，这些时序在单测里从未被构造过
- **"怎么防再犯？"** —— 三个修复都加了回归测试，但更根本的教训是：**依赖协议细节的代码，要在最严格的实现上测，且要用真实负载测**
- **"和案例 6 什么关系？"** —— 同一模式的三个新实例。案例 6 是"宽松网关掩盖 bug"，这次是"低频路径掩盖 bug"——掩盖的形式不同，本质相同

### 证据

- `git show 191f27f`（空 assistant 消息修复）
- `git show 5b7a52e`（压缩配对保护）
- `git show 8a8d70c`（预检报错提取）
- `docs/failure_analysis.md` 第 6 节（四次 run 对比）

---

## 案例 9 <a name="案例-9"></a>

## 从未校准的阈值：字符估算在 1M 窗口下浪费了 96% 的余量

**时间**：2026-08-30 ｜ **度量推翻直觉的典型案例**

### 现象

上下文压缩的触发阈值是 80K 字符——这个数字是 6 月 15 日定的，之后从未回头验证过。长任务里压缩频繁触发，每次都把中间轮次的历史摘要掉，PATCH 阶段的失败签名和定位历史被丢弃。当时默认这是“必要的取舍”。

### 排查（先观测，不先改）

没有直接换公式，而是先建观测管道：`_normalize_usage` 保留 API 返回的 `prompt_tokens`（之前只留 total 后丢弃），每个 llm\_response 步骤记录字符估算与实测对照。跑 3 个真实任务 46 次调用，拿到两个关键事实：

1. **稳态字符/token 比值 2.45**（范围 1.93~3.10）——chars/2.5 估算在稳态偏差 ±24%，够做二元判断不够做精确 reserve
2. **窗口事实修正**：deepseek-v4-flash 是 **1M token 窗口**，不是之前以为的 64K

第二个事实直接推翻了整个前提：旧阈值 80K chars ≈ 37K tokens，只占窗口的 **3.7%**。压缩在长任务里**从来都不是必要的**——纯粹是被拍脑袋的字符阈值人为触发，每次都在丢不该丢的上下文。

### 根因

阈值从未校准。字符估算本身没错（作为降级手段依然保留），错的是把它当主判定且从不对照实测。而“64K 窗口”这个错误认知让 80K chars 看起来“接近满窗”，实际上离满窗还有 96% 的余量。

### 修复与验证

压缩判定改为 `estimated_tokens > context_window_tokens - reserve_tokens`。估算优先用**最近一次 API 实测 prompt\_tokens 做锚点**（天然覆盖 system prompt + 工具 schema 开销，比任何离线估算准），无锚点时退回 chars/2.5 保守估算（高估 token → 提前压缩 → 安全方向）。

配置遵循既有分工：窗口大小进 `.env`（模型属性，随模型切换），reserve 进 policy（行为参数）。

验证：重跑 marshmallow\_1343（旧逻辑必触发压缩的任务），压缩次数 1 → **0**，上下文全程 38.5K tokens（窗口 3.9%），PATCH 阶段历史完整保留。380 测试全绿。

### 一句话总结

> “上下文压缩阈值是两个月前拍的，从未校准。建观测管道实测后发现模型窗口是 1M 不是 64K——旧阈值只占窗口 3.7%，每次压缩都在丢不该丢的上下文。修复后同等任务零压缩。**拍脑袋的阈值不会自己变对，观测才会告诉你真相**。”

### 常见疑问

- **“为什么锚点用上一次的 prompt\_tokens？它滞后一轮。”** —— 确实滞后：锚点是上一轮调用的实测，而压缩判断发生在新消息 append 后。在 1M 窗口 + 16K reserve 下这个误差无害；但换小窗口模型（如 64K 的 deepseek-chat）时，滞后一轮的增量可能就是几 K token，reserve 需要把这个滞后算进去。这是已知风险，记录在 ADR-0002 Risks 里
 - **“为什么不直接用 tiktoken 离线算？”** —— 增加依赖，且精度未必优于 API 返回的实测锚点。实测锚点天然包含 system prompt 和工具 schema 的开销，这些离线估算很难准确覆盖
 - **“chars/2.5 的 fallback 可靠吗？”** —— 稳态均值 2.45、偏差 ±24%。够做“要不要压缩”的二元判断，不够做精确 reserve——所以它只是首次调用前的降级，有锚点后立即切换

### 证据

- `git show 854561f`（Step 1 观测管道 + 校准数据）
- `git show 6a7a76c`（Step 2 判定替换 + 验证）
- `docs/decisions/0002-token-budget-replace-char-budget.md`（完整决策记录）

---

## 附：这些故事的共同模式

| 案例 | 教训 |
|---|---|
| search_graph 三连 bug | 模型"不配合"时，先怀疑基础设施 |
| 空响应假死 | 先复现归因（模型行为 vs 代码 bug），再选修复层 |
| token 收益被抵消 | 单任务验证会骗人；优化要抓大头（轮次 > schema） |
| phase 死锁 | 状态机的隐含假设在真实场景会碎 |
| None 崩溃 | 仓库可信度 = 每条声明可验证 |
| Windows harness 三连坑 | 跨平台工具链的坑都在宿主机/容器边界上 |
| OpenAI 协议双违规 | 宽松网关会掩盖协议违规，换严格 API 全暴露 |
| 三个潜伏的协议违规 | 低频路径的 bug 只能靠真实负载暴露 |
| 从未校准的阈值 | 拍脑袋的阈值不会自己变对，观测才会告诉你真相 |

一句话总结这个项目的开发方法论：**每个异常都值得一条 trace；每个修复都要能回答"怎么证明修好了"；每个"模型不行"的结论都要先排除"代码有 bug"。**
