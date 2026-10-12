# Agentic SWE (SAG-V1) — 面试备战指南

> 这篇文档是专为面试准备的**一本通**。读完它，你能在 15 分钟内讲清楚这个项目的架构、工程深度和量化结果。

---

## 目录

1. [30 秒电梯 Pitch](#1-30-秒电梯-pitch)
2. [3 分钟项目精讲](#2-3-分钟项目精讲)
3. [架构全景图](#3-架构全景图)
4. [核心设计哲学](#4-核心设计哲学)
5. [关键技术组件](#5-关键技术组件)
6. [量化结果一览](#6-量化结果一览)
7. [War Stories：13 个工程深度案例](#7-war-stories13-个工程深度案例)
8. [失败分析与根因归因](#8-失败分析与根因归因)
9. [高频面试问答](#9-高频面试问答)
10. [速查卡片](#10-速查卡片)

---

## 1. 30 秒电梯 Pitch

> **Agentic SWE** 是一个面向真实代码仓库的 AI Bug Repair Agent。从 rule-based solver 演进为 LLM coding agent，在隔离 workspace 中完成「理解→复现→定位→补丁→验证」闭环。核心设计哲学是**用确定性组件包裹概率性组件**——tool_policy 约束行为、verification quality layer 防止假成功、phase gate 控制阶段流转、trace 全量落盘保证可审计。SWE-bench Lite 官方 resolved **4/8**，真实 GitHub issue **4/5**，380 条回归测试，frozen set 连续 72+ 策略版本无回归。

---

## 2. 3 分钟项目精讲

### 背景与动机

这个项目的出发点是：**把 LLM 从「直接生成代码」约束进可控的工程闭环**。不是让模型自由聊天式修代码，而是把修复任务拆成可约束、可验证、可审计的阶段，每一阶段有明确的工具权限和验证门禁。

项目路径：从 rule-based solver（规则匹配 → 补丁生成）演进到 LLM coding agent（模型理解语义 → 工具调用 → 修复），rule-based 保留为稳定 baseline 对照。

### 核心工作流

```
issue → UNDERSTAND → REPRODUCE → LOCALIZE → PATCH → VERIFY → FINAL
```

每个阶段有：
- **tool_policy**：约束该阶段可调用的工具（比如 UNDERSTAND 阶段不能 write_file）
- **phase gate**：控制阶段流转条件（必须先有复现证据才能进 PATCH）
- **verification**：写入后自动执行 show_diff + targeted tests + full tests，失败时自动 undo
- **trace**：每一步的状态、工具调用、token 消耗全部落盘

### 关键设计决策

1. **确定性包裹概率性**：LLM 做语义理解和代码生成（概率性），但 tool_policy、phase gate、verifier 是硬编码的确定性约束（事前塑形 + 事后强制）
2. **先归因再修复**：每个失败/异常都先做 trace 级归因，确认是代码 bug 还是模型行为再动手。13 个 war story 每条都是「现象→排查→根因→修复→验证」完整闭环
3. **验证质量分层**：区分 full_verification / targeted / weak / local_smoke，不把本地 smoke 包装成 official resolved

---

## 3. 架构全景图

```
┌──────────────────────────────────────────────────────────┐
│                      Input Layer                          │
│  GitHub issue / semi-real task / local repo bug           │
└───────────────────────┬──────────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────────┐
│                   Runtime Harness                         │
│  workspace 隔离 · git 工作区 · 日志落盘 · 批量运行         │
└───────────────────────┬──────────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────────┐
│                     Agent Core                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐    │
│  │ToolPolicy│  │Phase Gate│  │ Tool Router           │    │
│  │ 阶段权限  │  │ 流转条件  │  │ 每轮暴露相关工具 schema │    │
│  └──────────┘  └──────────┘  └──────────────────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐    │
│  │ Verifier │  │Reflector │  │ Code Locator         │    │
│  │ 验证质量  │  │ 自动纠错  │  │ 代码定位 + graph hints │    │
│  └──────────┘  └──────────┘  └──────────────────────┘    │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Context Engineering                  │    │
│  │ token 预算压缩 · microCompact · 大输出落盘          │    │
│  └──────────────────────────────────────────────────┘    │
└───────────────────────┬──────────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────────┐
│                    Tool Layer                             │
│  list_files · grep · read_file · search_code ·           │
│  run_tests · edit_file · write_file · show_diff ·        │
│  undo · python_repl · search_graph                       │
└───────────────────────┬──────────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────────┐
│                 Audit Artifacts                           │
│  trace.json · result.json · patch.diff · summary.md      │
└──────────────────────────────────────────────────────────┘
```

---

## 4. 核心设计哲学

### 「用确定性组件包裹概率性组件」

这是贯穿整个项目的指导原则：

| 层 | 性质 | 职责 |
|---|---|---|
| LLM 语义理解与代码生成 | **概率性** | 理解 issue、读代码、写 patch |
| Prompt 工程（First Principles、few-shot） | **概率性塑形** | 事前引导，提高模型决策质量 |
| tool_policy / phase gate / verifier | **确定性强制** | 事后约束，确保不越界、不假成功 |

面试金句：
> "LLM 的本质是概率性的——你无法保证它每次都做出正确决策。所以架构的核心不是'信任模型'，而是'假设模型会犯错，用确定性约束兜底'。tool_policy 物理阻止错误阶段的工具调用，verifier 不看模型说什么只看测试结果，phase gate 没有复现证据就不放行写入。"

### 先归因，再修复（工程方法论）

13 个 war story 的共同模式：
1. 观察到异常现象
2. 最小复现确认问题（先怀疑基础设施，再怀疑模型）
3. trace 级深挖找根因
4. 修复 + 回归测试验证
5. 一句话总结教训

面试金句：
> "search_graph 工具上线后模型 26 次 run 从不调用。我先做了 4 轮 prompt 干预全部失败，最后发现是三个代码 bug——其中一个字段名不匹配。数据一直都在，模型看到的是空数组。教训：模型'不配合'时先验证基础设施真的在工作。"

---

## 5. 关键技术组件

### 5.1 Phase Gate & Tool Policy（阶段门禁）

**问题**：无约束的 agent 会跳过复现直接改代码，或者在没有证据的情况下声称修好了。

**方案**：
- 6 个阶段严格顺序：UNDERSTAND → REPRODUCE → LOCALIZE → PATCH → VERIFY → FINAL
- 每个阶段有允许的工具白名单（`ALLOWED_TOOLS_BY_PHASE`）
- Phase gate 控制流转：必须有复现证据（has_reproduction_evidence）才能进 PATCH；必须有定位候选才允许写入
- **预算硬约束**：轮次 ≥75% 且 0 写入时，强制收窄工具列表只留 edit_file/write_file/run_tests，物理阻止探索

**量化**：
- tool routing 在 task_010 上 token 30,510 → 18,553（-39%），LLM 调用 7 → 5
- click#3449：提示式告警无效（模型无视），硬约束生效（模型被拦截后转向合法路径完成修复）

**面试话术**：
> "phase gate 解决了两个核心问题：一是模型跳过复现直接改代码——约束要求必须有测试失败证据才能进 PATCH；二是模型探索到死——75% 预算后强制收窄工具列表，把'建议停止探索'从提示升级为硬约束。structurally 这和 compiler 的 type system 是一个思路：不是让程序员别犯错，是让错误的代码根本通不过。"

### 5.2 Verification Quality Layer（验证质量分层）

**问题**：常见 agent 看模型说"solved"就标 success——假成功（false positive）是 agent 最大的信任危机。

**方案**：五层验证质量 + 结构化 verifier pipeline

```
Level 0: missing          — 无证据（直接拒绝）
Level 1: weak/static      — 静态分析/模型自称（标记但不接受）
Level 2: targeted         — 只跑了失改测试（部分证据）
Level 3: local_smoke      — 本地全量测试通过（可信但不等于 official）
Level 4: full_verification — patch + pre-test 失败 → post-test 全过（最强）
```

Verifier pipeline：
1. `build_verification_evidence()` — 收集 patch、pre-test、post-test、official harness
2. `assess_evidence_quality()` — 分类为 strong / partial / weak / missing
3. `build_verifier_report()` — 综合 verdict（risk_level + acceptance + caveats）
4. `accepted_final_status_from_report()` — 映射为产品可读的最终状态

**真实案例验证**：
- pydicom-1139：本地 smoke 通过但官方判 regression → verification layer 正确区分 local_smoke vs official resolved
- jsonschema#1328 Run 1-3：系统没有把 3 次失败包装成任何形式的"部分成功"——失败得诚实

**面试话术**：
> "SWE-bench 官方评测中，pydicom-1139 被判定 unresolved。但本地容器里同一批测试全过——verification quality layer 的正确设计在这里得到验证：系统用 local_smoke_success + evidence_quality: partial + missing_evidence: official_harness 标记，而不是错误地声称 resolved。这个分层避免了 agent 最常见的伦理问题：把本地通过包装成 benchmark 成绩。"

### 5.3 Auto-Verification Loop（自动验证闭环）

**原理**：写入工具成功后，runtime 自动执行三级验证链，结果同轮回喂模型，不额外消耗轮次。

```
write_file/edit_file 成功
  → show_diff（立即查看改动）
  → targeted run_tests（只跑之前失败过的测试）
  → full run_tests（跑完整测试套件）
  → 结果同轮回喂
```

**失败签名对比（auto reflection）**：

| 失败 delta | 判定 | 系统动作 |
|---|---|---|
| 不变 | wrong_hypothesis / wrong_file | 自动 undo + 回 LOCALIZE |
| 变化 | partial_fix | 保留 patch，继续 PATCH |
| 新增失败 | overfit / low_confidence | 建议缩小范围 |

**面试话术**：
> "写入后的验证曾经需要模型做 3 轮决策——看 diff、跑 targeted 测试、跑 full 测试——每轮都要把全部历史重发给 LLM。把这三步下沉到 runtime 后，变成了零额外轮次的自动化流程。token 优化 27% 的核心不是省了 schema，是省了轮次——每少一轮就少一次完整上下文重发。"

### 5.4 上下文工程（Context Engineering）

三层策略，从轻到重：

**Layer 1: 结构化的工具输出**
- `run_tests` 内部做 `--tb=short` + `_build_failure_summary` 提取 failed tests/locations/exception/possible_symbols
- 模型不需要看完整 pytest 输出就能定位根因

**Layer 2: microCompact**
- 单个超大工具结果在进入上下文前前置截断到阈值
- 完整结果落盘到 `tool_outputs/`，审计链不因截断断裂

**Layer 3: Token 预算驱动的智能压缩（ADR-0002）**
- **旧问题**：80K 字符阈值是两个月前拍的，从未校准。实测 deepseek-v4-flash 窗口是 1M tokens，旧阈值只占 3.7%
- **新方案**：压缩判定改为 `estimated_tokens > context_window - reserve`，估算优先用最近一次 API 实测 prompt_tokens 做锚点
- **效果**：marshmallow_1343 压缩次数 1 → 0，上下文全程 38.5K tokens（窗口 3.9%），PATCH 阶段历史完整保留

**面试话术**：
> "上下文压缩的触发阈值是 6 月 15 日定的 80K 字符，之后从未验证过。8 月底建观测管道，发现模型窗口其实是 1M tokens 不是 64K——旧阈值只占窗口 3.7%，压缩在长任务里从来都不是必要的，纯粹是被拍脑袋的阈值人为触发。修复后同等任务零压缩。这个案例的核心教训：拍脑袋的阈值不会自己变对，观测才会告诉你真相。"

### 5.5 代码定位增强（Code Intelligence）

- `search_graph`：查询代码结构图（AST 级别），替代盲目的文本 grep
- 可选 `codebase-memory-mcp` backend，无 backend 时自动降级
- graph hints 只作为定位 prior，不替代源码阅读和测试验证
- 单次 run 限 3 次 search_graph 调用

**量化**：v16 评测，graph-assisted localization token -258 avg，source top1 8/8，grep -67%

### 5.6 Spill 落盘机制（关键澄清）

**重要**：spill 的设计动机是「修复审计链完整性」（完整证据落盘），而非「上下文管理/省 token」。在后者上 spill 实际是负贡献——它让模型需要二次读取文件。

**面试时正确表述**：
> "spill 不是上下文管理的优化手段，是审计链完整性的保障。工具大输出超过 12K 字符时，完整内容落盘到 tool_outputs/，上下文只保留摘要。这样即使摘要丢失了细节，审计时仍能从落盘文件还原完整证据。后来我们做了实证验证——扫了 185 个 trace.json，发现 spill 从未在高价值输出（run_tests）上触发过，真正的信息压缩在工具层就已经完成了。"

---

## 6. 量化结果一览

| 指标 | 数据 |
|---|---|
| **SWE-bench Lite 官方 resolved** | **4/8 submitted**（官方 Docker harness） |
| **真实 GitHub issue** | **4/5 resolved**（tomlkit #411/#377、packaging #938、click#3449） |
| **Semi-real benchmark** | 132 条任务，13 条代表 run 全部 accepted_success |
| **回归测试** | 380 passes（pytest） |
| **Frozen set 稳定性** | `frozen_40` 连续 72+ 策略版本无回归 |
| **Tool routing 优化** | task_010 token **30,510 → 18,553**（-39%） |
| **Auto-verification 优化** | 5 个扩展任务 token 平均 **-27.4%** |
| **代码瘦身** | patcher.py 4736 → 231 行，policy 80 → 13 条 |
| **覆盖生态** | 9 个开源库（rich / jinja / click / jsonschema / packaging / tomlkit / watchfiles / anyio / dateutil） |

---

## 7. War Stories：13 个工程深度案例

> **面试策略**：不要全讲，选 3-4 个最精彩的在被问到「项目难点/踩过什么坑」时展开。以下是推荐优先级：

### 首推案例（按面试展示力排序）

#### 🥇 案例 1：search_graph 三连 bug — 把基础设施故障误诊成模型问题

**一句话**：工具上线 26 次 run 模型从不调用，先做 4 轮 prompt 干预全失败，最后发现是三个代码 bug——其中一个字段名不匹配，数据一直都在模型看到空数组。

**关键细节**：
- 工具单元测试 82 个全过，但**测试只覆盖了「调用后返回什么」，没覆盖「模型视角看到什么」**
- 三个 bug：死代码（赋值写在 return 之后）、phase gate 挡路（带 weak_static 的任务跳过 LOCALIZE 直接进 PATCH）、字段名不匹配（返回 `results` 但读的是 `matches`）
- 修复后：grep -67%、read_file -57%、总调用 -37%

**面试讲法**：「模型不配合时先怀疑基础设施」——这是全项目最好的一课。

---

#### 🥈 案例 11：max_tokens 语义变化 — reasoning 思考链烧完上限被误判为「模型罢工」

**一句话**：零输出被当成罢工，token 分解发现 completion 精确等于 8000——reasoning 思考链烧完 max_tokens 上限，输出根本没开始。

**关键细节**：
- **同一表象两种根因**：案例 2 的 kimi-k2.5 空响应是 `finish_reason=stop`（模型主动），本案例是 `finish_reason=length`（截断）
- **三层排查**：token 计数指纹（completion 精确撞线）→ finish_reason（一字千金，区分截断与主动停止）→ reasoning_tokens 分解（量化思考消耗）
- **max_tokens 语义变化**：instruct 模型约束可见输出；reasoning 模型约束思考链+输出总和。参数名没变，语义变了
- **四层防御**：配置层（8000→32000）+ 观测层（finish_reason 落 trace）+ 处理层（截断与空响应区分处理）+ 验证层（同输入重跑对照）
- **修复后**：click#3449 第五次 run 从 0 patch 变成 success，修复语义与官方 click 8.4.1 同构

**面试讲法**：「表象（零输出）≠ 根因；token 计数是客观证据，先看数字再下结论」——展示你具备系统级归因能力。

---

#### 🥉 案例 9：从未校准的阈值 — 字符估算在 1M 窗口下浪费了 96% 余量

**一句话**：上下文压缩阈值是两个月前拍的 80K 字符，建观测管道实测后发现模型窗口 1M tokens——旧阈值只占窗口 3.7%，每次压缩都在丢不该丢的上下文。

**关键细节**：
- **先观测不改**：先建 `_normalize_usage` 观测管道，收集 3 任务 46 次调用的实测数据
- **两个关键发现**：稳态 chars/token 比值 2.45（偏差 ±24%），窗口事实修正（64K → 1M）
- **结论**：旧阈值 80K chars ≈ 37K tokens = 3.7% 窗口，压缩**从来都不必要**
- 修复后同等任务压缩 1→0，PATCH 阶段上下文完整保留

**面试讲法**：「拍脑袋的阈值不会自己变对，观测才会告诉你真相」——展示你的数据驱动决策思维。

---

#### 专题：click#3449 五次 Run 弧线 — 完整工程叙事

这是一条贯穿三个 war story 的终极叙事线，最适合「讲讲你项目中最难的问题」：

| Run | 干预 | 结果 | 关键发现 |
|---|---|---|---|
| 1 | 无（基线） | incomplete，0 patch | 16 轮全部读代码，探索到死 |
| 2 | 提示式告警 | incomplete，0 patch | 告警被无视，提示式干预无效 |
| 3 | 硬约束（4 工具） | incomplete，0 patch | 告警后连续空响应，误判为「罢工」 |
| 4 | 硬约束（5 工具） | incomplete，0 patch | 同上，根因未发现 |
| 5 | 硬约束 + max_tokens 修复 | **success，1 patch** | 零空响应，模型自主切换合法路径 |

**面试讲法**：
> "click#3449 这个任务我们跑了五次，每次发现一个新根因。Run 1/2 确认了提示式探索告警对模型无效——这是系统级证据，提示改不了行为。Run 3 实施硬约束后模型空响应，初判是罢工。Run 4 加深怀疑。Run 5 前逐轮 token 分解发现 completion 精确等于 8000——finish_reason 揭露是 reasoning 思考链截断，不是罢工。修复后模型被拦截探索时自主转向了合法路径，产出与官方 click 8.4.1 同构的 patch。五次 run 的弧线证明了：硬约束有效，只是此前被截断 bug 完全掩盖。"

---

### 其他案例速览

| 案例 | 一句话 | 计量 |
|---|---|---|
| 2: 空响应假死 | reasoning 模型偶发零输出，agent 层加韧性重试而非改 prompt | 1/3 概率触发 |
| 3: token 收益被抵消 | 省 schema 被多出的轮次吃掉，优化方向从「省 schema」转向「省轮次」 | 2/5 任务反升 |
| 4: phase 死锁 | 状态机隐含假设「总有测试可跑」在真实仓库不成立 | 14+ 轮空转 |
| 5: None 崩溃 | 签名说可选实现说必填，3 行修复 | README 声称 367→实际 365 |
| 6: 协议双违规 | 宽松网关掩盖两个消息构造 bug，换 DeepSeek 官方 API 立刻 400 | 13 任务全挂 |
| 7: Windows harness 三连坑 | 宿主机/容器边界的路径分隔符 + CRLF ×2，0/8→3/8 | 跨平台边界 |
| 8: 三个潜伏违规 | 低频路径的 bug：重试从未被执行、压缩从未被触发、预检从未实战 | 一天 3×400 |
| 10: pydicom 翻盘 | 两个独立根因：patch 真缺陷 + 环境漂移，3/8→4/8 | F2P 3/3 |
| 12: tree-sitter 崩溃 | codebase-memory-mcp 在 751 文件 repo 上 parser 断言崩溃 | 983KB YAML |
| 13: read_file 死循环 | graph 给正确候选，模型对同一段代码重复读 7 次，tokens +170% | 确定性约束救命 |
| 14: spill 收益为零 | 扫 185 个 trace 验证「模型是否真的需要完整大输出」—不需要，选择不落地 | 拒绝修路 |

---

## 8. 失败分析与根因归因

### 失败模式三层分类

| 层 | 失败实例 | 状态 |
|---|---|---|
| **基础设施层** | 协议违规（400×3）、环境依赖（attrs 缺失）、max_tokens 截断 | ✅ 全部修复 |
| **系统行为层** | 探索无节流（click#3449）、重叠读（55% 冗余）、告警强度不足 | ⚠️ 部分完成 |
| **任务适配层** | 设计讨论类 issue（#1257）、定位策略缺陷（tomlkit#381） | ❌ 需任务预分类 |

### 改进闭环：jsonschema#1328 四次 Run

```
Run 1: 测试命令指向不存在文件 → 用户错误
Run 2: API 400 空 assistant 消息 → 代码 bug（协议违规）
Run 3: attrs 未安装 → 环境依赖缺失
Run 4: 全部修复就位 → success / full_verification_success / 7881 tests 零回归
```

**面试话术**：这是「失败→归因→修复→验证」完整闭环的最佳案例。

### 未解决的开放问题（面试时展示前瞻思考）

1. **重叠读检测**（~40 行）：三次独立验证（click#3449 57%/38%、#1257 55%）确认冗余
2. **读操作节流**（~30 行）：对称于写入侧反循环检测
3. **任务预分类**（~30 行）：识别设计讨论类 issue，警告用户非 bug fix
4. **预算升级从单次 hint 升级为强制 phase 转换**：到达阈值且 0 写入时直接把 phase 推到 patch

---

## 9. 高频面试问答

### Q1: 这个项目是做什么的？

A: 一个面向真实代码仓库的 AI Coding Agent。核心闭环是「理解 issue → 复现测试失败 → 定位代码 → 生成补丁 → 验证修复 → 输出可审计产物」。从 rule-based solver 演进而来，核心设计哲学是用确定性组件（tool_policy / phase gate / verifier）包裹概率性组件（LLM 语义理解和代码生成）。

---

### Q2: 为什么不用 Cursor/Copilot/Claude Code，要自己做一个？

A: Cursor 和 Copilot 是 AI 辅助编码工具，帮你更快写代码；Agentic SWE 是自主修复 agent——不需要人参与，输入 issue 自动完成全流程。Claude Code 的架构思路有相似之处（工具调用 + 上下文管理），但本项目更侧重**可审计性和安全约束**：phase gate 物理阻止跳过复现直接改代码、verification quality layer 区分 4 级验证强度、trace 全量落盘。这些是面向「agent 自主操作生产环境代码」的场景必需的工程保障。

---

### Q3: SWE-bench Lite 4/8 算好还是不好？

A: 诚实回答——这是小样本结果，不是完整 benchmark 通过率。4/8 submitted 在同类项目中是中间偏上水平（SWE-agent 早期约 12%，Devin 首次公开 13.86%），但我们的总任务量只有 10 条（其中 2 条未产出 patch）。更值得关注的是**单条任务的深度**而非广度——click#3449 五次 run 的工程叙事、pydicom-1139 的翻盘过程，比 resolved 数字本身更有面试展示力。

---

### Q4: 你觉得最核心的设计决策是什么？

A: 用确定性包裹概率性。LLM 是概率性的——你永远不能 100% 信任它返回正确的动作。所以架构的核心不是「信任模型」而是「假设模型会犯错，用确定性约束兜底」：
- tool_policy：物理阻止错误阶段的工具调用（如在 UNDERSTAND 阶段 write_file 直接返回 violation）
- phase gate：没有复现证据=进不了 PATCH 阶段
- verifier：不看模型的自我报告，只看测试结果

这就像一个 compiler 的 type system——不是让程序员不犯错，是让错误的代码通不过。

---

### Q5: 代码里有个 2654 行的 llm_agent.py，为什么不拆？

A: 因为 `run()` 方法用了大量闭包来管理 agent 的内部状态（工具执行、消息构建、上下文压缩等）。这些闭包是同一个执行上下文的紧密耦合体，拆分会破坏闭包的 capture 语义，引入额外的状态传递——风险高于收益。这是有意识的工程权衡，不是技术债务。如果有更充分的理由做重构（比如需要支持多 agent 并发），会从干净状态重新开始，而不是接手半迁移。

---

### Q6: 上下文压缩的设计思路是什么？

A: 三层递进。最底层是工具内部的**结构化消化**——run_tests 在返回前就提取了 failure_summary（failed tests、locations、exception），模型不需要看完整 pytest 输出。中间层是 **microCompact**——单个超大结果进入上下文前截断。最上层是 **token 预算驱动的智能压缩**——用 API 实测 prompt_tokens 做锚点估算上下文占用，超过 `context_window - reserve` 才触发摘要压缩。最大的教训是：阈值必须校准。旧阈值 80K chars 是两个月前拍的，实测只占 1M 窗口的 3.7%，每次压缩都在丢不该丢的上下文。

---

### Q7: 你在这个项目中学到了什么？

A: **最重要的教训是归因方法论**——"每个异常都值得一条 trace；每个修复都要能回答'怎么证明修好了'；每个'模型不行'的结论都要先排除'代码有 bug'"。

具体例子：search_graph 工具上线后 26 次 run 模型从不调用。我先做了四轮 prompt 干预全失败，最后发现是三个代码 bug——其中一个字段名不匹配。测试 82 个全过，但只测了「调用后返回什么」没测「模型视角看到什么」。从那之后我给每个新工具加入了从模型视角的端到端验证。

---

### Q8: 如果你重新做这个项目，会怎么设计？

A: 三个方向：
1. **先把验证质量分层做扎实**（full/targeted/weak/local_smoke），再优化其他能力——这是 agent 最核心的信任问题，本项目中我们确实把它放到了很高的优先级
2. **上下文管理从第一天就用 token 预算而非字符估算**——ADM-0002 的教训
3. **失败案例驱动开发**：先收集 5-10 个失败 trace，做根因归因，再决定改进优先级——而不是拍脑袋加功能。jsonschema#1328 的四次 run 是最好的证据

---

### Q9: 你的系统和其他 SWE agent（SWE-agent / OpenHands / Devin）有什么不同？

A:
- vs SWE-agent：我们多了 verification quality layer（防止假成功）、phase gate（防止跳过复现）、预算硬约束（防止探索到死）
- vs OpenHands：我们更偏工程化——不是所有工具都暴露，而是阶段性收窄，减少动作空间和 token 成本
- vs Devin：我们是开源/个人项目，没法比规模。但我们的小而精路线有自己的优势：每个 war story 都是可追溯的真实工程闭环，不是调参调出来的数字

---

### Q10: 后续打算改进什么？

A: 项目当前已收敛，面试准备阶段保持现状。但改进清单是明确的：
1. 重叠读检测（三次独立验证确认 55%+ 冗余）
2. 读操作节流（对称于写入侧反循环检测）
3. 预算升级从 hint 升级为硬约束（phase 强制转换）
4. 找更多有失败测试锚点的任务验证硬约束泛化性

方向是「关闭已发现的问题」而不是「加新功能」——每个改进都遵循「模式发现→归因→修复→重跑验证→数字对比」的闭环。

---

## 10. 速查卡片

### 核心数字

| 数字 | 含义 |
|---|---|
| 4/8 | SWE-bench Lite 官方 resolved |
| 4/5 | 真实 GitHub issue 成功 |
| 380 | 回归测试数 |
| 132 | Semi-real benchmark 任务数 |
| 72+ | Frozen set 连续无回归版本数 |
| -39% | Tool routing token 优化（task_010） |
| -27.4% | Auto-verification token 优化（5 任务平均） |
| 4736→231 | patcher.py 代码瘦身 |
| 13 | War stories 案例数 |

### 核心架构术语

| 术语 | 一句话解释 |
|---|---|
| Phase Gate | 阶段流转门禁：没复现证据就别想进 PATCH |
| Tool Policy | 阶段工具白名单：UNDERSTAND 阶段物理阻止写入 |
| Verification Quality Layer | 4 级验证强度，防止假成功 |
| Auto-Verification Loop | 写入后自动三级验证（diff→targeted→full） |
| 预算硬约束 | 75% 预算 0 写入时强制收窄工具列表 |
| Token Budget | API 实测 prompt_tokens 锚点驱动压缩判定 |
| 确定性包裹概率性 | 架构核心哲学：constraint > trust |

### 一句话讲清楚

> "我们做了一个能自主修复代码 bug 的 AI agent。它不像 Cursor 那样辅助你写代码，而是自己读 issue、定位代码、写 patch、跑测试验证，全程不需要人参与。核心创新是用硬编码的工程约束（阶段门禁、工具权限、验证质量分级）来包裹 LLM 的概率性输出，确保 agent 不会跳过复现直接改代码、不会把失败包装成成功。SWE-bench 官方 resolved 4/8，真实 GitHub issue 4/5，380 条回归测试，13 个有完整工程闭环的 war story。"

---

*文档基于 2026-09-10 的项目状态整理。面试时如需引用具体数字或案例，建议再打开对应源文件确认最新数据。*