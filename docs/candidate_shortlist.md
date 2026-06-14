# 候选短名单

本文件只保留“当前最值得推进”的候选 issue，避免每次都从完整候选池重新筛。

筛选依据：

- 符合 `docs/issue_sourcing_spec.md`
- 尽量单函数 / 单模块
- 容易缩成 `1` 到 `3` 个稳定回归测试
- 能与现有 benchmark 类型形成增量，而不是重复

## 当前状态

- 当前已经完成一轮 A2 定向扩新来源搜索，并导入了第一批新候选
- `fsspec/filesystem_spec#979` 已经从新来源候选推进为 ready 口径的 semi_real 任务 `task_122`
- `fsspec#979` 已经完成正式 manifest 接入与 `improved_v64` 三线最小验证
- `agronholm/anyio#1109` 已推进为正式 semi_real 任务 `task_123`
- `task_123` 已完成 `improved_v65` 三线最小验证，并把正式任务数推进到 `62`
- `agronholm/anyio#1111` 已推进到 `accepted`，并已完成正式任务 `task_124` 接入
- `task_124` 已完成 `improved_v66` 三线最小验证，并把正式任务数推进到 `63`
- 当前最高优先级已经从 `anyio#1111` 切到继续补并发与协程家族的下一条候选，优先看 `anyio#1113`
- `anyio#1113` 已从 `imported` 推进到 `screened`
- 已利用 `scaffold_semi_real_task.py --from-candidate` 生成初版脚手架：
  - `benchmarks/tasks/task_125.json`
  - `benchmarks/repos/anyio_check_cancelled_repo`
- `anyio#1113` 当前已经继续推进到 ready bug repo 阶段：
  - 正常路径测试 `1` 条通过
  - 目标回归测试 `1` 条失败
  - 下一步可以直接进入“旧策略失败 / 新策略成功”的单任务验证
- `anyio#1113` 现已完成：
  - `improved_v68` 单任务失败
  - `improved_v69` 单任务成功
  - 正式 manifest 接入
- 已顺手增强脚手架自动推断：
  - 当 issue 文本只给 Python 符号名时，现在会尝试把 `from_thread.check_cancelled` 这类符号还原成 `anyio/from_thread.py`
- 当前扩新来源时，优先使用：
  - [docs/issue_sourcing_brief_a2.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/issue_sourcing_brief_a2.md)
  - [docs/issue_sourcing_spec.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/issue_sourcing_spec.md)

当前推荐的补位方向已经不是泛泛地“继续找 bug”，而是：

- `并发与协程`
- `文件路径与 IO`
- 其次是来自新生态的 `继承、优先级与控制流`

补充说明：

- `2026-06-13` 已基于本地搜索产物补入新的 anyio 并发候选：
  - `agronholm/anyio#82`
  - `agronholm/anyio#88`
- 其中 `agronholm/anyio#82` 已完成一轮人工筛选，状态推进到 `screened`
- `2026-06-14` 已继续为 `agronholm/anyio#82` 生成 semi_real 脚手架：
  - `benchmarks/tasks/task_128.json`
  - `benchmarks/repos/anyio_82_repo`
- `2026-06-14` 已进一步完成 `agronholm/anyio#82` 的单任务修复验证与正式接入：
  - `improved_v70` 单任务失败
  - `improved_v71` 单任务成功
  - 已纳入正式 manifest
- `2026-06-14` 已继续把 `agronholm/anyio#88` 从 `imported` 推进到 `screened`
- `2026-06-14` 已继续为 `agronholm/anyio#88` 生成 semi_real 脚手架：
  - `benchmarks/tasks/task_129.json`
  - `benchmarks/repos/anyio_88_repo`
- 这意味着 A2 扩容线已经重新从“主集已吸收的旧题”切回“可继续推进的新候选”

## 当前高优先级 shortlist

### `fsspec/filesystem_spec#979`

- family:
  - `文件路径与 IO`
- current_status:
  - `accepted`
- why_it_fits:
  - `unstrip_protocol` 的错误行为非常清晰，像典型的单函数路径语义 bug
  - issue 正文已经给了最小复现和期望行为，最适合压成 1 到 3 个稳定回归测试
- expected_target_files:
  - `fsspec/spec.py`
  - `fsspec/tests/test_spec.py`
- expected_test_shape:
  - 覆盖 `abstract-file`、`s3-file`、`s3a-file` 这类前缀边界输入
- current_progress:
  - `scaffold_semi_real_task.py --from-candidate --dry-run` 已跑通
  - 已补 target file 提示，并成功执行非 `dry-run`
  - 已生成：
    - `benchmarks/tasks/task_122.json`
    - `benchmarks/repos/fsspec_unstrip_protocol_repo`
  - 已把 TODO 模块与 TODO 测试补成稳定回归任务
  - 当前 repo 内回归测试已通过
- recommendation:
  - `已完成 ready 化，可视情况纳入正式集`

### `agronholm/anyio#1109`

- family:
  - `并发与协程`
- current_status:
  - `accepted`
- why_it_fits:
  - “重复进入 task group context 触发 AttributeError” 的错误边界比较具体
  - 比较有希望压成单模块行为回归，而不是重时序问题
- expected_target_files:
  - `anyio/_backends/_asyncio.py` 或 task group 相关模块
- expected_test_shape:
  - 1 到 2 个 task group 复入场景测试，确保从 `AttributeError` 变为明确受控行为
- current_progress:
  - 已完成人工筛选并推进为正式 semi_real 任务
  - `scaffold_semi_real_task.py --from-candidate --dry-run` 已跑通
  - 已手工补 `expected_target_files`
  - 已执行非 `dry-run`，并生成：
    - `benchmarks/tasks/task_123.json`
    - `benchmarks/repos/anyio_taskgroup_reentry_repo`
  - 当前 repo 已命中 `anyio/_backends/_asyncio.py` 与 `tests/test_taskgroups.py`
  - 已把 repo 从 TODO 脚手架补成 ready 口径最小 bug repo
  - 当前测试状态为：
    - 正常路径 `1` 条通过
    - 目标回归测试 `1` 条失败
  - 当前失败形式与真实 issue 对齐：重复进入同一个 task group 时泄漏 `AttributeError`
  - 已验证：
    - `improved_v64` 单任务失败
    - `improved_v65` 单任务成功
  - 已完成：
    - 正式集 `62 / 62`
    - `frozen_20` `20 / 20`
    - `frozen_40` `40 / 40`
- recommendation:
  - `已完成正式接入，下一步可继续沿 anyio 家族扩容`

### `agronholm/anyio#1111`

- 原因：
  - 已进入正式任务
  - 对应 `task_124`
  - `improved_v66` 已完成正式集、`frozen_20`、`frozen_40` 三线最小验证

### `agronholm/anyio#1113`

- family:
  - `并发与协程`
- current_status:
  - `accepted`
- why_it_fits:
  - 错误行为清晰，且 issue 文本提到 “trio passes but asyncio fails”，有利于压成对照型回归测试
- current_progress:
  - 已完成人工筛选，状态从 `imported` 推进到 `screened`
  - 已跑通 `scaffold_semi_real_task.py --from-candidate --dry-run`
  - 已执行非 `dry-run`，并生成：
    - `benchmarks/tasks/task_125.json`
    - `benchmarks/repos/anyio_check_cancelled_repo`
  - 当前自动推断出的 target files 为：
    - `anyio/from_thread.py`
    - `tests/test_from_thread.py`
  - 已把 repo 从 TODO 脚手架补成 ready 口径最小 bug repo
  - 当前测试状态为：
    - 正常路径 `1` 条通过
    - 目标回归测试 `1` 条失败
  - 当前失败形式与真实 issue 对齐：
    - `asyncio` backend 下 `CancelledError` 会泄漏出对应 cancel scope
  - 已验证：
    - `improved_v68` 单任务失败
    - `improved_v69` 单任务成功
  - 已完成：
    - 正式集 `64 / 64`
    - `frozen_20` `20 / 20`
    - `frozen_40` `40 / 40`
- risk_notes:
  - 已完成正式接入，但平均耗时相对 `v68` 有回升，后续仍需继续做性能复核
- recommendation:
  - `已完成正式接入，可继续转向 watchfiles 或补 v69 稳定性复跑`

### `agronholm/anyio#82`

- family:
  - `并发与协程`
- current_status:
  - `accepted`
- why_it_fits:
  - 标题直接指向 `CancelledError leak with asyncio and curio`
  - 和当前 `anyio#1113` 一样属于“取消/异常泄漏边界”，但问题路径不同，适合继续做同生态增量扩容
  - 当前已经完成导入和首轮人工筛选，后续可以直接进入 issue 级判题或脚手架评估
- expected_target_files:
  - 当前搜索结果提示：`test_anyio.py`
- expected_test_shape:
  - 优先压成 `2` 到 `3` 条稳定回归测试，覆盖当前错误路径、期望不再泄漏路径，以及一个相邻不回归场景
- current_progress:
  - 已从 `screened` 继续推进到“已生成 semi_real 脚手架”
  - 已生成：
    - `benchmarks/tasks/task_128.json`
    - `benchmarks/repos/anyio_82_repo`
  - 当前自动推断结果为：
    - `anyio/module.py`
    - `test_anyio.py`
  - 已继续补成 ready 口径最小并发回归任务：
    - trio 对照路径 `1` 条通过
    - asyncio / curio 目标路径 `2` 条失败
  - 当前更准确的口径是：
    - `accepted + ready + in_formal_manifest + task_128`
  - 已进一步完成：
    - `improved_v70` 单任务失败
    - `improved_v71` 单任务成功
  - 这说明它已经不只是 ready 候选，而是已经完成正式扩容所需的直接质量证明
- risk_notes:
  - 语义上与已有 anyio 题族相邻，后续应避免把它做成和 `task_124 / task_125` 过于相似的重复题
- recommendation:
  - `已完成正式接入，下一步转向 v71 stability / performance 复核与新来源扩容`

### `agronholm/anyio#88`

- family:
  - `并发与协程`
- current_status:
  - `accepted`
- why_it_fits:
  - 标题直接指向 `Parent task spuriously cancelled with asyncio`
  - issue 文本提到 trio / curio / asyncio 的行为差异，具备对照型并发 bug 的味道
- expected_target_files:
  - 当前搜索结果提示：`fail_case.py`
- expected_test_shape:
  - 优先压成 `2` 到 `3` 条稳定回归测试，覆盖父任务被误取消的错误路径与期望行为
- current_progress:
  - 已完成首轮人工筛选
  - 当前状态已从 `imported` 推进到 `screened`
  - 已进一步生成 semi_real 脚手架：
    - `benchmarks/tasks/task_129.json`
    - `benchmarks/repos/anyio_88_repo`
  - 当前自动推断结果为：
    - `anyio/module.py`
    - `tests/test_fail_case.py`
  - 已继续补成 ready 口径最小并发回归任务：
    - 正常路径 `1` 条通过
    - 目标 asyncio 路径 `1` 条失败
  - 当前已从 `screened` 进一步推进到 `accepted`
  - 已进一步完成单任务验证：
    - `improved_v69` 单任务失败
    - `improved_v70` 单任务成功
  - 当前更准确的口径是：
    - `accepted + ready + in_formal_manifest`
  - 当前下一步应更新为：
    - 对 `improved_v70` 补稳定性复跑
    - 再观察是否值得成为新的长期主稳定锚点
- risk_notes:
  - 仍需进一步人工筛选，确认是否会落成重时序或多模块问题
- recommendation:
  - `已完成 ready 化，当前优先进入单任务修复验证或正式接入评估`

### `samuelcolvin/watchfiles#266`

- family:
  - `文件路径与 IO`
- why_it_fits:
  - 和权限忽略、error handler 边界有关，语义上是有增量的
- current_status:
  - 已于 `2026-06-13` 从 `imported` 推进到 `screened`，随后继续推进到 `accepted`
  - 当前 `--dry-run` 自动推断已修正到：
    - `watchfiles/main.py`
    - `tests/test_main.py`
  - 已进一步生成并补齐本地 ready semi-real：
    - `task_126`
    - `benchmarks/repos/watchfiles_266_repo`
- risk_notes:
  - 平台/WSL/docker 味道还是偏重，应作为备选，不建议先于 `fsspec#979`
- recommendation:
  - `已完成 semi-real ready 化，并已纳入 challenge manifest；后续再视代表性决定是否升格为正式任务`

## 已从短名单移除

### `python-attrs/attrs#1479`

- 原因：
  - 已进入正式任务
  - 对应 `task_058`

### `simonw/sqlite-utils#488`

- 原因：
  - 已进入正式任务
  - 对应 `task_059`

### `simonw/sqlite-utils#186`

- 原因：
  - 已进入正式任务
  - 对应 `task_060`

### `PyCQA/isort#1815`

- 原因：
  - 已进入正式任务
  - 对应 `task_061`

### `pydantic/pydantic#9582`

- 原因：
  - 已进入正式任务
  - 对应 `task_014 / task_057`

### `dateutil/dateutil#384`

- 原因：
  - 已进入正式任务
  - 对应 `task_043 / task_044`

### `python-jsonschema/jsonschema#1162`

- 原因：
  - 已进入正式任务
  - 对应 `task_045 / task_046`

### `pypa/packaging#810`

- 原因：
  - 已进入正式任务
  - 对应 `task_047 / task_048`

### `pypa/packaging#638`

- 原因：
  - 已进入正式任务
  - 对应 `task_062 / task_063`

### `python-poetry/tomlkit#442`

- 原因：
  - 已进入正式任务
  - 对应 `task_068 / task_069`

### `python-poetry/tomlkit#383`

- 原因：
  - 已进入正式任务
  - 对应 `task_070 / task_071`

### `python-poetry/tomlkit#431`

- 原因：
  - 已进入正式任务
  - 对应 `task_072 / task_073`

### `pallets/jinja#2151`

- 原因：
  - 已进入正式任务
  - 对应 `task_074 / task_075`

### `pallets/jinja#2176`

- 原因：
  - 已进入正式任务
  - 对应 `task_076 / task_077`

### `dateutil/dateutil#1191`

- 原因：
  - 已进入正式任务
  - 对应 `task_049 / task_050`

### `python-jsonschema/jsonschema#1328`

- 原因：
  - 已进入正式任务
  - 对应 `task_051 / task_052`

### `python-jsonschema/jsonschema#1125`

- 原因：
  - 已进入正式任务
  - 对应 `task_053 / task_054`

### `simonw/sqlite-utils#159`

- 原因：
  - 已进入正式任务
  - 对应 `task_055 / task_056`

### `pypa/packaging#788`

- 原因：
  - 已进入正式任务
  - 对应 `task_064 / task_065`

### `pypa/packaging#909`

- 原因：
  - 已进入正式任务
  - 对应 `task_066 / task_067`

### `agronholm/anyio#88`

- 原因：
  - 已进入正式任务
  - 对应 `task_129`

## 使用方式

每次准备扩容时，优先按下面顺序使用：

1. 先确认 shortlist 是否为空
2. 若为空，优先导入新的 issue 列表并重建 shortlist
3. 一旦某条进入正式任务，就把它从 shortlist 中移除并转入“已从短名单移除”
