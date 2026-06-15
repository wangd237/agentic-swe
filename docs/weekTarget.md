# Target 2 & 3：验证改进 + 交付展示包

**当前状态**：Target 1 压力测试完成（14 条 / 85.7%）。Target 2 功能已提交（`f6e8f45`）且 3 条聚焦验证全部通过。Target 3 展示包已完成：4 条 case study、`docs/one_pager.md`、README 数字更新、文档链接检查和全量测试。

**原则**：不加新功能。验证刚做完的改进是否真实提升了修复能力，然后把证据打包。

**每周完成后必须做：将本轮的改进发现追加写入 `docs/agent_evolution.md`（不上传 GitHub）。**

---

## Target 2：聚焦验证 — 改进有没有用？

### Step 1：提交当前改动 ✅ 已完成（`f6e8f45`）

改动内容：`python_repl` 受控求值、`context_diff` 自动注入、反循环检测 + `ANTI_LOOP_MESSAGE`、强制反思 prompt、`max_iterations` 8→16、Windows GBK 编码修复。

### Step 2：跑 3 条验证任务 ✅ 已完成

不跑 14 条。只跑 3 条最能检验 Target 2 改进效果的：

| 任务 | 验证什么 | 成功标准 |
|------|---------|---------|
| `task_048` | python_repl + 循环检测 + 强制反思 → 是否打破领域盲区 | 从之前的不生成 patch → 生成 patch 或至少不再同方向打转 |
| `task_030` | context_diff → 是否减少格式精度失败 | 从之前的一次成功一次失败 → 稳定 success |
| `task_089` | 回归基线 — 简单任务不受影响 | success，tool calls 不增加 |

实际结果：

| 任务 | Before | After |
|------|--------|-------|
| `task_048` | `incomplete/max_iterations`, no patch | `success`, 11 calls, `run_20260615T074619354360Z_6882` |
| `task_030` | 曾 13 calls hit `max_iterations` | `success`, 12 calls, `run_20260615T081448691235Z_0502` |
| `task_089` | `success`, 7 calls | `success`, 6 calls, `run_20260615T081624552533Z_0056` |

对比：每条和 Target 1 的同任务 run 对比（tool calls / iterations / final_status / patch quality）。只增加了改进价值而不增加展示噪音。

### Step 3：根据结果决策 ✅ 已完成

- 如果 task_048 突破 → 继续 Target 3 ✅
- 如果 task_048 仍失败 → 分析 root cause，补一条针对性改进后再验证
- 如果回归基线退化 → 回滚对应改动

决策：`task_048` 已突破，`task_030` 与 `task_089` 均成功，无回滚项。进入并完成 Target 3。

### Target 2 验收

| 检查项 | 达标线 | 实际 |
|--------|--------|------|
| 提交 | Target 2 改动已 commit | ✅ `f6e8f45` |
| 验证 runs | 3 条完成 | ✅ |
| 对比 | 每条有升级前后对比 | ✅ |
| `agent_evolution.md` | 追加验证结果 | ✅ |
| `git status` | 干净 | 提交后检查 |

---

## Target 3：展示包 — 只做高频回报的事

Target 2 验证通过后，把项目推到面试就绪。不加文档量，加信息密度。

### 3.1 4 条 case study（不是 6 条） ✅ 已完成

选最能打的 4 条。每条必须有**决策链**（不是步骤列表，是「agent 在第 N 轮因为 X 选择了 Y」）：

- Case 1：`task_010` rich ANSI CRLF — 已有，补充决策链
- Case 2：`task_024` jinja2 静态分析 — 算法修复，不同 bug 类型
- Case 3：`task_132` rich Windows 编码 — 从 3 次 incomplete 到 harness 升级后 success
- Case 4：`task_048` — Target 2 已突破，选它

### 3.2 `docs/one_pager.md` ✅ 已完成

面试官 2 分钟文件。只放：
- Architecture diagram（ASCII，一张）
- 核心数字（一条 `<10` 行的表）
- 一个最能打的 case 缩略（带 patch 片段）
- Clone → run 3 行命令

### 3.3 README 数字更新 + 死链检查 ✅ 已完成

### 3.4 `agent_evolution.md` 收口 ✅ 已完成

覆盖 Phase 0 → Phase 5（Target 2 验证结论），不上传 GitHub。

### Target 3 验收

| 检查项 | 达标线 | 实际 |
|--------|--------|------|
| Case Study | 4 条，全含决策链 | ✅ |
| One-Pager | 存在，2 分钟可读完 | ✅ |
| README | 数字真实，链接无 404 | ✅ `missing_count=0` |
| 测试 | 全部通过 | ✅ `216 passed` |
| `agent_evolution.md` | 覆盖 Phase 0→5 | ✅ |
| `git status` | 干净 | 提交后检查 |

---

## 不做

- 不加新 benchmark 任务
- 不跑多模型（Kimi/GLM）
- 不加新工具（11 个够了）
- 不做 Reflection / multi-agent / Web UI / LangGraph
- 不加文档量（不写 known_boundaries.md、不写 failure_deep_dive 续篇——这些有价值但 ROI 低，stress_test_report 已经覆盖了核心边界）
