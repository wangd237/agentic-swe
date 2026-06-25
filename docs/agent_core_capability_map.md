# Agent Core Capability Map

本文件用于把当前优化重新拉回 agent 主线：我们的目标不是做 benchmark runner，也不是围绕单个任务调参，而是构建一个能在真实 repo 中修复 bug 的 coding agent。

## 目标定义

最终目标：

```text
软件问题描述 + 真实 repo
  -> 隔离 workspace
  -> 理解问题
  -> 复现失败
  -> 定位代码
  -> 生成补丁
  -> 验证修复
  -> 输出可审计结果
```

SWE-bench Lite、semi-real tasks、token 统计都只是测量工具。它们的价值在于暴露 agent core 的能力缺口，而不是成为项目本身。

## 能力地图

```text
Input
  -> Observation Processing
  -> Agent State / Memory
  -> Tool Routing
  -> Execution Workflow
  -> Patch Generation
  -> Verification
  -> Reflection / Recovery
  -> Trace / Metrics
```

## 1. Input

职责：

- 接收本地 repo 路径、issue 描述、可选测试命令。
- 将 semi-real task、SWE-bench Lite task、用户本地 bug repair 都归一化为同一种 Task。

当前状态：

- `scripts/repair_bug.py` 支持用户本地 repo。
- `scripts/import_swebench_lite_task.py` 支持导入 SWE-bench Lite 单题。
- `scripts/export_swebench_prediction.py` 支持导出 SWE-bench prediction JSONL。

边界：

- GitHub clone / PR / issue crawler 是输入便利，不是当前 agent core 主线。
- SWE-bench Docker harness 是评测设施，不是 agent 本体。

## 2. Observation Processing

职责：

- 把工具返回的原始输出转成 agent 可用的结构化观察。
- 典型输入包括测试失败、traceback、pytest assertion、搜索结果、diff。

当前状态：

- `run_tests` 提取 `failed_tests`、`assertion_lines`、`locations`、`output_excerpt`。
- v9 新增 `exception` 和 `possible_symbols`，可从非 pytest traceback 中提取异常信号。
- `show_diff` 长 diff 会压缩，避免把大块 diff 直接塞回上下文。

近期经验：

- v9 提高了 grounding 质量，但单样本上未直接降低 token。
- 观察处理的目标不是总能降 token，而是让 agent 看得更准。

下一步候选：

- 更好地区分测试框架噪声、环境警告和真实失败。
- 从 traceback 中提取 import path、类名、函数名、异常类型之间的关系。

## 3. Agent State / Memory

职责：

- 记录当前 phase、失败签名、定位候选、已读文件、已改文件、验证强度。
- 避免 agent 只靠对话上下文隐式记忆。

当前状态：

- `AgentState` 记录 phase、failure signature、localization candidates、hypotheses、modified files、verification strength。
- `FailureSignature` 已纳入 exception / possible symbols / guided search。
- Strategy memory 可检索历史修复经验。

风险：

- 长期记忆如果过早做复杂，会把项目带向 memory system，而不是 bug repair 主流程。

下一步候选：

- 明确哪些状态是决策必要状态，哪些只是 trace/debug 信息。
- 减少 `llm_agent.py` 中重复更新状态的路径。

## 4. Tool Routing

职责：

- 控制不同阶段模型能看到哪些工具。
- 减少无关工具 schema token 和错误动作空间。

当前状态：

- v1/v2 实现 phase/state-aware schema filtering。
- v8 允许 `reproduce` 阶段使用只读 `grep/search_code`，解决真实 repo 中复现后无法定位的问题。
- 执行层 `ToolPolicy` 仍作为安全兜底。

经验结论：

- v8 是明确正收益：同样 16 步限制下，`pydicom__pydicom-1139` 从 incomplete 变为 success。
- 工具路由应优先服务“该阶段合理动作”，而不是单纯压缩工具数。

下一步候选：

- 将 phase tool policy 写成更容易审计的配置或表格。
- 给每个工具增加 phase-level rationale，避免后续随意放开动作空间。

## 5. Execution Workflow

职责：

- 将确定性工程动作从 LLM 决策层下沉到 runtime。
- 让 LLM 专注于判断和修复，而不是每一步机械流程都问模型。

当前状态：

- v3 实现 `edit_file/write_file` 后立即自动 `show_diff + run_tests`。
- v4/v4.1 尝试失败上下文自动加载，但未证明稳定收益，已回退。
- v10 尝试 failure signal guided search，原始策略过宽，v10.2 加了去重保护。

经验结论：

- v3 是稳定收益主线。
- v10 说明 runtime 自动动作必须克制；只要自动工具返回太宽，就会变成 token 成本。

下一步候选：

- 梳理“哪些动作应自动执行，哪些必须交给模型决定”。
- 对自动动作增加门控：高置信、低成本、可回滚、只读优先。

## 6. Patch Generation

职责：

- 让 agent 基于最新文件上下文做最小、安全、可验证的修改。

当前状态：

- `edit_file` / `write_file` 受 patch gate 控制。
- v6/v6.1/v7 提升 edit failure recovery，尤其是 `old_string_not_found` 的相似上下文建议。
- patch recovery state 允许失败修复后继续修补，而不是被 phase policy 卡死。

经验结论：

- 错误编辑带来的返工成本远高于几百 token 的 schema 压缩。
- 不应让工具自动替模型写入高相似补丁，风险高于收益。

下一步候选：

- 更强约束：编辑前必须基于最近 read_file 的片段。
- 区分“安全等价编辑”和“语义猜测编辑”。

## 7. Verification

职责：

- 判断 patch 是否真的修复问题，而不是模型自称完成。
- 区分 full / targeted / weak verification。

当前状态：

- `verification.py` 支持 verification strength。
- 写后自动执行 targeted/full tests。
- weak/static verification 不会被包装成普通 success。
- SWE-bench Lite smoke 可以导出 prediction JSONL，但不等同 official resolved。

风险：

- 最小复现命令可能过窄，导致 patch 本地 smoke 通过但不等价于 gold patch。
- 只追求本地 smoke success 会偏离真实 agent 目标。

下一步候选：

- 对每次成功输出 verification caveat。
- 增加 pass-to-pass 或回归测试意识，但不要先陷入完整 Docker harness 工程。

## 8. Reflection / Recovery

职责：

- 当 patch 后测试失败、失败签名未变、修改过宽或定位低置信时，自我纠错。

当前状态：

- `reflector.py` 支持结构化 reflection decision。
- 失败验证后可切回 localize、必要时 undo。
- repeated write loop 有检测和提示。

下一步候选：

- 将 reflection 触发条件从散落逻辑收束为明确 policy。
- 区分 wrong file、partial fix、test env、overfit 等失败类型的后续动作。

## 9. Trace / Metrics

职责：

- 让每次 agent 行为可复盘、可比较、可量化。

当前状态：

- trace step 记录 phase、state snapshot、evidence ids、verification strength。
- result 记录 LLM call count、token、tool routing、agent core metrics。
- `项目1改进记录.md` 记录 v1-v10 的实验与回退理由。

风险：

- 指标会诱导我们过度优化 token，而忘记修复质量。

下一步候选：

- 指标分层：能力指标优先，token 指标辅助。
- 每次优化必须同时记录成功率、验证强度、token、工具调用和是否改变安全边界。

## 主线优先级

当前最应该关注：

1. **Verification Quality**
   - 因为真实 agent 最怕“看起来修了，其实没修”。
   - SWE-bench Lite 中非 gold 等价 patch 已经暴露这个问题。

2. **Observation Processing**
   - 让 agent 看懂失败，比盲目增加工具更重要。
   - v9 属于这个方向。

3. **Execution Workflow**
   - 只把高置信、低风险、确定性的动作下沉到 runtime。
   - v3 是正例，v10 原始版是反例。

4. **Tool Routing**
   - 维持合理动作空间。
   - v8 是正收益，应保留。

暂缓：

- GitHub PR 自动化。
- Dashboard / leaderboard。
- 大规模 SWE-bench Docker harness 集成。
- 复杂长期记忆系统。
- 为单个 benchmark case 写规则。

## 下一步建议

下一阶段不建议继续做 v11 样本挖掘，也不建议继续围绕 `pydicom__pydicom-1139` 调参。

建议进入：

```text
Agent Core Refocus v2: Verification Quality
```

具体任务：

1. 设计成功判定分层：
   - local smoke success
   - targeted success
   - full verification success
   - benchmark official resolved

2. 在 result / summary 中明确输出验证等级和 caveat。

3. 对 SWE-bench Lite smoke 成功增加提示：
   - 本地最小复现通过；
   - patch 是否 gold-equivalent 未确认；
   - official harness 未运行。

4. 选 1-2 个已有成功样本，检查 patch 与 gold patch 的差异，并记录“本地 smoke success 不等于 resolved”的判断标准。

这一阶段能直接提升 agent 的可信度，比继续追 token 更接近产品化 agent 的主目标。
