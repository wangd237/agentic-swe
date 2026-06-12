# 候选短名单

本文件只保留“当前最值得推进”的候选 issue，避免每次都从完整候选池重新筛。

筛选依据：

- 符合 `docs/issue_sourcing_spec.md`
- 尽量单函数 / 单模块
- 容易缩成 `1` 到 `3` 个稳定回归测试
- 能与现有 benchmark 类型形成增量，而不是重复

## 当前 Top 1

### `pallets/jinja#2176`

- 原因：
  - `indent` filter 的行为边界很清楚
  - 但 issue 仍是 open，语义稳定性略弱于 closed/fixed 候选

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

## 使用方式

每次准备扩容时，优先按下面顺序使用：

1. 先从当前 Top 6 中选择最容易转成 semi_real 的 issue
2. 若 Top 6 消耗完，再回到完整候选池或导入新的 issue 列表
3. 一旦某条进入正式任务，就把它从 shortlist 中移除或下移
