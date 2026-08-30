# Challenge Set

本文件用于单独记录当前 `challenge manifest` 的定位、内容和体验方式。

它服务的不是“正式 benchmark 扩容”，而是“系统边界展示”。

## 1. 当前定位

challenge set 用于承载这类任务：

- 已经压成可运行的 `semi_real` 任务
- 有明确展示价值
- 但暂时不适合直接并入正式主集

这类题通常满足至少一条：

- 原始 issue 带较重的平台、环境或上下文语境
- 当前本地缩题虽然稳定，但和原 issue 的代表性仍需要继续观察
- 更适合作为“系统边界案例”而不是“正式规模扩容证据”

因此 challenge set 的目标不是替代正式验证集，而是补一层 agent 边界展示：

- 正式集负责稳定、可对比、可累计的验证口径
- challenge 集负责表达系统边界、失败分类和保守候选

## 2. 当前 manifest

- `benchmarks/manifests/real_issue_tasks_challenge_v1.json`

当前任务数：

- `6`

## 3. 当前 challenge 任务

| task_id | 来源 issue | repo | 当前状态 | 说明 |
| --- | --- | --- | --- | --- |
| `task_126` | `samuelcolvin/watchfiles#266` | `watchfiles_266_repo` | `accepted + ready + in_challenge_manifest` | 原 issue 带 WSL / Docker / Windows 挂载语境；当前已压成稳定本地回归题，但先保守地放在 challenge 集 |
| `task_127` | `samuelcolvin/watchfiles#110` | `watchfiles_110_repo` | `accepted + ready + in_challenge_manifest` | 原 issue 带 Windows + Ctrl+C + `awatch` 平台语境；当前更适合作为 challenge hard case 持续观察 |
| `task_130` | `samuelcolvin/watchfiles#169` | `watchfiles_169_repo` | `accepted + ready + in_challenge_manifest` | 原 issue 带 WSL / Docker / Windows 三重运行语境；当前压成 Linux-like `metadata-write` 事件被错误过滤的最小环境边界回归题 |
| `task_131` | `samuelcolvin/watchfiles#215` | `watchfiles_215_repo` | `accepted + ready + in_challenge_manifest` | 原 issue 带 `vim` 保存行为语境；当前压成单文件 watch 把 `Remove(File)` 错当真实删除的最小编辑器保存边界回归题 |
| `task_132` | `Textualize/rich#2411` | `rich_windows_rule_repo` | `accepted + ready + in_challenge_manifest` | 原 issue 带 Windows + subprocess + 控制台编码语境；当前压成 Windows-like legacy 编码流上的最小字符降级回归题，补上控制台编码边界 |
| `task_133` | `Textualize/rich#2457` | `rich_windows_no_color_repo` | `accepted + ready + in_challenge_manifest` | 原 issue 带 Windows 10 + legacy console + `no_color` 语境；当前压成 Windows-like `legacy_windows + vt=False` 分支忽略 `no_color` 的最小颜色禁用回归题，补上控制台颜色禁用边界 |

## 4. 如何运行

### 4.1 跑整个 challenge 集

```bash
python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v71.json --run-label challengev71
```

当前真实产物：

- `logs/summaries/batch_run_challengev69_001.json`
- `logs/summaries/batch_eval_challengev69_001.json`
- `logs/summaries/batch_run_challengev69_r2_001.json`
- `logs/summaries/batch_eval_challengev69_r2_001.json`
- `logs/summaries/batch_run_challengev71_r3_001.json`
- `logs/summaries/batch_eval_challengev71_r3_001.json`
- `logs/summaries/batch_run_challengev71_r5_001.json`
- `logs/summaries/batch_eval_challengev71_r5_001.json`

如果只是沿用当前最新主版本，也可以直接运行：

```bash
python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v71.json --run-label challengev71_r1
```

当前结果：

- `challengev69`：
  - `task_count = 1`
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`
  - `average_duration_sec = 0.6472`
- `challengev69_r2`：
  - `task_count = 2`
  - 代表当前 challenge manifest 已扩到最小双题集合
- `challengev71_r3`：
  - `task_count = 3`
  - 代表 challenge 集已经扩到稳定三题集合；当前第 `4` 条已接入 manifest，下一轮应补四题全链路评测
- `challengev71_r5`：
  - `task_count = 5`
  - 代表 challenge 集已经扩到五题集合；当前下一步应切换为第 `6` 条 challenge 候选 sourcing
- `challengev72_r6`：
  - `task_count = 6`
  - `success_rate = 0.5`
  - `test_pass_rate = 0.5`
  - 代表 challenge 集已经扩到六题集合；当前下一步应切换为第 `7` 条 challenge 候选 sourcing

### 4.2 跑单条 challenge 任务

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_126.json --policy optimization/policy_versions/improved_v71.json
```

当前真实结果：

- `final_status = success`
- `patch_applied = false`
- `post_test_exit_code = 0`

## 5. 如何解读当前结果

`task_126` 当前更像一个“边界展示题”，而不是“正式扩容题”。

原因是：

- repo 当前已经是 ready 口径
- `improved_v71` 跑单任务时，pre-test 就已经通过
- 因此它不再满足“正式扩容题”通常需要的：
  - 带 bug 基线失败
  - 新策略修复成功
  这种强对比证据

但它依然有价值，因为它能清楚展示：

- challenge 题可以被独立承载
- challenge 题可以被独立运行和评测
- 系统边界案例不必强行混进正式 benchmark 主口径

## 6. 后续推进原则

当前 challenge set 的后续动作优先级如下：

1. 继续补第 `7` 条 challenge 题，形成更稳的边界展示集合
2. 对现有 challenge 题继续观察代表性是否足够强，尤其是新接入的 `task_133`
3. 只有在代表性与正式 benchmark 证据都足够强时，再考虑升格到正式集

当前找题 brief：

- `docs/challenge_sourcing_brief_a3.md`

不建议现在做的事：

- 为了凑正式任务数，把 challenge 题直接并入正式集
- 用 challenge 题替代正式集的 success / frozen / streak 主口径

## 7. 相关文件

- `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- `benchmarks/tasks/task_126.json`
- `benchmarks/tasks/task_130.json`
- `benchmarks/tasks/task_131.json`
- `benchmarks/tasks/task_132.json`
- `benchmarks/tasks/task_133.json`
- `benchmarks/repos/watchfiles_266_repo`
- `benchmarks/repos/watchfiles_169_repo`
- `benchmarks/repos/watchfiles_215_repo`
- `benchmarks/repos/rich_windows_rule_repo`
- `benchmarks/repos/rich_windows_no_color_repo`
- `scripts/run_challenge_eval.py`
- `logs/summaries/batch_run_challengev69_001.json`
- `logs/summaries/batch_eval_challengev69_001.json`
- `logs/summaries/batch_eval_challengev71_r5_001.json`
- `logs/summaries/batch_eval_challengev72_r6_001.json`
- `docs/challenge_sourcing_brief_a3.md`
