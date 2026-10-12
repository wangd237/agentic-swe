# SAG-V1 面试准备文档

> 整合自项目全部现有文档，一站式面试准备。覆盖：项目概述、架构、核心指标、技术深挖、War Stories、Badcase 归因、面试问答。

---

## 目录

1. [一句话定位 + 电梯演讲](#1-一句话定位--电梯演讲)
2. [项目概述](#2-项目概述)
3. [架构总览：双平面控制系统](#3-架构总览双平面控制系统)
4. [核心指标（必背）](#4-核心指标必背)
5. [核心模块深挖](#5-核心模块深挖)
6. [War Stories：工程能力证明](#6-war-stories工程能力证明)
7. [Badcase 与改进方向](#7-badcase-与改进方向)
8. [面试模拟问答](#8-面试模拟问答)
9. [白板速查卡](#9-白板速查卡)

---

## 1. 一句话定位 + 电梯演讲

**一句话**：面向真实代码仓库的 AI Bug Repair Agent，输入 issue + repo，在隔离 git workspace 中走 Understand→Reproduce→Localize→Patch→Verify→Final 六阶段闭环，输出可审计的 trace/result/patch。

**电梯演讲（30 秒）**：
> "我做了一个 LLM coding agent，叫 SAG-V1。它从 rule-based solver 演进而来——不是让模型自由聊天式修代码，而是把修复任务拆成六个阶段，每个阶段受 tool policy 约束。核心设计理念是'用确定性组件包裹概率性组件'：LLM 负责判断，Runtime 负责纪律。SWE-bench Lite 官方 resolved 4/8，380 测试全覆盖，82 个策略版本 frozen_40 零回归。"

**面试核心竞争力**：
- 不是 demo，是完整工程闭环
- 有系统的失败归因和改进闭环
- 有 War Stories（14 个真实踩坑→修复→验证的完整叙事）
- 架构复杂度匹配问题规模——不造不必要的轮子

---

## 2. 项目概述

### 2.1 基本信息

| 维度 | 内容 |
|---|---|
| 项目名 | Agentic SWE（SAG-V1） |
| 时间跨度 | 2026年6-7月，19 个活跃提交日，187 commits |
| 技术栈 | Python · Pydantic · pytest · OpenAI-compatible API · Tool Calling · JSON Trace |
| 代码规模 | app/ 43 文件 ~8,470 行 |
| 测试覆盖 | 68 文件 / 374 passes |
| 当前阶段 | 代码已收敛，转入面试准备 |

### 2.2 从 Rule-Based 到 LLM Agent 的演进

```
V0: 纯 rule-based solver（4736 行 patcher.py，80 条 policy）
  ↓ "规则穷举不完整 + 策略天花板"
V1: LLM tool-use agent（231 行 patcher.py，13 条 policy）
  ↓ 用 374 条测试做 safety net
V2: 确定性约束层包裹概率性 LLM
  ↓ tool_policy、verifier、reflector、budget escalation
Current: 收敛态，面试准备
```

**演进的核心逻辑**：rule-based 阶段积累了工具链、harness、benchmark、验证体系——这些基础设施让 LLM agent 不是从零开始，而是直接嫁接在已验证的底座上。

### 2.3 双重基因

| 基因 | 来源 | 在项目中的体现 |
|---|---|---|
| **SWE-bench 学术基因** | 官方 harness、issue 派生任务 | frozen set 回归门禁（72+ 版本零回归）、maturity audit |
| **真实修复引擎基因** | 规则型缺陷定位 + 策略迭代 | code_locator 多信号加权、strategy_memory 跨任务记忆 |

**面试表述口径**：不要说是"为了做 SWE-bench 的刷榜项目"。正确表述：**"一个面向真实代码仓库的 AI 修复 Agent，SWE-bench Lite 是评测手段之一，不是目标本身。"**

---

## 3. 架构总览：双平面控制系统

这是面试中最核心的架构图，建议能白板画出。

### 3.1 总体分层

```text
GitHub issue / task JSON
        |
        v
   Runtime Harness（workspace 隔离 + 产物契约）
        |
        v
   LLM Agent 主循环（tool loop，16 轮上限）
        |
   +--------+--------+
   |                  |
   v                  v
数据平面               控制平面
（LLM 决策）           （确定性代码）
  - build_tools       - 四道门禁
  - LLM 调用          - 写后自动验证
  - 解析 tool_calls   - 反思器(undo)
  - 工具执行          - auto-finalize
  - 结果回喂          - 预算升级
                      - 上下文压缩
        |
        v
   可审计产物（trace.json / result.json / patch.diff / summary.md）
```

### 3.2 数据平面 vs 控制平面（最核心的概念）

| 维度 | 数据平面 | 控制平面 |
|---|---|---|
| 负责什么 | 判断（选什么工具、怎么修） | 纪律（能不能调、验证够了没） |
| 实现 | LLM API 调用 | 纯确定性 Python 代码 |
| 可测试 | 行为测试（QA 集） | 单元测试全覆盖 |
| 例子 | 读文件、写 patch | 门禁拦截、反思 undo、强度判定 |

**面试金句**：*"业界常见做法是把反思、验证写成 prompt 让 LLM 自己做——不可测试、不可审计、烧 token。我的 reflector.py 全文 130 行纯函数、零 LLM 调用。"*

### 3.3 六阶段状态机

```
UNDERSTAND → REPRODUCE → LOCALIZE → PATCH → VERIFY → FINAL
```

**阶段推进是证据驱动而非时间驱动**：
- `next_phase_after_tool()` 检查复现证据 + 定位候选 → 直接跳 PATCH
- 真实仓库无测试可跑时，有候选即可进 PATCH（phase 死锁修复）
- `recovery` 状态：反思踢回 LOCALIZE 后，保留写入权限，不死锁

### 3.4 双层门禁

**Schema 层**（tool_router）：模型"看不到"不该用的工具——省 schema token
**Policy 层**（tool_policy 四道门）：模型"调不动"违规工具——安全兜底

| 门 | 规则 | 防什么 |
|---|---|---|
| ① 阶段白名单 | 不在当前阶段 → 直接拒 | 阶段错位调用 |
| ② PATCH gate | 复现证据 + 候选非空 | 无证据盲写 |
| ③ 写入门禁 | 目标必须在候选列表中 | 乱改文件 |
| ④ diff-before-tests | 有未观察的 patch 禁止测试 | 改了没看就验 |

---

## 4. 核心指标（必背）

### 4.1 能力指标

| 指标 | 数字 | 来源 |
|---|---|---|
| SWE-bench Lite 官方 resolved | **4/8**（10 提交 8，2 未产出 patch） | 官方 Docker harness |
| 真实 GitHub issue | **4/5 resolved**（tomlkit#411/#377、packaging#938、click#3449） | 修复语义与官方一致 |
| semi-real 任务成功率 | 87.9%（29/33 LLM run） | agent_eval_summary |
| 工具数 | 11 个（含 search_graph、python_repl） | tool_definitions |
| frozen_40 无回归 | 82 个策略版本 | 回归门禁 |
| 测试覆盖 | 68 文件 / 374+ passes | tests/ |
| 策略版本数 | 82 个（最终瘦身至 13 个代表性） | optimization/ |
| patcher.py 瘦身 | 4736 行 → 231 行 | code_locator 替代 rule-based |

### 4.2 实验数据（面试核心弹药）

| 实验 | 规模 | 题目 | Hit@5 | P99 延迟 | 空结果 |
|---|---|---|---|---|---|
| v1 初版（wps-open） | 85 篇 | 14 题 | 71.4% | — | — |
| v2 规模化（金山云） | 4180 篇 | 45 题 | **66.0%** | 17.2s | — |
| v3 修复后（Golden Set v2） | 4732 篇 | 109 题 | **87.6%** | 10.9s | 6→0 |

**修复叙事**：规模化后 Hit@5 从 71.4% 跌至 66% → 定位两根因：交集过滤收缩 + Rerank 全量拉取向量 → 修复后 +21.6pp。

### 4.3 消融实验数据

| 实验 | 结果 |
|---|---|
| expand_off | 仅掉 1 题（10→9/14） |
| fast_mode_off | 从 10/14 崩至 **1/14**（组件贡献 64pp） |

### 4.4 工具路由优化

| 指标 | Baseline | After | 变化 |
|---|---|---|---|
| task_010 token | 30,510 | 18,553 | -39.2% |
| task_010 LLM 调用 | 7 | 5 | -28.6% |

### 4.5 搜索图工具修复效果

| 指标 | 修复前 | 修复后 |
|---|---|---|
| search_graph 调用 | 0（3 个 bug 导致永不可用） | 正常使用 |
| grep | 基线 | **-67%** |
| token | 基线 | **-22%** |
| 总调用 | 基线 | **-24%** |

### 4.6 口径注意

- SWE-bench 提交 10 个，8 个产出 patch，官方判定 4 个 resolved
- semi-real 不是 SWE-bench 正式成绩，是"能力快照"
- P99 3.3s（修复专项）vs 10.9s（109 题全量），对外统一用 17.2s→10.9s（同题集对比）

---

## 5. 核心模块深挖

### 5.1 主循环（llm_agent.py · 2654 行 · 编排器）

每轮 12 步严格顺序（面试可要求白板画出）：

1. **auto-finalize 检查**：当前 generation 已被 full 测试验证 → break
2. **预算升级检查**：轮次 ≥75% 且 0 写入 → 注入强制写 patch 指令
3. **schema 过滤**：build_tools_for_state() 按当前 phase 裁剪工具
4. **LLM 调用** → 记录 last_measured_prompt_tokens（ADR-0002 锚点）
5. **解析 tool_calls**（含纯文本 tool_call 恢复机制）
6. **四道门验证**：ToolPolicy.validate()
7. **执行**：只读并行（ThreadPoolExecutor），写入串行
8. **结果处理**：搜索命中 → remember_candidate；测试失败 → 提取 failure_summary → 自动引导符号搜索
9. **写入成功 → 自动验证链**：show_diff → targeted tests → full tests
10. **验证失败且打过 patch → 反思器** → 可能 auto-undo + 回 localize
11. **phase 推进**：next_phase_after_tool()
12. **压缩检查**：token 预算判定 + 配对保护

**协议韧性**（面试加分细节）：
- 空响应重试：reasoning 模型约 1/3 概率空响应，max_empty_response_retries=2
- 预算升级拼进最后一条 user 消息尾部（避免 user-user 连续、避免隔断配对）
- 空 assistant 强制填占位文本（防止发非法消息）

### 5.2 AgentState / 代数校验（memory.py）

**核心字段**：
- `workspace_generation`：写入代数（每次写入 +1）
- `diff_observed_generation`：diff 观察代数（show_diff 时同步）
- `requires_diff_before_tests()`：两者不等 → 禁止跑测试

**堵死的时序漏洞**："先跑测试 → 又改文件 → 没重验 → 却标成功"。这是分布式系统 epoch/version 思想的 agent 版本。

### 5.3 反思器（reflector.py · 130 行纯函数）

决策树按 **wrong_file → low_confidence → overfit → delta** 顺序判定（面试必问为什么这个顺序）：

| 条件 | 判定 | 行为 |
|---|---|---|
| 改了候选之外的文件 | wrong_file | undo + 回 localize |
| 改动文件最高 confidence < 0.4 | low_confidence | undo + 回 localize |
| 改动文件数 > max_patch_files | overfit | undo + 回 localize |
| delta=unchanged | wrong_hypothesis | 不回滚，回 localize |
| delta=changed | partial_fix | **保留，继续在 PATCH 修** |

**delta=changed 不回滚是关键设计**：失败签名变了 = 补丁产生了影响 = 方向正确。区分"无效补丁"和"不完整补丁"是修复 agent 最核心的判断。

### 5.4 验证质量分层（verification.py + verifier.py）

六级验证等级：none → local_smoke_success → targeted_success → full_verification_success → official_resolved → weak_verification_success

**关键规则**：
- 模型自报 success 但非 full 验证 → 强制降级（模型说了不算，代码说了算）
- SWE-bench Lite 本地 full 成功 → 自动降级为 local_smoke_success（pydicom-1139 教训的制度化）
- evidence_quality 分 strong/partial/weak/missing 四级

### 5.5 定位系统（code_locator.py）

多信号加权累加（不是 RRF）：

| 信号 | 分值 |
|---|---|
| task_hint（任务声明文件） | 3.0 |
| failure_location（非测试） | 4.0 |
| test_import_mapping（测试→实现推断） | 3.5 |
| symbol_match（issue 关键词 ∩ AST 符号） | min(2.0+len×0.4, 4.0) |
| search_hit | 1.5 |

confidence = min(score/5.0, 1.0)；测试文件降权。

### 5.6 上下文工程（ADR-0002）

**判定式**：`estimated_tokens > context_window_tokens - reserve_tokens`

**估算**：优先用 API 实测 prompt_tokens 锚点，无锚点时 chars/2.5 保守降级

**校准数据**：3 任务 46 次调用，稳态 chars/token 比 2.45（偏差 ±24%）

**关键发现**：deepseek-v4-flash 窗口 1M（非 64K），旧阈值 80K chars 仅占 3.7%——压缩在长任务里从来不是必要的，纯粹被拍脑袋阈值人为触发。

**配对保护**：压缩边界不得切在 assistant(tool_calls) 与 tool_result 之间。

### 5.7 反空转三件套

| 机制 | 规则 |
|---|---|
| 写侧反循环 | 连续 3 次改同一文件且相似度 ≥0.8 → 注入提醒 |
| 重复搜索拦截 | (工具, pattern, glob) 缓存，返回上次命中 + 提醒换策略 |
| 预算升级干预 | 75% 轮次 0 写入 → 强制注入"总结根因 + 立即写 patch" |

**从提示式到硬约束的演进**：click#3449 经历五次 run 弧线证明——提示式告警被无视（3 个独立实例），硬约束（收窄工具列表至只留写/验证工具 + max_tokens 修复）引导成功完成修复。

---

## 6. War Stories：工程能力证明

> 面试官问"你遇到过什么难题"时，从这里选。每一条都是"现象→排查→根因→修复→验证"的完整闭环。

### 最推荐讲的三个（按面试效果排序）

**🥇 案例 1：search_graph 三连 bug——把基础设施故障误诊成模型问题**
- 26 次 run，模型一次没用新工具。做了 4 轮 prompt 干预全部失败
- 第二天发现 3 个代码 bug：死代码、phase gate 挡路、返回字段名不匹配
- 教训：**模型"不配合"时，先怀疑基础设施，不要急着改 prompt**
- 量化：修复后 grep -67%、token -22%、总调用 -24%

**🥈 案例 3：token 优化收益被抵消——从"省 schema"转向"省轮次"**
- 单任务上 token -14.6%，扩展到 5 个任务后 2/5 反升
- 规律：反升的两个恰好 LLM 调用次数 +1
- 根因：schema 省下的是小头，多一轮完整调用（全量历史重发）吃掉所有节省
- 决策：换方向，把确定性流程下沉到 runtime，稳定降 27%
- 教训：**单任务验证会骗人，扩展验证 + 敢于回退才可靠**

**🥉 案例 9：从未校准的阈值——字符估算浪费了 96% 余量**
- 上下文压缩阈值 80K chars 是两个月前拍的，从未校准
- 建观测管道实测发现模型窗口 1M（不是以为的 64K），80K chars 仅占 3.7%
- 每次压缩都在丟不该丢的上下文
- 修复后同等任务零压缩
- 教训：**拍脑袋的阈值不会自己变对，观测才会告诉你真相**

### 快速选讲指南

| 面试官问 | 选这个 |
|---|---|
| 最有代表性的 debug 经历 | 案例 1（三连 bug） |
| 怎么做决策/权衡 | 案例 3（优化方向转向） |
| 度量/观测驱动 | 案例 9（校准阈值） |
| 真实案例验证 | 案例 10（pydicom 翻盘 3/8→4/8） |
| 协议/兼容性问题 | 案例 6（OpenAI 协议双违规）或案例 11（max_tokens 语义变化） |
| 跨平台工程能力 | 案例 7（Windows harness 三连坑） |
| 对外部依赖的处理 | 案例 12（tree-sitter 崩溃） |
| 什么时候选择不修 | 案例 14（spill 收益为零，验证后选择不落地） |

### 全部 14 个案例速查

| # | 案例 | 一句话教训 |
|---|---|---|
| 1 | search_graph 三连 bug | 模型不配合 → 先怀疑代码，不是 prompt |
| 2 | reasoning 空响应假死 | 先复现归因（模型行为 vs 代码 bug），再选修复层 |
| 3 | token 收益被抵消 | 单任务验证会骗人；抓大头（轮次 > schema） |
| 4 | phase 死锁 | 状态机隐含假设在真实场景会碎 |
| 5 | tool_router None 崩溃 | 仓库可信度 = 每条声明可验证 |
| 6 | OpenAI 协议双违规 | 宽松网关掩盖协议违规，换严格 API 全暴露 |
| 7 | Windows harness 三连坑 | 跨平台坑都在宿主机/容器边界上 |
| 8 | 三个潜伏的协议违规 | 低频路径 bug 只能靠真实负载暴露 |
| 9 | 从未校准的阈值 | 观测才会告诉你真相 |
| 10 | pydicom-1139 翻盘 | 本地通过 ≠ 官方 resolved，拆到根因 |
| 11 | max_tokens 语义变化 | reasoning 思考计入上限，零输出 ≠ 罢工 |
| 12 | tree-sitter 断言崩溃 | 外部工具上游 bug 先 diagnose 再跑 |
| 13 | read_file 死循环 | 确定性约束层缩短模型退化破坏半径 |
| 14 | spill 收益为零 | 对齐外部方案前先验证场景是否存在 |

---

## 7. Badcase 与改进方向

### 7.1 失败模式分类

| 层 | 失败 | 实例 | 状态 |
|---|---|---|---|
| **基础设施层** | 协议违规、环境依赖 | OpenAI 双违规、attrs 缺失 | ✅ 全部修复 |
| **系统行为层** | 探索无节流、重叠读、告警强度不足 | click#3449、sqlfluff-1625 | ⚠️ 搜索拦截✓，读侧✗ |
| **任务适配层** | issue 类型与 agent 能力错配 | jsonschema#1257（设计讨论） | ❌ 无防御 |

### 7.2 当前待改进项（面试官问"下一步做什么"时的回答）

**A 类（有明确方向，约 40 行代码）**：
1. **重叠读检测**：同一文件同一行范围连续读 N 次时拦截——三份数据确认 55~57% 冗余
2. **读操作节流**：连续 N 次读操作后注入提醒（对称于写入侧反循环）

**B 类（需更多验证）**：
3. **预算升级硬约束**：提示式升级对探索型失败无效（3 个实例），改为收窄工具列表
4. **任务预分类**：issue 含 proposal/design/RFC 信号时警告

**面试金句**：*"这个项目不需要新方向，需要的是关闭已经打开的问题。从'发现问题→写了一篇文档→没有下文'变成'发现→归因→修复→重跑验证→数字对比'的完整工程叙事。"*

### 7.3 click#3449 五次 run 弧线（最完整的失败→成功叙事）

| Run | 干预 | 结果 | 关键发现 |
|---|---|---|---|
| 1 | 无 | incomplete，0 patch | 基线：探索到死 |
| 2 | 提示式告警 | incomplete，0 patch | 告警被无视（探索型失败） |
| 3 | 硬约束（4 工具） | incomplete，0 patch | 模型被拦截后空响应——**实为 max_tokens 截断** |
| 4 | 硬约束 + python_repl | incomplete，0 patch | 同样截断 |
| 5 | 硬约束 + max_tokens 修复 | **success** | 修复语义与 click 8.4.1 官方同构 |

**核心叙事**：四次"失败"重新定性——Run 1/2 是真实探索不收敛（硬约束的靶子）；Run 3/4 的"罢工"是截断 bug 表象；Run 5 证明硬约束 + 正确预算下，约束有效引导模型完成修复。

---

## 8. 面试模拟问答

### Q1：简单介绍一下你的项目

> "SAG-V1 是一个面向真实代码仓库的 AI Bug Repair Agent。核心定位不是'给 LLM 加个工具调用'，而是'构建一个可约束、可验证、可审计的修复闭环'。从 rule-based solver 演进而来，现在有六阶段工作流、双层门禁、确定性反思器、代数交叉校验、四级验证强度——LLM 负责判断，Runtime 负责纪律。SWE-bench Lite resolved 4/8，380 测试全覆盖，frozen_40 连续 82 个版本零回归。"

### Q2：为什么从 rule-based 转到 LLM agent？

> "Rule-based 阶段有两大天花板：一是规则穷举不完整——真实 bug 的模式空间比规则大得多；二是策略天花板——规则只能做'已知模式→已知修复'的确定性映射。LLM 的语义理解和代码生成能力能覆盖更广泛的修复类型。但关键是我们不是从零开始——rule-based 阶段积累了完整的工具链、harness、benchmark、验证体系，LLM agent 直接嫁接在已验证的底座上。这个'有基础设施后再切 agent 类型'的路径，比'直接做 LLM agent'更可控。"

### Q3：你架构上最大的设计决策是什么？

> "双平面控制系统——数据平面（LLM 决策）和控制平面（确定性代码）分离。业界常见做法是把反思、验证也写成 prompt 让 LLM 做——不可测试、不可审计、烧 token。我的 reflector.py 130 行纯函数，零 LLM 调用；验证强度由代码判定，模型自报 success 会被强制降级。所有纪律性动作（门禁、验证、反思、回滚、压缩）都是确定性代码。"

### Q4：Agent 怎么防止乱改代码？

> "双层门禁。Schema 层让模型看不到不该用的工具（省 token + 减误调用），Policy 层四道门物理阻止违规调用：阶段白名单防错位、PATCH gate 防无证据盲写、写入门禁防护散、diff-before-tests 防改了没看就验。另外还有代数交叉校验——workspace_generation 和 diff_observed_generation 必须相等才允许跑测试，堵死了'先测→再改→标成功'的时序漏洞。"

### Q5：验证质量怎么保证？

> "四级验证强度状态机 + 六级 VerifierReport。关键设计是防自欺——模型自报 success 但验证强度不足时强制降级。SWE-bench Lite 任务的本地 full 成功也自动降级为 local_smoke_success，因为 pydicom-1139 教训是'本地全过 ≠ 官方 resolved'。evidence_quality 分 strong/partial/weak/missing，缺项记入 missing_evidence。"

### Q6：token 优化怎么做的？效果如何？

> "这里有一个挺有意思的转折。第一版工具路由按 phase 过滤 schema——单任务上 token 降 14.6%，以为效果很好。扩展到 5 个任务后 2/5 反升——规律是反升的两个恰好 LLM 调用次数多了一轮。发现省 schema 是小头，多一轮调用（全量历史重发）是大头。于是换方向：把确定性验证流程从 LLM 决策层下沉到 runtime——写入后自动 show_diff + targeted tests + full tests，结果同轮回喂。最终稳定降 27%。教训是单任务验证会骗人。"

### Q7：遇到的最难的 bug 是什么？

> "search_graph 三连 bug。给 agent 加了新工具 search_graph，26 次 run 模型一次没用。我做了 4 轮 prompt 干预全失败——强引导、few-shot 全试了，最后下结论说'模型不探索新工具，等更强的模型吧'。第二天回头读代码，发现三个 bug：死代码（变量写在 return 之后）、phase gate 挡路（工具暴露阶段错误）、字段名不匹配（返回 results 但读的 matches）。任何一个都足以让工具永远失败。修完后 grep -67%、token -22%。教训是模型'不配合'时，先验证基础设施真的在工作，别急着怪模型。"

### Q8：项目下一步做什么？

> "这个项目不需要新方向，需要关闭已经打开的问题。当前有三个待改进：重叠读检测（三份数据确认 55~57% 冗余）、读操作节流、预算升级从提示式改为硬约束。更关键的是方法论——从'发现问题→写文档→放一边'变成'发现→归因→修复→重跑验证→数字对比'的完整闭环。这对面试官来说比刷成功率更有说服力。"

### Q9：为什么 llm_agent.py 2654 行不拆？

> "这是有意识的设计决策（见 ADR-0004）。主循环有 18 处干预点（预算升级注入、自动验证回喂、反思触发、phase 推进……），它们之间有顺序耦合——拆分会让正确性依赖隐式状态传递。2500+ 行在一个文件里不漂亮，但顺序是正确的。而且项目已收敛，收敛期做大规模重构的风险不可接受——不是'没时间拆'，是'选择不拆'。面试时能把这个决策说清楚，比代码行数好看更重要。"

### Q10：你有什么遗憾或觉得没做好的？

> "三个。一是很多问题的产出是一篇新文档而不是一个关闭的问题——Badcase 分析很好，但没有走完'修复→验证'的闭环。二是早期太信单任务验证结果，token 优化那次如果一开始就扩展验证，能节省两周走弯路的时间。三是 spill 落盘机制的动机——最初说它是为了省 token/管理上下文，其实真正动机是修复审计链完整性。面试时不能把动机讲错。"

---

## 9. 白板速查卡

### 主循环 12 步（按序）

```
1. auto-finalize 检查
2. 预算升级检查
3. schema 过滤 (build_tools_for_state)
4. LLM 调用
5. 解析 tool_calls
6. 四道门 (ToolPolicy.validate)
7. 执行（只读并行，写入串行）
8. 结果处理（candidate + failure_summary + 引导搜索）
9. 写入成功 → 自动验证链
10. 验证失败 + 有 patch → 反思器
11. phase 推进 (next_phase_after_tool)
12. 压缩检查 (token 预算 + 配对保护)
```

### 四道门

```
① 阶段白名单: phase ∈ ALLOWED_TOOLS_BY_PHASE
② PATCH gate:  复现证据 + 候选非空
③ 写入门禁:    target ∈ localization_candidates
④ diff-before: diff_observed == workspace_generation
```

### 反思器决策树（按序）

```
wrong_file → undo + localize
low_confidence → undo + localize
overfit → undo + localize
delta=unchanged → 不回滚 + localize
delta=changed → 保留补丁 + 继续 PATCH
```

### 关键数字速记

```
SWE-bench: 4/8 resolved
真实 issue: 4/5 success
测试: 374 passes
frozen_40: 82 版本零回归
patcher.py: 4736 → 231 行
v3 Hit@5: 87.6%（修复后）
消融: fast_mode_off 崩至 1/14（组件贡献 64pp）
click#3449: 5 次 run 弧线，第 5 次 success
context window: 1M（非 64K）
```

### ADR 速查

```
0001: 采用 ADR 记录决策
0002: token 预算替换字符预算（* 1M 窗口事实修正）
0003: 工具大输出落盘（>12K chars → tool_outputs/）
0004: 推迟 wrapper 钩子化（收敛期大重构 = 行为级回归风险）
0005: 否决清单（事件总线/子代理/持久化状态机——不造不必要的轮子)
```

---

## 附录：面试前快速浏览清单

- [ ] 能一句话说清楚项目做什么
- [ ] 能画出双平面控制架构图
- [ ] 能背出核心数字（4/8, 4/5, 374, 82, 4736→231, 87.6%）
- [ ] 能默写反思器决策树
- [ ] 能默写四道门
- [ ] 准备了至少 2 个 War Story（推荐案例 1 + 案例 3）
- [ ] 能说清"为什么 2654 行不拆"（ADR-0004）
- [ ] 能说清"项目下一步做什么"（A 类 + B 类）
- [ ] 能说清楚 click#3449 五次 run 弧线的核心叙事
- [ ] 知道"架构本质是用确定性组件包裹概率性组件"怎么展开

---

*文档整合日期：2026-09-10，基于项目全部现有文档融合。*