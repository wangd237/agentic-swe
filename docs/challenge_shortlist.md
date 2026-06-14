# Challenge Shortlist

本文件只保留“当前最值得作为 challenge 题继续推进”的候选。

它和 [docs/candidate_shortlist.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/candidate_shortlist.md) 的区别是：

- `candidate_shortlist` 更偏正式 benchmark 扩容
- `challenge_shortlist` 更偏系统边界展示

## 当前 challenge 选择标准

优先进入 challenge 集的题，一般满足至少一条：

- 原始 issue 对平台、环境、运行语境依赖较重
- 当前可以压成稳定本地回归，但和原 issue 的代表性还需要继续观察
- 问题本身更像“系统边界”而不是“正式主集规模扩容”
- 修复可能涉及较复杂的内部语义、较高的回归风险，短期内不适合作为正式 benchmark 门槛题

不优先进入 challenge 集的题：

- 单函数、单模块、边界清楚、可以稳定形成“旧版失败 / 新版成功”的题
- 更适合作为正式主集继续扩容的题

## 当前已落地 challenge 题

### `samuelcolvin/watchfiles#266`

- current_status:
  - 已进入 `task_126`
  - 已纳入 `real_issue_tasks_challenge_v1.json`
- why_challenge:
  - 原 issue 带明显的 `WSL / Docker / Windows 挂载` 语境
  - 虽然当前已压成稳定本地回归题，但先保守地独立承载更稳
- current_evidence:
  - `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v69.json --run-label challengev69`
  - `batch_eval_challengev69_001.json`

### `samuelcolvin/watchfiles#110`

- current_status:
  - 已进入 `task_127`
  - 已纳入 `real_issue_tasks_challenge_v1.json`
- why_challenge:
  - 原 issue 明确带有 `Windows + Ctrl+C + awatch` 的平台语境
  - 当前更适合作为 challenge hard case 持续观察，而不是直接并入正式主集
- current_evidence:
  - `python -m pytest benchmarks/repos/watchfiles_110_repo/tests/test_main.py -q`
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_127.json --policy optimization/policy_versions/improved_v69.json`
  - `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v69.json --run-label challengev69_r2`

### `samuelcolvin/watchfiles#169`

- current_status:
  - 已进入 `task_130`
  - 已纳入 `real_issue_tasks_challenge_v1.json`
- challenge_fit:
  - `environment-heavy`
- why_challenge:
  - 原 issue 明确带有 `WSL / Docker / Windows` 三重运行语境
  - 很适合作为“平台 / 环境边界”展示题，而不是直接并入正式主集
  - 和当前 challenge 集中的 `watchfiles#266 / #110` 同属 watchfiles 语境，但问题形态不同，更偏“变更事件完全不触发”
- current_evidence:
  - `logs/summaries/candidate_search_watchfiles_a3_001.json`
  - `benchmarks/real_world_candidates.json`
  - `benchmarks/tasks/task_130.json`
  - `benchmarks/repos/watchfiles_169_repo`
  - `python -m pytest benchmarks/repos/watchfiles_169_repo/tests/test_main.py -q`

### `samuelcolvin/watchfiles#215`

- current_status:
  - 已进入 `task_131`
  - 已纳入 `real_issue_tasks_challenge_v1.json`
- challenge_fit:
  - `environment-heavy`
- why_challenge:
  - 原 issue 带有明显的 `vim` 保存行为差异语境
  - 单文件 watch 下 `Remove(File)` 事件会让后续修改不再继续触发，这类“编辑器保存策略 + 事件归并”边界很适合作为系统展示题
  - 与现有 `#266 / #110 / #169` 的 challenge 题型不同，补上了“编辑器保存语义”这一条边界维度
- current_evidence:
  - `benchmarks/tasks/task_131.json`
  - `benchmarks/repos/watchfiles_215_repo`
  - `python -m pytest benchmarks/repos/watchfiles_215_repo/tests/test_main.py -q`
  - `logs/summaries/semi_real_pipeline_audit_challenge215_ready_001.json`

### `Textualize/rich#2411`

- current_status:
  - 已进入 `task_132`
  - 已纳入 `real_issue_tasks_challenge_v1.json`
- challenge_fit:
  - `platform-heavy`
- why_challenge:
  - 原 issue 明确带有 `Windows + subprocess + 控制台编码` 语境
  - 当前压成 Windows-like legacy 编码流上的最小安全降级语义测试后，能够稳定表达 `Console.rule()` / `Console.print("─")` 的平台输出边界
  - 和现有 watchfiles challenge 题型不同，补上了“控制台编码 / 字符降级”这一条新平台边界维度
- current_evidence:
  - `benchmarks/tasks/task_132.json`
  - `benchmarks/repos/rich_windows_rule_repo`
  - `python -m pytest benchmarks/repos/rich_windows_rule_repo/tests/test_console.py -q`
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_132.json --policy optimization/policy_versions/improved_v71.json`

## 下一轮 challenge sourcing 的方向

## 当前最值得补的 challenge 候选

下一条 challenge 题，优先从下面几类问题重新找：

- 平台 / 环境语境较重，但仍可压成稳定本地回归的题
- parser / formatter / control-flow 内部语义较复杂、回归风险较高的题
- 更适合展示系统边界，而不适合直接并入正式主集的题

优先来源建议：

- 新生态或当前覆盖较薄的生态
- 原 issue 自带明显环境边界的仓库
- 不与当前正式主集 `66` 条任务重复

## 当前推荐推进顺序

1. 继续观察 `task_126`、`task_127`、`task_130`、`task_131`、`task_132` 这五条 challenge 题的代表性和稳定性
2. 优先为第 `7` 条 challenge 候选重新做 sourcing，避免 challenge 来源继续过窄
3. 优先找新的平台 / 环境型 hard case，避免 challenge 线来源长期集中在 watchfiles 与少数生态
4. 如出现更适合正式主集的题，优先送回 formal 扩容链路
5. 避免把已经落地的 challenge 题继续留在 shortlist 候选区段

## 建议下一步动作

1. 继续跟踪 `task_127`、`task_130`、`task_131`、`task_132`、`task_133` 在 challenge 流水线中的表现，确认它们是否持续保持 hard case 价值
2. 优先从新生态里找带明显平台 / 环境边界的问题，避免 challenge 集来源过窄
3. 重点寻找与现有 watchfiles / rich 两条线不重复的平台、终端、路径或并发边界题
