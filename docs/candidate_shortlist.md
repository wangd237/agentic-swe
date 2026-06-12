# 候选短名单

本文件只保留“当前最值得推进”的候选 issue，避免每次都从完整候选池重新筛。

筛选依据：

- 符合 `docs/issue_sourcing_spec.md`
- 尽量单函数 / 单模块
- 容易缩成 `1` 到 `3` 个稳定回归测试
- 能与现有 benchmark 类型形成增量，而不是重复

## 当前 Top 4

### `pypa/packaging#638`

- 原因：
  - `Marker.evaluate(extra=None)` 是非常干净的类型边界 bug
  - 单函数、单断言风格，适合快速转成高质量 semi_real
  - 能补足 marker 归一化与空值处理能力

### `python-poetry/tomlkit#431`

- 原因：
  - dotted key + super table 的渲染输出差异非常明确
  - 与现有 `tomlkit` 两条任务相比，新增了 super table / dotted key 组合语义
  - 仍然是单模块渲染逻辑，不会把修复边界拉太大

### `python-poetry/tomlkit#383`

- 原因：
  - 当前 `tomlkit` 任务更偏序列化，这条能补容器删除语义
  - `OutOfOrderTableProxy.pop()` 失败是很典型的容器状态 bug
  - 语义有增量，不会和现有两个 `tomlkit` 任务过度重复

### `pallets/jinja#2151`

- 原因：
  - async runtime 的 `__repr__` 警告问题，目标方法和修复方向都很清楚
  - 能给 `jinja` 来源新增 async/runtime 表示层能力面
  - 与现有 `meta` / `slice` 两条任务形成明显互补

## 当前备选 2

### `python-poetry/tomlkit#442`

- 原因：
  - 极易最小化，适合作为高置信度补量候选
  - 但难度略低，优先级可稍后于更有语义增量的候选

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
