## Current Task: v17 改进实施

### 范围（来自架构审查，对照 Claude Code 源码验证）

从原 v17 6 项缩减到 3 项。P1 两项（四层权限、Skills）推迟/不做，P2 一项（子 Agent）推迟到 v18。

### P0-a: 工具定义统一只读/并发属性

**问题**：is_read_only / is_concurrency_safe 信息分散在三处硬编码集合：
- `llm_agent.py:49` `READ_ONLY_TOOL_NAMES`
- `tool_policy.py:10` `WRITE_TOOLS`
- `run_metrics.py:13` `WRITE_TOOLS`

加新工具需改 3 个文件，且信息不一致时不会报错。

**方案（对照 Claude Code 验证）**：
1. 在 `tool_definitions.py` 的每个工具 dict 中加两个 bool 字段：`"is_read_only"` 和 `"is_concurrency_safe"`
2. 在 `tool_definitions.py` 中新增导出函数：`read_only_tool_names()`、`write_tool_names()`、`concurrency_safe_tool_names()`
3. 删除 `llm_agent.py`、`tool_policy.py`、`run_metrics.py` 中的硬编码集合，改为调用导出函数

Claude Code 的做法一致——`getAllBaseTools()` 是单一真相来源，每个工具通过 `isReadOnly()` / `isConcurrencySafe()` 方法声明属性。我们比 Claude Code 更轻量：不用 Tool 基类，只在 dict 里加字段。

**影响面**：
- `app/agent/tool_definitions.py` — 11 个工具各加 2 个字段 + 新增 3 个导出函数
- `app/agent/tool_router.py` — 分组逻辑从硬编码改为调用导出函数
- `app/agent/tool_policy.py` — `WRITE_TOOLS` 改为引用导出函数
- `app/agent/llm_agent.py` — `READ_ONLY_TOOL_NAMES` 改为引用导出函数
- `app/agent/run_metrics.py` — `WRITE_TOOLS` 改为引用导出函数

**改动量**：约 20 行新增 + 10 行删除。风险：低。

---

### P0-b: 工具结果前置截断（microCompact）

**问题**：当前压缩是"等爆了再处理"——只在总字符超 `max_context_chars` 时一次性暴力压缩。可能导致中间轮次的关键工具结果被压缩掉。

**方案（对照 Claude Code 验证）**：
在现有压缩逻辑前增加一个额外步骤：遍历 messages，对最近的 tool_result 消息，如果单个 content 超过阈值（`max_tool_chars * 2`），截断到 `max_tool_chars` 并追加 `...[truncated]` 标记。如果截断后仍超阈值，fall through 到现有全量压缩。

Claude Code 的 microCompact 做的是更激进的事：直接把工具结果 content 替换为 `[Old tool result content cleared]`。我们更温和——只截断不删除。

**不改动的**：现有全量压缩（"留头+留尾+中间摘要"）保持不动。

**影响面**：`app/agent/llm_agent.py` 的 `compress_context_if_needed()` 闭包。

**改动量**：约 30 行新增。风险：低。

---

### P2: RunContext + 闭包重构（增量，选做）

**问题**：`run()` 方法有 17 个局部变量 + 11 个闭包，散落在 ~1700 行函数体内。闭包因需要使用 `nonlocal` 变量而不得不内联定义，无法单独测试。

**方案**：
1. 新增 `app/agent/run_context.py`，定义 `RunContext` dataclass，包含 17 个局部变量
2. 分 2-3 轮迁移闭包为类方法或独立函数
3. 每轮只迁移 3-4 个闭包，确保不破坏状态机逻辑

**当前不动，后续选一轮做。**

---

### 优先级与状态

| 优先级 | 改进项 | 工作量 | 状态 |
|--------|--------|--------|------|
| **P0-a** | 工具定义统一只读/并发属性 | ~30 行，低风险 | 待开始 |
| **P0-b** | 工具结果前置截断（microCompact） | ~30 行，低风险 | 待开始 |
| **P2** | RunContext + 闭包重构 | ~100 行，分 2-3 轮 | 后续选做 |

### 不做的（审查后排除）

| 原项 | 原因 |
|------|------|
| P1 四层权限模式 | 无真实用例，当前静态 ALLOWED_TOOLS_BY_PHASE 够用 |
| P1 Skills 体系 | 三个策略行为已独立模块化，不需要额外注册表 |
| P2 子 Agent 生命周期 | 推迟到 v18，当前无 multi-agent 用例 |
