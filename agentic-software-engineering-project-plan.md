# Agentic Software Engineering 项目实施规格书

## 1. 文档目的

本文件不是概念介绍，而是 `项目落地规格书`。


目标：

- 让代理能够在尽量少歧义的前提下，按步骤实现项目
- 让项目始终围绕同一个主线推进，不偏题
- 让每个阶段都有清晰的输入、输出、完成标准

本文档的额外定位是：

- 可以直接发给 `Claude Code` 或类似代码代理，作为项目实现的主规格
- 让代理在尽量少追问的前提下，能够按 phase 连续推进
- 让代理每次实现后都留下清晰的代码、文档、日志与验证证据

本项目的总代号为：

`Agentic Software Engineering for GitHub Issue Resolution`

该大项目由两个核心子项目组成：

1. `Mini SWE-Agent for GitHub Issues`
2. `Tool-Use and Patch-Quality Optimization for SWE-Agent`

---

## 2. 项目总目标

实现一个面向 `小型 Python 仓库` 的 AI Agent 系统，使其能够：

1. 接收一个 issue 或 bug 修复任务
2. 理解任务描述
3. 查看仓库结构
4. 搜索并读取相关代码
5. 生成修改方案
6. 修改代码
7. 运行测试
8. 输出修复结果
9. 记录完整轨迹
10. 对运行结果做评测与优化

最终应形成完整闭环：

`Task -> Agent Run -> Logging -> Evaluation -> Optimization -> Re-run`

除实现闭环外，本项目还应满足一个额外目标：

- 能够作为 `Agent / LLM Application / Applied AI / Evals` 方向实习求职中的核心项目，被清晰展示、复现和讲解

---

## 2.1 求职导向目标

本项目除了工程实现目标，还承担 `求职展示目标`。

项目最终不应只证明“能做出一个 Agent demo”，还应证明：

- 你理解 Agent 系统的基本组成：任务、工具、上下文、patch、测试、日志、评测、优化
- 你能把一个 Agent 系统做成 `可运行、可复现、可比较、可分析` 的工程项目
- 你能用实验数据说明某些设计为什么有效，而不是只展示功能存在
- 你理解真实 Agent 工程中的关键约束：成本、时延、稳定性、安全性、失败模式

因此，项目最终必须同时服务两个对象：

1. `实现者`：需要依据文档落地系统
2. `面试官 / 招聘方`：需要快速判断项目是否具备真实 Agent 工程价值

---

## 2.2 简历级成果目标

本项目完成后，至少应能沉淀出以下 `简历级证据`：

1. 一个可运行的 issue-resolution mini SWE-Agent
2. 一组结构化 benchmark tasks
3. 一套可复现的 baseline vs improved 对比实验
4. 一份可量化的结果报告
5. 若干可讲述的成功案例与失败案例

最终应能支持类似如下的项目表述：

`实现一个面向小型 Python 仓库 issue 修复的 mini SWE-Agent，构建任务、工具调用、patch、测试、trace、评测与优化闭环，并通过 prompt / policy 改进在固定 benchmark 上取得可量化提升。`

---

## 2.3 面向 Claude Code 的使用方式

如果将本文档直接交给 `Claude Code` 实现，默认采用如下工作方式：

1. Claude Code 必须先阅读本文档，再开始改动代码
2. Claude Code 必须严格按 phase 顺序推进
3. Claude Code 每次只实现当前 phase 的最小闭环，不得跨 phase 过度扩展
4. Claude Code 每完成一个 phase，都必须：
   - 更新代码
   - 更新对应文档
   - 提供运行命令
   - 提供可验证证据
5. 若文档中存在“推荐”和“必须”两类要求，优先满足“必须”
6. 若实际环境与文档假设不一致，Claude Code 应优先做最小可运行替代方案，并在文档中记录偏差

Claude Code 不应把本文档理解为纯 brainstorming 文档，而应理解为：

`一份要求按阶段实现、验证、记录和交付的执行规格`

---

## 3. 非目标

以下内容明确不属于第一阶段目标：

- 支持大型复杂多语言仓库
- 支持前端工程、Docker 重型环境或分布式系统
- 追求 SOTA 级别 benchmark 成绩
- 训练一个大模型
- 一开始就实现多代理协同
- 一开始就支持复杂多文件大规模重构

如果代理有额外时间，可以在主线完成后扩展；但在主线未完成前，不得优先实现这些内容。

---

## 4. 硬性范围约束

为避免项目失控，必须遵守以下约束：

### 4.1 仓库范围

- 仅支持 `Python` 仓库
- 仅选择 `小型或中小型` 仓库
- 仓库必须尽量容易运行测试
- 仓库必须有明确测试命令

### 4.2 任务范围

- 优先处理 `单 bug`、`函数级 bug`、`单模块 bug`
- 第一阶段允许只修改 `1 个文件`
- 第二阶段可放宽为 `少量文件`
- 不做“需求开发型大功能新增”

### 4.3 测试范围

- 默认使用 `pytest`
- 第一阶段优先跑目标测试
- 若环境允许，再扩展到全量测试

### 4.4 工具范围

第一阶段只允许依赖以下基础工具：

- `list_files`
- `search_code`
- `read_file`
- `run_tests`
- `write_file` 或 `apply_patch`
- `show_diff`

如果需要新增工具，必须先说明其必要性。

### 4.5 求职场景下的范围纪律

为了避免项目变成“看起来很大但做不完”的简历风险，必须遵守以下纪律：

- 主线完成前，不得把精力优先放在训练、多代理、前端展示、平台化部署
- 主线完成前，不得因为“想更真实”而盲目引入复杂仓库或复杂环境
- 任何增强项都必须以 `不破坏主线交付节奏` 为前提
- 若时间不足，优先保住 `baseline、improved、结果报告、失败分析`，而不是保住扩展功能

---

## 4.6 风险清单与修正原则

本项目在求职场景下存在以下常见风险，必须提前规避：

### 风险 1：项目范围过大，导致主线做不完

表现：

- 目录和设计非常完整，但缺少可运行结果
- 优化、训练、多代理等增强项挤占主线时间

修正原则：

- 始终先完成最小闭环
- 每个 phase 完成后立即留下可运行证据
- 扩展项必须显式标记为 `增强线`，不得与主线混淆

### 风险 2：benchmark 含金量不足

表现：

- 全部任务都来自自造 toy bugs
- 最终结果只能证明系统适配了自己设计的数据

修正原则：

- 自造任务只作为联调集，不应成为唯一正式结果来源
- 正式 benchmark 中必须包含一部分真实或半真实任务
- baseline 与 improved 必须在相同任务集上对比

### 风险 3：项目像 demo，不像实验型工程

表现：

- 只展示“能修一个 bug”
- 没有统计指标、错误分类、优化对比

修正原则：

- 必须输出量化指标
- 必须输出错误 taxonomy
- 必须至少完成一轮可解释的优化对比

### 风险 4：项目过度强调训练，削弱工程主线

表现：

- 提前进入 SFT / DPO / LoRA
- 训练实验很多，但 agent 主线和 eval 不扎实

修正原则：

- 训练永远是可选增强项
- 无 baseline / improved 报告前，不得将训练作为主卖点

### 风险 5：缺少真实 Agent 工程约束

表现：

- 不记录成本、时延、重试次数、上下文大小
- 不讨论 patch 安全和失败退出策略

修正原则：

- 从第一版开始记录工程运行指标
- 将安全性、可控性和退出机制纳入设计要求

---

## 5. 最终交付物

项目完成后，至少应包含以下交付物：

1. 一个主仓库
2. 一个可运行的 `Mini SWE-Agent`
3. 一个小型 benchmark 任务集
4. 一套轨迹日志
5. 一套评测脚本
6. 一份优化前后对比结果
7. 一份 README
8. 一份架构说明
9. 一份实验说明
10. 一份面向求职展示的结果摘要
11. 至少 2 个成功案例与 2 个失败案例分析

如果时间允许，可增加：

- 小规模 SFT 数据
- 小规模 preference 数据
- 轻量 LoRA / DPO 实验记录

说明：

- `10` 和 `11` 不是装饰性材料，而是求职时用于解释项目价值的重要交付物
- 若时间不足，优先保证结果摘要和案例分析存在，再考虑训练相关交付物

---

## 6. 推荐目录结构

代理在初始化项目时，应按以下目录组织：

```text
agentic-software-engineering/
  README.md
  GUIDE.md
  docs/
    architecture.md
    benchmark.md
    eval_design.md
    optimization.md
  app/
    agent/
      prompts.py
      planner.py
      executor.py
      policy.py
    tools/
      list_files.py
      search_code.py
      read_file.py
      run_tests.py
      write_file.py
      show_diff.py
    runtime/
      repo_session.py
      task_runner.py
      logger.py
    schemas/
      task_schema.py
      trace_schema.py
      result_schema.py
  benchmarks/
    tasks/
    repos/
    manifests/
  evals/
    metrics.py
    graders.py
    error_taxonomy.py
    batch_eval.py
    report_templates/
  optimization/
    prompt_versions/
    policy_versions/
    datasets/
    sft/
    dpo/
  logs/
    trajectories/
    test_runs/
    summaries/
  scripts/
    run_single_task.py
    run_batch.py
    generate_report.py
```

说明：

- 若实际实现略有不同，允许调整
- 但必须保留“执行层、任务层、评测层、优化层、日志层”这几个概念

## 6.1 必须创建的首批文件

为保证 Claude Code 能快速落地，初始化时至少应创建以下文件：

- `README.md`
- `GUIDE.md`
- `app/agent/prompts.py`
- `app/agent/planner.py`
- `app/agent/executor.py`
- `app/agent/policy.py`
- `app/tools/list_files.py`
- `app/tools/search_code.py`
- `app/tools/read_file.py`
- `app/tools/run_tests.py`
- `app/tools/write_file.py`
- `app/tools/show_diff.py`
- `app/runtime/repo_session.py`
- `app/runtime/task_runner.py`
- `app/runtime/logger.py`
- `app/schemas/task_schema.py`
- `app/schemas/trace_schema.py`
- `app/schemas/result_schema.py`
- `scripts/run_single_task.py`

第一阶段不要求所有文件都完全实现，但这些路径应尽早存在，避免后续结构反复调整。

## 6.2 目录职责约定

为减少 Claude Code 实现时的歧义，各目录职责固定如下：

### `app/agent`

- 放置 agent loop、prompt 生成、决策与执行控制逻辑
- 不应直接承担文件系统复制、日志持久化等底层职责

### `app/tools`

- 放置可被 agent 调用的工具包装
- 每个工具模块应暴露清晰、可测试的 Python 接口
- 工具层应尽量与模型调用逻辑解耦

### `app/runtime`

- 放置任务运行时、仓库副本管理、日志落盘、结果组织逻辑

### `app/schemas`

- 放置任务、trace、result 等结构化数据定义
- 如无特殊需要，优先使用简单、可序列化的数据结构

### `benchmarks`

- 放任务与样例仓库
- 原始 repo 应与运行副本分离

### `evals`

- 放指标统计、错误分类、批量评测、报告生成逻辑

### `optimization`

- 放 prompt 版本、policy 版本、可选训练数据与实验配置

### `logs`

- 放每次运行产物，不应手写编辑

### `scripts`

- 放面向用户或开发者的入口脚本

## 6.3 运行环境默认假设

除非用户另行指定，Claude Code 应按以下默认假设实现：

- 使用 `Python 3.10+`
- 使用 `pytest` 作为测试执行器
- 尽量使用标准库与轻量依赖
- 第一版优先保证本地命令行运行，不优先实现 Web UI
- 第一版优先支持 `JSON` 作为任务、trace、result 的交换格式

若引入第三方依赖，Claude Code 必须说明：

- 为什么需要该依赖
- 它解决了什么问题
- 是否存在更轻量替代方案

---

## 7. 核心术语定义

为避免歧义，统一采用以下定义：

### 7.1 Task

一条 bug 修复任务。包括：

- 仓库信息
- issue 文本
- 测试命令
- 成功标准

### 7.2 Agent Run

Agent 针对一条 task 的一次完整执行。

### 7.3 Trace

Agent Run 过程中每一步动作的结构化记录。

### 7.4 Patch

Agent 对代码仓库做出的修改。

### 7.5 Evaluation

对单次运行结果或批量运行结果进行质量评价。

### 7.6 Optimization

基于评测结果对 prompts、policy、grader 或训练数据做改进。

### 7.7 Baseline

未经过增强优化的初始系统版本。

### 7.8 Improved

在 baseline 基础上做过 prompt、policy 或 grader 改进后的系统版本。

---

## 8. 项目一：Mini SWE-Agent 的实施要求

## 8.1 项目目标

构建一个最小可运行的 SWE-Agent，用于自动完成小型 Python 仓库的 issue 修复任务。

## 8.2 输入

输入必须结构化为任务对象，至少包含：

```json
{
  "task_id": "task_001",
  "repo_name": "sample_repo",
  "repo_path": "benchmarks/repos/sample_repo",
  "issue_title": "Fix empty input handling",
  "issue_text": "Calling parse_items([]) raises an IndexError. It should return an empty list.",
  "test_command": "pytest tests/test_parser.py -q",
  "success_criteria": "Target tests pass without introducing new failures.",
  "difficulty": "easy",
  "tags": ["bugfix", "python"]
}
```

## 8.2.1 Task Schema 最低字段契约

Claude Code 实现时，`Task` 至少应满足以下字段约定：

- `task_id: str`
- `repo_name: str`
- `repo_path: str`
- `issue_title: str`
- `issue_text: str`
- `test_command: str`
- `success_criteria: str`
- `difficulty: str`
- `tags: list[str]`

推荐附加字段：

- `target_files_hint: list[str]`
- `expected_failure_test: str | null`
- `max_retries: int | null`
- `metadata: dict`

要求：

- 任务对象必须可序列化为 JSON
- 任务对象必须能被单文件加载
- 不允许把运行时生成字段混入原始 task 定义文件

## 8.3 输出

单次运行结束后，必须产出：

- 最终状态：成功 / 失败 / 部分成功
- 最终 patch
- 测试结果
- 轨迹日志
- 最终总结
- 本次运行的成本 / 耗时 / 工具调用统计

## 8.3.1 单次运行产物契约

每条任务完成后，Claude Code 至少应在对应 run 目录下落盘以下产物：

- `task.json`
- `result.json`
- `trace.json`
- `patch.diff`
- `summary.md`

若实现方便，建议再增加：

- `test_stdout.txt`
- `test_stderr.txt`
- `agent_messages.json`
- `metadata.json`

要求：

- 文件命名应稳定，便于批量评测脚本读取
- `result.json` 应作为单次运行的主结果入口
- `summary.md` 应用自然语言总结本次任务过程与结论

## 8.4 必备工具能力

### `list_files`

作用：

- 查看仓库结构
- 获取候选文件范围

### `search_code`

作用：

- 搜索函数名、错误关键词、变量名、测试名

### `read_file`

作用：

- 读取代码或测试文件内容

### `run_tests`

作用：

- 运行指定测试命令
- 返回退出码、标准输出、标准错误

### `write_file` 或 `apply_patch`

作用：

- 将 Agent 生成的修改写入任务仓库副本

### `show_diff`

作用：

- 查看本次任务中实际修改的内容

## 8.4.1 工具接口最低约定

Claude Code 在实现工具层时，应尽量让每个工具满足：

- 输入是显式参数，而不是隐式依赖全局状态
- 输出是结构化对象或字典，而不是仅返回裸字符串
- 工具错误要能区分“未找到”“命令失败”“权限问题”“超时”等类别

推荐接口风格如下：

```python
def list_files(repo_path: str, recursive: bool = True) -> dict: ...
def search_code(repo_path: str, query: str) -> dict: ...
def read_file(repo_path: str, relative_path: str) -> dict: ...
def run_tests(repo_path: str, command: str, timeout_sec: int = 120) -> dict: ...
def write_file(repo_path: str, relative_path: str, content: str) -> dict: ...
def show_diff(repo_path: str) -> dict: ...
```

其中每个返回值至少建议包含：

- `ok`
- `tool_name`
- `summary`
- `data`
- `error`

## 8.4.2 工具实现要求

各工具最低要求如下：

### `list_files`

- 支持返回相对路径列表
- 默认忽略明显无关目录，如 `.git`、`__pycache__`

### `search_code`

- 支持按关键词搜索代码文本
- 返回命中的文件路径与命中片段摘要

### `read_file`

- 返回文件文本内容
- 返回读取的相对路径
- 对过长文件可增加截断或分段策略，但需记录处理方式

### `run_tests`

- 返回退出码、stdout、stderr、耗时
- 需要能区分超时与普通失败

### `write_file` / `apply_patch`

- 只能写入当前 run 的工作副本
- 不得修改 benchmark 原始仓库

### `show_diff`

- 返回本次 run 相对于工作副本初始状态的差异
- 应便于落盘为 `patch.diff`

## 8.5 Agent 最小执行流程

每次运行必须遵循以下主流程：

1. 读取 task
2. 输出初步理解
3. 使用工具查看仓库和相关文件
4. 形成修复假设
5. 读取更多上下文验证假设
6. 生成 patch
7. 写入 patch
8. 运行测试
9. 观察测试结果
10. 若允许重试，则进行有限次数重试
11. 输出最终结果

禁止行为：

- 未读取相关文件就直接修改代码
- 修改后不运行测试就结束
- 无限循环调用工具
- 修改无关文件但不解释原因

## 8.5.1 Agent Loop 控制参数

第一版建议 Claude Code 直接实现一套明确的控制参数，避免无界执行：

- `max_steps = 12`
- `max_retries = 2`
- `max_files_to_read_before_first_patch` 可设为一个有限值
- `max_patch_files` 第一阶段建议限制为 `1`

说明：

- 这些参数可以在后续 phase 中调整
- 但第一版必须有硬上限

## 8.5.2 Agent 决策最小要求

在第一版中，Claude Code 不需要实现复杂 planner，但至少应实现以下决策节点：

1. 判断 issue 涉及的候选文件
2. 判断是否需要读取测试文件
3. 判断是否已有足够证据生成 patch
4. 判断测试失败后是继续重试还是结束
5. 判断当前修改是否偏离 issue 主线

如果短期内无法实现复杂推理，应优先用显式规则 + 简单 prompt 完成最小闭环。

## 8.6 Repo Session 约束

必须为每条 task 创建独立运行副本，避免污染 benchmark 原始仓库。

要求：

- 原始 benchmark 仓库只读保留
- 每次运行复制到工作目录后再修改
- 每次运行可独立清理

## 8.6.1 Run Directory 组织方式

推荐每次运行采用如下目录结构：

```text
logs/
  trajectories/
    task_001/
      run_001/
        task.json
        result.json
        trace.json
        patch.diff
        summary.md
        workspace/
```

其中：

- `workspace/` 是本次 run 的可写仓库副本
- 其他文件是本次 run 的日志与结果

要求：

- `run_id` 必须唯一
- 目录名必须稳定、可预测
- 批量评测脚本必须能够根据目录结构自动发现运行结果

## 8.7 Trace 记录要求

每次 Agent Run 都必须记录 trace。

建议结构：

```json
{
  "task_id": "task_001",
  "run_id": "task_001_run_001",
  "steps": [
    {
      "step_index": 1,
      "action_type": "tool_call",
      "tool_name": "search_code",
      "tool_input": {"query": "parse_items"},
      "tool_output_summary": "Found parser.py and tests/test_parser.py"
    }
  ],
  "final_status": "success"
}
```

必须至少记录：

- step index
- action type
- tool name
- tool input
- tool output 摘要
- patch 摘要
- test result 摘要
- final status
- 总工具调用数
- 总运行耗时
- 若可获得，则记录 token 使用量或近似成本

推荐附加记录：

- 本次读取的关键文件列表
- 本次 patch 影响的文件列表
- 重试次数
- 是否命中预设安全规则或退出规则

## 8.7.1 Trace Step 结构建议

Claude Code 实现时，建议每个 step 记录为统一结构：

```json
{
  "step_index": 1,
  "action_type": "tool_call",
  "tool_name": "search_code",
  "tool_input": {"query": "parse_items"},
  "tool_output_summary": "Found parser.py and tests/test_parser.py",
  "observation": "The parser implementation and related tests are both present.",
  "decision": "Read parser.py before editing.",
  "timestamp": "2026-06-04T00:00:00Z"
}
```

说明：

- `observation` 表示对当前结果的归纳
- `decision` 表示下一步动作理由
- 即使第一版没有复杂 reasoning，也建议保留这两个字段，便于后续评测

## 8.8 完成标准

Mini SWE-Agent 第一阶段完成的标准是：

- 能跑通至少 1 条任务
- 能生成并应用 patch
- 能运行测试
- 能保存 trace
- 能输出结果文件

第二阶段完成标准：

- 能批量运行多个任务
- 有稳定目录结构
- 有基础日志和错误处理
- 能输出最基本的运行统计信息

## 8.9 Claude Code 在项目一中的直接交付要求

当 Claude Code 实现项目一时，每个 phase 结束至少应交付：

### 代码交付

- 对应模块代码
- 入口脚本
- 必要的 schema 定义

### 文档交付

- `README.md` 中更新当前可运行能力
- `GUIDE.md` 中记录如何运行当前阶段

### 验证交付

- 至少一个可执行命令
- 至少一个真实运行结果样例
- 若失败，也要记录失败输出和原因

若缺少以上任一项，则视为该 phase 尚未真正完成。

---

## 9. 项目二：Tool-Use and Patch-Quality Optimization 的实施要求

## 9.1 项目目标

在 Mini SWE-Agent 运行结果的基础上，构建可复用的评测与优化系统。

## 9.2 输入

该项目的输入来自项目一生成的数据：

- task 数据
- trace 日志
- patch 结果
- 测试结果
- 最终状态

## 9.2.1 评测脚本读取约定

Claude Code 在实现评测系统时，应默认从 `result.json`、`trace.json`、`patch.diff` 读取核心信息。

要求：

- 不依赖人工复制粘贴结果
- 不依赖临时 print 输出作为唯一数据源
- 批量评测应能遍历 run 目录自动读取

## 9.3 输出

该项目至少要输出：

- 指标统计结果
- 错误分类结果
- baseline 评测报告
- improved 评测报告
- 对比结论
- 结果摘要页，用于 README 或求职材料展示

## 9.4 必做指标

### 结果指标

- `Success Rate`
- `Test Pass Rate`
- `Partial Fix Rate`

### 工具使用指标

- 是否读到关键文件
- 是否运行测试
- 是否存在重复无效搜索
- 是否在合理时机结束

### Patch 质量指标

- 修改文件数
- patch 是否过大
- patch 是否包含明显无关修改

### 效率指标

- 平均步数
- 平均工具调用数
- 平均每题耗时
- 若条件允许，增加平均 token 消耗或平均调用成本

## 9.4.1 指标计算最低约定

为避免评测口径不一致，Claude Code 实现时建议遵守：

- `Success Rate`：`final_status == success` 的比例
- `Test Pass Rate`：测试命令退出码为 `0` 的比例
- `Partial Fix Rate`：未完全成功但达到预设部分成功条件的比例
- 平均步数：trace 中 step 数的平均值
- 平均工具调用数：`action_type == tool_call` 的 step 数平均值

若引入更复杂指标，必须在 `docs/eval_design.md` 中明确定义。

## 9.5 错误分类要求

必须建立 `error taxonomy`，至少包含：

- `Wrong File Selection`
- `Wrong Root Cause`
- `Patch Incorrect`
- `No Test Execution`
- `Over-editing`
- `Premature Finish`
- `Looping / Repeated Search`

要求：

- 错误分类实现可以先从规则法开始
- 第一版不强制使用模型做 error labeling
- 但必须保证分类逻辑可复现、可解释

## 9.6 优化要求

优化必须分阶段进行，不能一开始就进入训练。

强制顺序：

1. `Prompt Optimization`
2. `Policy Optimization`
3. `Grader / Rule Optimization`
4. `Optional Light Post-Training`

### Prompt Optimization

目标：

- 让 Agent 更明确地先理解任务再行动
- 让 Agent 改前说明理由
- 让 Agent 改后强制跑测试

### Policy Optimization

目标：

- 限制无效工具调用
- 限制重复搜索
- 增加测试优先或测试校验策略

### Grader / Rule Optimization

目标：

- 未跑测试时不给高分
- 改动过大时发出警告
- 明显偏离 issue 时降低评分

### Optional Light Post-Training

目标：

- 基于 trace 构造少量监督样本或偏好样本
- 尝试小规模 LoRA / DPO

说明：

- 这一步是加分项，不是核心主线
- 若主线结果尚不稳定，不得优先投入训练实验

## 9.7 实验设计要求

至少要有两组实验：

### Baseline

- 原始 Agent
- 基础 prompt
- 基础 policy

### Improved

- 增强后的 prompt / policy / grader

可选第三组：

### Light Trained

- 加入 SFT 或 preference 优化后的版本

实验比较时必须遵守：

- 各组实验尽量使用相同任务集
- 各组实验必须明确记录模型、prompt 版本、policy 版本、运行参数
- 若存在人工介入，必须显式标注，不得与纯自动结果混淆
- 结果汇报中必须同时展示成功案例和失败案例，避免只挑选成功样本

## 9.8 完成标准

该项目完成的最低标准：

- 能对批量运行结果输出指标
- 能输出错误分类
- 能给出 baseline 和 improved 的对比
- 能明确说明哪些优化起作用

## 9.9 Claude Code 在项目二中的直接交付要求

当 Claude Code 实现项目二时，每个阶段至少应交付：

- 一个可运行的评测脚本
- 一个可阅读的结果文件或报告
- 一份明确的优化前后差异说明
- 至少一个被归类的失败案例

如果只能输出数字而无法解释数字背后的失败模式，则该阶段视为未完整完成。

---

## 10. benchmark 任务集要求

## 10.1 第一阶段数量

建议先准备：

- `5-10` 条最小任务用于联调

## 10.2 第二阶段数量

建议扩展到：

- `10-20` 条正式任务

## 10.3 任务来源

优先级如下：

1. 自己构造的简单 bug 任务
2. 小型开源仓库中的真实 issue
3. 有失败测试的公开教学仓库

不建议一开始直接选择复杂工业仓库。

补充要求：

- 联调集可以主要由自造任务构成
- 正式结果集不得全部由自造任务构成
- 正式结果集中，建议至少有一部分任务来自真实小型开源仓库或基于真实 issue 改写的半真实任务
- 每条任务都应尽量具备清晰测试命令与可验证成功标准

## 10.3.1 benchmark 有效性要求

为了让结果更有说服力，benchmark 至少应划分为两层：

### Debug / Dev Set

用途：

- 联调工具
- 调试 prompt
- 发现系统性错误

特点：

- 可包含较多自造简单任务
- 允许频繁反复使用

### Report Set

用途：

- 输出正式 baseline / improved 对比结果
- 用于 README、汇报与求职展示

特点：

- 不应只包含最容易的样本
- 不应全部由自造 toy bugs 组成
- 应尽量覆盖不同错误类型
- 在开始正式对比前尽量冻结任务集合，避免反复改题导致结果失真

## 10.4 每条任务必须包含的字段

- `task_id`
- `repo_name`
- `repo_path`
- `issue_title`
- `issue_text`
- `test_command`
- `success_criteria`
- `difficulty`
- `tags`

---

## 11. 实施阶段划分

以下阶段必须按顺序推进。

## Phase 0：项目初始化

目标：

- 建立目录
- 写初始 README
- 选定首个最小仓库

完成标准：

- 项目骨架存在
- 有 1 个可运行测试的 Python 仓库

Claude Code 本阶段必须完成：

- 创建目录结构
- 创建占位模块和入口脚本
- 确定一个最小 benchmark repo
- 在 `README.md` 与 `GUIDE.md` 中写明当前状态与后续计划

## Phase 1：观察型 Agent

目标：

- 实现 `list_files / search_code / read_file`
- 让 Agent 能理解问题并找相关文件

完成标准：

- Agent 能给出“应读哪些文件及原因”

Claude Code 本阶段必须完成：

- 实现 `list_files`
- 实现 `search_code`
- 实现 `read_file`
- 实现一个最小 task 加载与调用流程
- 保存最基本 trace

## Phase 2：测试闭环

目标：

- 实现 `run_tests`
- 将测试结果纳入决策

完成标准：

- Agent 能读取 issue、搜索代码、运行测试并总结失败现状

Claude Code 本阶段必须完成：

- 实现 `run_tests`
- 将测试结果写入 `result.json` 或等价结果文件
- 能在 summary 中说明“失败发生在哪里”

## Phase 3：Patch 闭环

目标：

- 实现 `write_file` 或 patch 应用
- 让 Agent 能自动尝试修复

完成标准：

- 至少 1 条任务自动修复成功

Claude Code 本阶段必须完成：

- 实现 `write_file` 或 patch 应用能力
- 记录 `patch.diff`
- 将修复前后测试结果都纳入结果文件

## Phase 4：批量运行

目标：

- 设计 task JSON
- 编写 batch runner
- 输出批量日志

完成标准：

- 能对多个任务连续运行并保存结果

Claude Code 本阶段必须完成：

- 实现 `scripts/run_batch.py`
- 支持遍历任务集
- 为每个 task 自动创建独立 run 目录

## Phase 5：评测系统

目标：

- 统计指标
- 分类错误

完成标准：

- 能输出 baseline 报告

Claude Code 本阶段必须完成：

- 实现 `evals/metrics.py`
- 实现 `evals/error_taxonomy.py`
- 实现一个最小可用的 `batch_eval.py`

## Phase 6：优化系统

目标：

- 做 prompt / policy / grader 优化
- 重跑 benchmark

完成标准：

- 能输出 improved 报告
- 至少有一个指标改进
- 能解释该改进来自哪些 prompt / policy / grader 变化

Claude Code 本阶段必须完成：

- 保存 baseline 配置
- 保存 improved 配置
- 明确对比两者差异
- 更新 `docs/optimization.md` 与 `docs/results.md`

## Phase 7：可选训练增强

目标：

- 构造数据
- 试做轻量训练

完成标准：

- 有小规模实验记录

说明：

- 若截至 Phase 6 时主线结果已经足够完整，可直接将项目视为求职可投递版本
- Phase 7 不是求职主线的必需条件

---

## 12. 代理执行时的约束规则

为了让 Claude Code 或其他代理实现时不跑偏，必须遵守以下规则：

1. 优先完成当前 phase 的最小闭环，再进入下一 phase。
2. 不得在主闭环未打通前，优先实现 UI、美化、复杂前端、部署平台。
3. 每增加一个模块，都要同时考虑：
   - 输入是什么
   - 输出是什么
   - 如何验证
4. 每完成一个 phase，都要留下可运行证据：
   - 脚本
   - 日志
   - 示例输出
5. 如果某个设计过于复杂，优先改成更小可运行版本，而不是卡住。
6. 若出现实现分歧，优先选择：
   - 更简单
   - 更容易验证
   - 更符合主线目标
7. 若某项增强不能显著提升求职展示价值，应降低优先级。
8. 每次正式实验必须保留可追溯配置，避免结果无法复现。

## 12.1 Claude Code 的执行协议

为了确保 Claude Code 真正按本文档实现，必须遵守以下协议：

1. 每次开始工作时，先声明当前目标 phase。
2. 每次只解决当前 phase 的最小闭环。
3. 先阅读现有代码和文档，再进行修改，不得盲写。
4. 代码修改后，必须运行当前阶段对应的验证命令。
5. 结果必须写回代码和文档，而不是只在对话里描述。
6. 若遇到实现阻塞，优先选择更小但可运行的实现，而不是停留在分析阶段。
7. 不得在没有明确收益的情况下重构整个项目结构。
8. 不得跳过日志、结果落盘、README 更新这些“非模型部分”的工程工作。

## 12.2 Claude Code 每轮输出要求

在每一轮较大改动后，Claude Code 的交付至少应包含：

- 改了哪些文件
- 当前 phase 达成了什么
- 用什么命令验证
- 还缺什么才能进入下一 phase

如果只提供“已经实现”而没有验证命令和结果证据，则视为交付不完整。

---

## 13. 推荐的实现优先级

实现优先级必须为：

1. 仓库与任务结构
2. 基础工具
3. 最小 Agent loop
4. 测试执行
5. patch 写入
6. trace 记录
7. batch run
8. metrics
9. error taxonomy
10. prompt / policy optimization
11. optional training

## 13.0.1 初始默认技术路线

若用户未另行指定，Claude Code 应优先采用以下最小路线：

1. 单 agent、单轮主循环 + 有限重试
2. 本地文件系统工具，不优先接入复杂外部服务
3. JSON schema + markdown summary
4. 规则约束 + prompt 驱动，而不是一开始就做复杂学习算法
5. 先完成单任务可运行，再做 batch，再做 eval，再做 optimization

---

## 13.1 工程现实约束

为了让项目更贴近真实 Agent 工程，应额外考虑以下约束：

### 模型与版本管理

- 必须记录每次实验所用模型名称与版本别名
- 若允许替换模型，必须保证评测报告能区分“模型变化”与“系统设计变化”

### 上下文控制

- 应记录一次任务中读取了哪些关键文件
- 应尽量避免无上限追加上下文
- 若设计了摘要或裁剪机制，必须在文档中说明策略

### 成本与时延

- 每次 batch run 应至少记录单题耗时
- 若条件允许，应记录 token 使用量、模型调用次数或近似成本
- 优化不应只看成功率，也要看成本和效率是否恶化

### 安全与可控性

- patch 写入前应有最基本的范围约束
- 不允许静默修改与 issue 无关的大量文件
- 应存在最大步数、最大重试次数、失败退出机制

### 结果可复现性

- 每次正式实验应保留任务集版本、配置版本、prompt / policy 版本
- README 或 docs 中应说明如何复现 baseline 与 improved

---

## 13.2 成果展示要求

项目最终不仅要“实现”，还要“易于展示”。

README 首页或结果摘要页至少应包含：

1. 项目一句话定位
2. 系统主流程图
3. benchmark 任务数量与来源概述
4. baseline vs improved 核心指标表
5. 1 个典型成功案例
6. 1 个典型失败案例及错误归因
7. 如何本地复现

推荐展示顺序：

1. 结果
2. 设计
3. 运行方式
4. 失败分析
5. 后续扩展

禁止把 README 首页写成只有目录结构和模块说明，而没有结果摘要。

---

## 13.3 面试讲解目标

项目完成后，至少应能够围绕以下问题给出清晰回答：

1. 为什么把问题限定在小型 Python issue 修复？
2. Agent 与普通代码补全或聊天式助手的差别是什么？
3. 你的工具集为什么这样设计？
4. 为什么要强制测试闭环和 trace 记录？
5. baseline 的主要失败模式是什么？
6. improved 版本到底改了什么，为什么有效？
7. 如果继续做下去，下一个优先优化点是什么？

如果一个项目最终做完后，无法清楚回答以上问题，则说明该项目虽然实现了部分功能，但求职说服力仍不足。

---

## 14. 文档要求

项目落地时至少维护以下文档：

- `README.md`
- `GUIDE.md`
- `docs/architecture.md`
- `docs/benchmark.md`
- `docs/eval_design.md`
- `docs/optimization.md`
- `docs/results.md` 或等价结果总结文档
- `docs/case_studies.md` 或等价案例分析文档

这些文档必须和代码同步更新，不能只写代码不写文档。

补充要求：

- `README.md` 必须优先呈现结果与定位，而不是只呈现目录结构
- `docs/results.md` 应记录 baseline / improved 的核心指标与结论
- `docs/case_studies.md` 应至少包含成功案例、失败案例、失败归因、下一步改进方向

---

## 15. 项目成功标准

当以下条件全部满足时，可以视为本主线项目基本完成：

1. Agent 能在小型 Python 仓库上执行 bug 修复任务
2. 有一组结构化 benchmark tasks
3. 有 trace 日志和结果文件
4. 有 batch run 能力
5. 有指标统计与错误分类
6. 有 baseline 与 improved 对比
7. 有完整文档可供他人复现
8. 有可直接用于求职展示的结果摘要与案例分析

如果再加上小规模训练实验，则属于增强完成版本。

若从 `求职可投递` 角度判断，则建议至少满足以下附加条件：

1. 正式结果不只依赖自造任务
2. README 首页有量化结果
3. 能讲清一个成功案例和一个失败案例
4. 能解释某次优化为什么带来指标提升
5. 能说明当前系统的主要局限，而不是只展示优点

---

## 16. 最终定位语句

这个项目的最终定位不是：

`我做了一个会聊天的编程助手`

而是：

`我实现了一套面向 GitHub issue 修复的小型 Agentic Software Engineering 系统，并围绕工具使用、补丁质量、轨迹评测和优化形成了完整实验闭环。`
