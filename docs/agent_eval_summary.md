# Agent Eval Summary

本文档记录当前 LLM coding agent 的小样本真实运行结果。目标不是替代完整 benchmark，而是为求职展示提供一个清晰、可审计的 agent 能力快照。

## 1. Run 设置

- agent：OpenAI-compatible LLM coding agent
- policy：`llm_deepseek_minimal`；另有 `llm_deepseek_max1` 用于 failure taxonomy 受限运行
- model：`deepseek-chat`
- runner：`scripts/run_issue_agent.py`
- 当前已记录 LLM run：`33`
- 当前阶段样本选择原则：文件少、测试明确、覆盖不同库和缺陷类型；每批约 `5` 条后停下来抽检 diff

运行命令形态：

```bash
python scripts/run_issue_agent.py --task benchmarks/tasks/<task_id>.json --policy optimization/policy_versions/llm_deepseek_minimal.json
```

## 2. 结果表

| Task | Repo / Issue | 缺陷类型 | Status | Tool calls | Modified file | Run |
| --- | --- | --- | --- | ---: | --- | --- |
| `task_010` | `Textualize/rich#4090` | CRLF ANSI 行解析 | `success` | 6 | `rich_ansi_repo/ansi.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_010/run_20260614T080459321811Z_6319/result.json) |
| `task_019` | `dateutil/dateutil#1432` | UTC/GMT 零偏移回落 | `success` | 5 | `dateutil_tz_repo/tz.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_019/run_20260614T113332817562Z_3323/result.json) |
| `task_024` | `pallets/jinja#2069` | 分支赋值静态分析 | `success` | 6 | `jinja_meta_repo/meta.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_024/run_20260614T113402398598Z_5993/result.json) |
| `task_016` | `pallets/click#3111` | 负向 boolean flag 默认值 | `success` | 7 | `click_flag_repo/core.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_016/run_20260614T113438108363Z_4434/result.json) |
| `task_093` | `pallets/click#3572` | confirm 输出 ANSI 清理 | `success` | 6 | `click_confirm_repo/prompts.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_093/run_20260614T113509337696Z_0010/result.json) |
| `task_026` | `pallets/jinja#2118` | slice fill_with 整除边界 | `success` | 6 | `jinja_slice_repo/filters.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_026/run_20260614T125530440188Z_1570/result.json) |
| `task_028` | `python-poetry/tomlkit#494` | 数组追加逗号格式保真 | `success` | 6 | `tomlkit_array_repo/formatter.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_028/run_20260614T125722705788Z_9580/result.json) |
| `task_032` | `pypa/packaging#873` | wheel 版本 normalization | `success` | 7 | `packaging_wheel_repo/utils.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_032/run_20260614T125710781867Z_0410/result.json) |
| `task_034` | `python-jsonschema/jsonschema#1157` | mixed-type extras 错误消息 | `success` | 7 | `jsonschema_extras_repo/utils.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_034/run_20260614T125702622732Z_3132/result.json) |
| `task_038` | `python-jsonschema/jsonschema#1159` | integer-valued float multipleOf | `success` | 5 | `jsonschema_multipleof_repo/validator.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_038/run_20260614T125719275442Z_3582/result.json) |
| `task_040` | `pypa/packaging#885` | 复合 marker extra normalize | `success` | 5 | `packaging_requirement_repo/requirements.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_040/run_20260614T125937221880Z_6575/result.json) |
| `task_042` | `pallets/click#2958` | alias resolve_command None | `success` | 6 | `click_alias_repo/cli.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_042/run_20260614T125937121740Z_5271/result.json) |
| `task_044` | `dateutil/dateutil#1448` | MM.YYYY 返回顺序 | `success` | 6 | `dateutil_month_year_repo/parser.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_044/run_20260614T125938286589Z_6723/result.json) |
| `task_046` | `python-jsonschema/jsonschema#1163` | single-label hostname | `success` | 5 | `jsonschema_single_label_hostname_repo/hostname.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_046/run_20260614T125937737872Z_7122/result.json) |
| `task_048` | `pypa/packaging#886` | specifier dev+local 比较 | `success` | 11 | `packaging_specifier_repo/specifiers.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_048/run_20260614T125937936166Z_6625/result.json) |
| `task_050` | `dateutil/dateutil#1450` | attached comma year 解析 | `success` | 5 | `dateutil_attached_comma_repo/parser.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_050/run_20260614T130436831319Z_4726/result.json) |
| `task_052` | `python-jsonschema/jsonschema#1165` | ErrorTree 缺失索引污染 | `success` | 5 | `jsonschema_error_tree_repo/error_tree.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_052/run_20260614T130436877519Z_1176/result.json) |
| `task_123` | `agronholm/anyio#1109` | TaskGroup 重复进入 | `success` | 7 | `anyio/_backends/_asyncio.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_123/run_20260614T131623724272Z_2113/result.json) |
| `task_124` | `agronholm/anyio#1111` | 已完成 task cancellation spin | `success` | 10 | `anyio/_backends/_asyncio.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_124/run_20260614T131624574711Z_3381/result.json) |
| `task_125` | `agronholm/anyio#1113` | cancel scope 内取消语义 | `success` | 7 | `anyio/from_thread.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_125/run_20260614T131625493948Z_7238/result.json) |
| `task_128` | `agronholm/anyio#82` | 嵌套 task group 取消异常泄漏 | `success` | 8 | `anyio/module.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_128/run_20260614T131040931880Z_1322/result.json) |
| `task_129` | `agronholm/anyio#88` | 父任务额外取消 | `success` | 9 | `anyio/module.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_129/run_20260614T131624457541Z_1965/result.json) |
| `task_126` | `samuelcolvin/watchfiles#266` | ignore_permission_denied OSError 边界 | `success` | 8 | `watchfiles/main.py`, `tests/test_main.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_126/run_20260614T130318816140Z_7458/result.json) |
| `task_127` | `samuelcolvin/watchfiles#110` | Windows Ctrl+C stop_event | `success` | 8 | `watchfiles/main.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_127/run_20260614T130318467096Z_6062/result.json) |
| `task_130` | `samuelcolvin/watchfiles#169` | metadata-write reload 过滤 | `success` | 7 | `watchfiles/main.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_130/run_20260614T130318993474Z_8852/result.json) |
| `task_131` | `samuelcolvin/watchfiles#215` | 原子保存事件序列 | `success` | 7 | `watchfiles/main.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_131/run_20260614T130436617938Z_6416/result.json) |
| `task_133` | `Textualize/rich#2457` | Windows no_color 优先级 | `success` | 6 | `rich_windows_no_color_repo/console.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_133/run_20260614T130436324436Z_0074/result.json) |

## 3. 汇总指标

| 指标 | 当前结果 |
| --- | --- |
| 已记录 LLM run 数 | `33` |
| success 数 | `29` |
| incomplete 数 | `4` |
| 当前成功率 | `87.9%` (`29 / 33`) |
| 覆盖生态数 | `9` (`rich`, `dateutil`, `jinja`, `click`, `jsonschema`, `packaging`, `tomlkit`, `watchfiles`, `anyio`) |
| 平均工具调用数 | `6.7` |
| Challenge / boundary run 数 | `7` |
| incomplete_reason 覆盖 | `no_patch`, `max_iterations` |
| 所有成功是否有 patch | `yes` |
| 所有成功是否通过测试验证 | `yes` |
| 已人工抽检成功 patch | `29` 条 |

## 4. LLM Agent vs Rule-based Baseline

| Task | LLM status | LLM tool calls | Baseline status | Baseline tool calls | 观察 |
| --- | --- | ---: | --- | ---: | --- |
| `task_010` | `success` | 6 | `success` | 9 | LLM 独立定位 CRLF 根因，工具调用更少 |
| `task_019` | `success` | 5 | `success` | 10 | LLM 直接修复 UTC/GMT 无 offset 语义 |
| `task_024` | `success` | 6 | `success` | 9 | LLM 能处理轻量静态分析误判 |
| `task_016` | `success` | 7 | `success` | 12 | LLM 能解释负向 flag 与 default 的交互 |
| `task_093` | `success` | 6 | `success` | 10 | LLM 复用 echo 路径的 ANSI 清理语义 |

这组对比的重点不是证明 LLM 一定优于规则版 baseline，而是说明项目已经具备清晰双轨结构：LLM agent 是展示主角，rule-based solver 是稳定参照。

## 5. 扩展样本

| Task | Repo / Issue | 缺陷类型 | Status | Tool calls | Run |
| --- | --- | --- | --- | ---: | --- |
| `task_036` | `python-jsonschema/jsonschema#1121` | hostname 格式检查异常回落 | `success` | 5 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_036/run_20260614T115358297399Z_9685/result.json) |
| `task_099` | `pallets/jinja#2108` | macro include generator repr | `success` | 6 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_099/run_20260614T115439071151Z_9032/result.json) |
| `task_132` | `Textualize/rich#2411` | Windows-like legacy console 编码边界 | `incomplete` | 14 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_132/run_20260614T115513496398Z_8231/result.json) |
| `task_132` | `Textualize/rich#2411` | Windows-like legacy console 编码边界 | `incomplete / no_patch` | 14 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_132/run_20260614T130913910002Z_5098/result.json) |
| `task_054` | `pydantic/pydantic#9582` | 受限轮次 failure taxonomy | `incomplete / max_iterations` | 1 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_054/run_20260614T131946984622Z_9956/result.json) |

`task_132` 是当前最有价值的边界案例：测试一开始就已经通过，agent 没有生成 patch，最终状态保持 `incomplete`。这说明当前成功判定不会因为“测试通过”就误报修复成功，而是还要求有实际 patch 和当前 generation 的验证证据。

后续新 run 会在 `result.json` 中写入 `incomplete_reason`，用于区分 `no_patch`、`failed_tests`、`max_iterations`、`no_tests_run`、`unverified_patch` 等失败或边界类型。`task_132` 是该字段落地前的旧 run，因此当前 result 里没有 reason 字段。

新增 challenge run 中，`task_126 / task_127 / task_130 / task_131 / task_133` 均被 LLM agent 成功修复。`task_054` 使用 `llm_deepseek_max1` 受限策略，专门验证达到轮次上限时会写入 `incomplete_reason=max_iterations`，补足 failure taxonomy 的第二类真实产物。

## 6. 工具链升级 rerun

2026-06-15 按 [docs/weekTarget.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/weekTarget.md) 完成首轮工具链升级后，使用真实 OpenAI-compatible / DeepSeek API 重跑旧 incomplete run 所属任务。

| Task | 旧结果 | 新结果 | Tool calls | 关键观察 | Run |
| --- | --- | --- | ---: | --- | --- |
| `task_132` | `incomplete/no_patch`，旧 run `14` calls | `incomplete/no_patch` | `5` | 代码与测试已满足目标语义，agent 仍拒绝无 patch 成功；trace 第 2 轮 `read_file` 并行执行并带 `parallel_group_id` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_132/run_20260615T022726937782Z_5832/result.json) |
| `task_054` | `incomplete/max_iterations`，旧 run 为 `llm_deepseek_max1` 受限策略 | `success` | `9` | agent 使用 `edit_file` 两次修复 `extend()`，第一次测试失败时 `failure_summary` 暴露 `AttributeError`，第二次修正后 3 tests pass | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_054/run_20260615T022958080689Z_9857/result.json) |

对比摘要：

- 旧 4 条 incomplete run：`0 / 4` success，平均 `7.5` tool calls，平均 `28.84s`。
- 新工具链按唯一任务重跑 2 条：`1 / 2` success，平均 `7.0` tool calls，平均 `43.77s`。
- `task_054` 是明确正向证据：`edit_file` 减少全文件重写风险，结构化失败摘要帮助模型从中间错误收敛到正确 patch。
- `task_132` 是边界证据：工具链减少了观察工具调用，但任务本身在当前 repo 中已处于测试通过且无 patch 状态，继续保持 `no_patch` 是合理的保守判定。

## 7. 第一批人工抽检记录

| Task | 抽检结论 |
| --- | --- |
| `task_010` | CRLF 先归一化为 LF，避免 `\r` 被行解码逻辑误当作覆盖控制符 |
| `task_019` | UTC/GMT 缺省 offset 显式视为 `0`，再沿用原有符号变换逻辑 |
| `task_024` | 移除“已赋值变量仍强制加入 undeclared”的错误分支，符合分支赋值静态分析语义 |
| `task_016` | 未提供 flag 时返回原始 default，避免负向 flag 默认值被错误覆盖 |
| `task_093` | `color=False` 时复用 ANSI 清理逻辑，避免 confirm 输出泄漏控制码 |
| `task_036` | 空 hostname 返回 `False` 而不是抛底层 `ValueError`，符合格式校验失败语义 |
| `task_099` | 正确消费 include stream 并拼接输出，避免把 generator repr 渲染给用户 |
| `task_026` | `remainder > 0` 后才补 `fill_with`，符合 slice 整除边界语义 |
| `task_028` | 删除重复补逗号分支，符合 tomlkit 数组下一行逗号格式 |
| `task_032` | 拒绝前导零非 normalized 版本；实现偏最小，适合当前 semi-real 样本，泛化需谨慎 |
| `task_034` | mixed type 排序失败时保留原序渲染，避免错误消息生成抛 `TypeError` |
| `task_038` | integer-valued float 按整数取模，避免浮点精度误判 |
| `task_040` | 复合 marker 中统一规范化 extra 名称 |
| `task_042` | `cmd is None` 时直接返回，避免 alias 访问空命令 |
| `task_044` | 点号分支与斜杠分支统一返回 `(year, month)` |
| `task_046` | 允许 single-label hostname，同时仍拒绝空 label |
| `task_048` | local version 场景改为比较 public 版本，patch 窄且对齐目标测试 |
| `task_050` | 去除 token 中紧贴年份的逗号后再识别 4 位年份 |
| `task_052` | 缺失索引返回空 `ErrorTree` 但不写回内部 children |
| `task_126` | `ignore_permission_denied=True` 时吞掉 `OSError` 子类，并补充相邻测试 |
| `task_127` | 将 `stop_event` 传入阻塞 watch，支持中途停止 |
| `task_130` | 不再过滤 Linux-like `metadata-write` 目标事件 |
| `task_131` | 识别 `modify-name-from + remove` 原子保存序列并继续 watch |
| `task_133` | `no_color` 判断前置，避免 Windows legacy 分支绕过禁色 |
| `task_128` | 删除 asyncio/curio 的取消异常泄漏分支，统一保留原始嵌套失败语义 |
| `task_123` | 重复进入 `TaskGroup` 时抛出受控 `RuntimeError`，避免退出后状态缺失 |
| `task_124` | 已完成 task 从 cancellation 集合移除，避免无限重排 |
| `task_125` | 在 cancel scope 内抛出取消异常，避免泄漏 |
| `task_129` | 子任务失败后父任务清理流程不再被额外取消 |

## 8. 观察

当前样本覆盖了不同类型的修复：

- 文本解析边界：`task_010`
- 时区偏移语义：`task_019`
- 静态分析控制流：`task_024`
- CLI flag 默认值：`task_016`
- CLI 输出 ANSI 清理：`task_093`
- 序列化 / 格式保真：`task_028`
- 版本与 specifier 语义：`task_032`, `task_040`, `task_048`
- JSON schema 错误消息和数值语义：`task_034`, `task_038`, `task_046`
- watchfiles 平台 / 文件事件边界：`task_126`, `task_127`, `task_130`, `task_131`
- Windows legacy console 输出边界：`task_133`
- 并发 / task group 取消语义：`task_128`

当前最重要的结论是：LLM agent 已经不只是跑通单个 demo，而是在多个库、多类缺陷上完成了可审计的工具调用、patch 写入和测试验证闭环。

## 9. 当前边界

这仍然是小样本结果，不应夸大成完整 benchmark 通过率。下一步应该补：

- 当前尚未覆盖 `failed_tests` 和 `unverified_patch` 两类 reason；
- 后续如果继续补 failure taxonomy，应优先设计真实失败验证，而不是继续刷成功样本。
