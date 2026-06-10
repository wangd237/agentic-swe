# 候选短名单

本文件只保留“当前最值得推进”的候选 issue，避免每次都从完整候选池重新筛。

筛选依据：

- 符合 `docs/issue_sourcing_spec.md`
- 尽量单函数 / 单模块
- 容易缩成 `1` 到 `3` 个稳定回归测试
- 能与现有 benchmark 类型形成增量，而不是重复

## 当前 Top 2

### 1. `simonw/sqlite-utils#186`

- 标题：
  - `.extract() shouldn't extract null values`
- 推荐级别：`medium`
- 为什么适合：
  - 仍然属于 sqlite-utils，但问题边界比事务语义更局部
  - 可以缩成单函数数据提取与空值过滤行为
  - 能补“数据抽取时的空值语义”这一类现有 benchmark 较少覆盖的问题
- 预期目标文件：
  - `extract` 或值清洗逻辑
- 预期测试形态：
  - `None` 不应被当成可继续抽取的值
  - 非空字符串或对象保持原有抽取行为
- 主要风险：
  - 要避免把真实 sqlite schema 细节整体搬进 benchmark

### 2. `PyCQA/isort#1815`

- 标题：
  - `Tuple sorting doesn't consider profile`
- 推荐级别：`medium`
- 为什么适合：
  - 问题边界集中在排序策略选择
  - 可望缩成单模块配置分派与输出断言
  - 能补“配置 profile 影响行为”的 benchmark 类型
- 预期目标文件：
  - tuple 排序或 profile 分派逻辑
- 预期测试形态：
  - 指定 profile 后 tuple 排序应符合该 profile 语义
  - 默认 profile 行为保持不回归
- 主要风险：
  - 要避免把完整格式化器行为整体搬进 benchmark

## 已从短名单移除

### `python-attrs/attrs#1479`

- 原因：
  - 已进入正式任务
  - 对应 `task_058`

### `simonw/sqlite-utils#488`

- 原因：
  - 已进入正式任务
  - 对应 `task_059`

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

## 使用方式

每次准备扩容时，优先按下面顺序使用：

1. 先从本文件 Top 2 里选
2. 如果都不合适，再回到完整候选池
3. 一旦某条进入正式任务，就把它从 shortlist 中移除或下移
