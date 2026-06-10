# 候选短名单

本文件只保留“当前最值得推进”的候选 issue，避免每次都从完整候选池重新筛。

筛选依据：

- 符合 `docs/issue_sourcing_spec.md`
- 尽量单函数 / 单模块
- 容易缩成 `1` 到 `3` 个稳定回归测试
- 能与现有 benchmark 类型形成增量，而不是重复

## 当前 Top 4

### 1. `python-attrs/attrs#1479`

- 标题：
  - `Alias not available during field transformation`
- 推荐级别：`medium`
- 为什么适合：
  - 如果能缩成最小字段变换链路，可以补到对象定义阶段的元数据可见性问题
  - 与当前 benchmark 的 parser / validator / specifier 语义差异较大
- 预期目标文件：
  - 字段变换或 alias 读取逻辑
- 预期测试形态：
  - 字段变换阶段应能读取 alias
  - 不影响无 alias 的普通字段
- 主要风险：
  - 容易落到框架构建时序，缩题时要非常克制

### 2. `simonw/sqlite-utils#488`

- 标题：
  - ``sqlite-utils transform` should set empty strings to null when converting text columns to integer/float`
- 推荐级别：`medium`
- 为什么适合：
  - 能补数据清洗 / 类型转换边界这一类目前较少覆盖的问题
  - 输入输出示例比较明确，适合缩成单函数转换逻辑
- 预期目标文件：
  - transform / coercion 逻辑
- 预期测试形态：
  - 空字符串在整数或浮点转换时回落为 `None`
  - 非空数字字符串保持正常转换
- 主要风险：
  - 容易把 sqlite 表结构细节带进来，缩题时要尽量只保留数据转换本身

### 3. `simonw/sqlite-utils#186`

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

### 4. `PyCQA/isort#1815`

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

1. 先从本文件 Top 4 里选
2. 如果都不合适，再回到完整候选池
3. 一旦某条进入正式任务，就把它从 shortlist 中移除或下移
