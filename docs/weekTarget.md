# 三周 Goal：Agent 项目达到面试就绪

**总目标：三周后，这个项目可以直接放进简历，面试中打开给人看。面试官 5 分钟内能回答三个问题——这个 agent 做了什么、怎么做的、做得好不好。**

当前基线：harness 架构对齐 Claude Code（4 个 Phase 完成），39 LLM runs / 38 success，10 工具，git 原生工作区，规划先行，上下文压缩。

**每周完成后必须做：将本轮的改进发现（新增了什么、改了什么、为什么改、效果如何）追加写入 `docs/agent_evolution.md`。** 该文件是面试专用的设计演进记录，不上传 GitHub（已在 `.gitignore` 中排除）。

---

## Target 1：压力测试 — 找到当前 agent 的真实上限

**主题：把 agent 推到能力边界，收集失败证据和成功亮点，修复阻挡性问题。**

### 1.1 修阻塞 bug

- 修 `test_run_tests_returns_failure_summary` 的 Windows GBK 编码问题（当前唯一的自动化测试失败）
- 确认 `pytest -q` 全部通过

### 1.2 压力测试跑 14 条硬任务

选任务原则：覆盖不同库、不同 bug 类型、优先未跑过的 + 之前失败过的。

**酸测试（rerun）：**
- `task_132` — rich Windows 编码边界，3 次 incomplete/no_patch。升级 harness（grep + planning + 智能截断）后重跑，看能否突破
- `task_133` — rich Windows no_color，challenge 集未跑过的一条

**首次挑战（新任务，代表不同 bug 类型）：**
- `task_075` — jinja2 async repr，coroutine warning，需要理解异步语义
- `task_089` — jinja2 map default，模板 filter 链，逻辑密集
- `task_115` — pytest expression scanner，反斜杠解析，parser 级 bug
- `task_101` — tomlkit out-of-order table，TOML 规范语义复杂
- `task_030` — tomlkit inline table 损坏
- `task_056` — sqlite-utils delete_where 自动提交
- `task_057` — pydantic model validator 继承
- `task_058` — attrs alias 字段转换
- `task_097` — click progressbar 边缘行为
- `task_105` — pytest caplog filter 嵌套
- `task_109` — packaging name normalization

**回归验证（确认升级后不变差）：**
- `task_048` — packaging specifier，之前 11 tool calls success，看升级后工具调用数是否下降

### 1.3 压力测试分析

每条失败任务必须回答：
- 失败在哪个阶段？（定位阶段 / 修复阶段 / 验证阶段）
- 是模型能力问题还是 harness 问题？
- 如果改进 harness 能解决，标记优先级
- 如果模型能力不足，记录为已知边界

产出：`docs/stress_test_report.md`，包含 14 条任务的完整结果 + 失败根因分析 + 能力边界总结。

### 1.4 根据压力测试结果做一轮改进

如果发现了 harness 层面的共性问题（比如某个工具返回信息仍然不够好、context 压缩阈值不合理、prompt 在某种场景下有误导），立即改。如果是模型能力边界（比如 tomlkit 规范理解不够），记录下来但不在此轮解决。

### 1.5 落盘 agent_evolution.md

Target 1 完成后，将本轮所有改进发现追加写入 `docs/agent_evolution.md`（该文件不上传 GitHub）。

### Target 1 验收

| 检查项 | 达标线 |
|--------|--------|
| 测试 | `pytest -q` 全部通过 |
| 压力测试 runs | ≥ 12 条完成（允许部分因额度不足 skip） |
| 失败分析 | ≥ 3 条失败有根因分析 |
| 能力边界文档 | `docs/stress_test_report.md` 存在 |
| 改进 | ≥ 1 项 harness/prompt 改进源于压力测试发现 |
| `agent_evolution.md` | 已追加 Target 1 的改进记录 |
| git status | 干净（`agent_evolution.md` 不在 git 追踪中） |

---

## Target 2：多模型规模化验证

**主题：证明 agent 框架是模型无关的。换模型不掉链子。**

### 2.1 批量运行基础设施

- `scripts/run_multi_model_eval.py`：批量运行、限速、重试、断点续跑、不同模型并发
- 输入 manifest + 模型列表，自动产出 per-model 的 trajectory 目录

### 2.2 三模型跑 frozen_40

- 任务集：`benchmarks/manifests/real_issue_tasks_frozen_40_v1.json`（40 条）
- 模型：DeepSeek / Kimi / GLM
- 预计 120 次 API 调用

### 2.3 跨模型对比

- `scripts/aggregate_model_comparison.py` 产出聚合报告
- `docs/model_comparison.md`：三模型成功率、tool calls、duration、incomplete_reason 分布、交集分析（全成功 / 全失败 / 不一致）
- 不一致任务高亮 + trace 链接

### 2.4 失败深挖 + prompt 针对性优化

- ≥ 5 条失败 case 的 trace 级根因分析
- 基于分析做一轮 prompt 优化 + 验证

### 2.5 落盘 agent_evolution.md

Target 2 完成后，将多模型发现（跨模型差异、不一致分析、prompt 优化决策）追加写入 `docs/agent_evolution.md`。

### Target 2 验收

| 检查项 | 达标线 |
|--------|--------|
| 多模型批量脚本 | 可运行，支持断点续跑 |
| 完成 run 数 | ≥ 100 条 (task, model) pair |
| 跨模型报告 | `docs/model_comparison.md` 存在，含交集分析 |
| 失败深挖 | ≥ 5 条有根因分析 |
| `agent_evolution.md` | 已追加 Target 2 的多模型发现 |
| `git status` | 干净（`agent_evolution.md` 不在 git 追踪中） |

---

## Target 3：展示包打磨

**主题：把三周的成果打包成面试官可以在 5 分钟内理解的东西。**

### 3.1 Case Study 补齐

从压力测试 + 多模型对比中选 4 条最有代表性的成功案例，补充到 `docs/agent_case_studies.md`。每条含：问题、agent 决策链（为什么在那个时刻做了那个选择）、patch、验证。

选案例原则：覆盖不同库、不同 bug 类型、不同难度。优先选跨模型表现一致的（证明稳定性）和压力测试中突破的（证明升级有意义）。

### 3.2 失败案例 "Known Boundaries"

从压力测试和跨模型验证中，整理 3-5 条「已知边界」——agent 目前修不了的任务类型和原因。格式：场景描述 + agent 尝试了什么 + 为什么失败 + 可能的改进方向。

这份文档的价值不是在面试中「暴露弱点」，而是展示「我知道 agent 的边界在哪里」——这是工程能力的信号。

### 3.3 项目 One-Pager

`docs/one_pager.md`：面试官说「给我 2 分钟讲你的项目」时打开的文件。
- 一句话定位
- Agent 工作流（3 步 ASCII 图）
- 核心数字（39+ runs / X% success / 10 tools / 3 models / X ecosystems）
- 多模型对比结论（一句）
- 一个最能打的 case study 缩略版
- 架构简图
- 快速开始 3 行命令

### 3.4 README + 文档链接全面审计

- README Agent 能力表更新到最新数据（跨模型、总 runs、成功率）
- `docs/` 下所有交叉引用链接走一遍，确保无 404
- 旧文档（GUIDE.md、optimization_log.md）加「历史参考」声明

### 3.5 最终测试 + 清理

- `pytest -q` 全部通过
- `git status` 干净（`agent_evolution.md` 不在 git 追踪中，不上传 GitHub）
- `.env.example` 内容与实际配置一致
- `pip install -r requirements.txt` 后 `run_issue_agent.py` 一键跑通

### 3.6 agent_evolution.md 收口

将 Target 1 压力测试发现 + Target 2 跨模型洞察 + Target 3 展示层决策补进 `docs/agent_evolution.md`。最终版涵盖 Phase 0 → Phase 7 完整演进（含压力测试反馈循环和多模型验证发现），作为面试专用参考，**不上传 GitHub**。

### Target 3 验收

| 检查项 | 达标线 |
|--------|--------|
| Case Study | ≥ 6 条详细案例（含决策链） |
| Known Boundaries | ≥ 3 条有场景+尝试+原因+方向 |
| One-Pager | `docs/one_pager.md` 存在，2 分钟可读完 |
| README | Agent 能力表为最新真实数据 |
| 文档链接 | 全 docs/ 无 404 |
| 测试 | 全部通过 |
| 一键跑通 | clone → pip install → 配 .env → run 通过 |
| `agent_evolution.md` | 覆盖 Phase 0→7 完整演进（本地文件，不上传 GitHub） |
| `git status` | 干净（`agent_evolution.md` 始终不被 git 追踪） |

---

## 任务完成后项目状态总览

```
README.md              ← 面试官 30 秒扫完 Agent 能力
docs/
  one_pager.md          ← 2 分钟深度理解
  agent_overview.md     ← 架构、双轨、工具、验证策略
  agent_case_studies.md ← 6 条案例，不同库不同 bug 类型
  agent_eval_summary.md ← 跨模型数据
  model_comparison.md   ← 三模型交集分析
  stress_test_report.md ← 压力测试结果 + 能力边界
  known_boundaries.md   ← 已知失败模式
  weekTarget.md         ← 本文件
  agent_evolution.md    ← 面试专用：完整设计演进（不上传 GitHub，已 gitignore）

app/agent/              ← 10 工具 + git commit/reset + 规划先行 + 上下文压缩 + 智能截断
benchmarks/             ← 验证集（降级为配角）
scripts/                ← run_issue_agent + run_multi_model_eval + aggregate
```

## 不做

- 不加新 benchmark 任务
- 不做 Anthropic / Claude API 适配
- 不做 Reflection / multi-agent
- 不做 Web UI
- 不做 LangGraph
- 不做 Prompt caching（服务端自己处理）
