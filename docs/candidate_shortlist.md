# 候选短名单

本文件只保留“当前最值得推进”的候选 issue，避免每次都从完整候选池重新筛。

筛选依据：

- 符合 `docs/issue_sourcing_spec.md`
- 尽量单函数 / 单模块
- 容易缩成 `1` 到 `3` 个稳定回归测试
- 能与现有 benchmark 类型形成增量，而不是重复

## 当前 Top 5

### 1. `python-jsonschema/jsonschema#1328`

- 标题：
  - `The return of __iter__() and __contains__() change after accessing of an index with no error`
- 推荐级别：`high`
- 为什么适合：
  - 可以补“容器状态污染 / 惰性访问副作用”这一类目前仍缺的缺陷
  - 行为差异明确，适合做状态前后对照测试
  - 与现有 `jsonschema` 任务语义差异足够大
- 预期目标文件：
  - 一个最小 `ErrorTree` 风格容器对象
- 预期测试形态：
  - 访问空索引前后，`__contains__` / `__iter__` 结果应保持一致
- 主要风险：
  - 需要缩题得足够小，避免把整个错误树结构都搬进 benchmark

### 2. `python-jsonschema/jsonschema#1125`

- 标题：
  - `extend() doesn't copy applicable_validators`
- 推荐级别：`medium-high`
- 为什么适合：
  - 属于 validator 组合逻辑问题
  - 输入输出可以通过极小 schema 行为复现
  - 能补一类“继承 / 扩展时语义丢失”的任务形态
- 预期目标文件：
  - validator `extend` 逻辑
- 预期测试形态：
  - 扩展后仍保留 `applicable_validators`
  - 普通 validator 扩展路径不回归
- 主要风险：
  - 要避免把完整 legacy validator 体系整体搬进 benchmark

### 3. `simonw/sqlite-utils#159`

- 标题：
  - `.delete_where() does not auto-commit (unlike .insert() or .upsert())`
- 推荐级别：`medium`
- 为什么适合：
  - 行为断言非常清楚
  - 能补数据库状态与提交语义这一类目前较少覆盖的缺陷
- 预期目标文件：
  - `delete_where` 或事务提交逻辑
- 预期测试形态：
  - 删除后不显式提交也应对后续读取可见
  - 插入 / 更新行为保持不变
- 主要风险：
  - 会天然引入数据库状态，缩题时要把依赖面压到最小

### 4. `pydantic/pydantic#9582`

- 标题：
  - `Model validator is ignored during inheritance`
- 推荐级别：`medium`
- 为什么适合：
  - 属于继承链语义问题，但输入输出仍有明确现象
  - 如果能缩成最小 validator 链路，会补到目前较少覆盖的模型继承行为
- 预期目标文件：
  - 最小 validator 分派逻辑
- 预期测试形态：
  - 父类 validator 继续运行
  - 子类 validator 不应覆盖掉父类 validator
- 主要风险：
  - 需要把问题缩到足够小，避免引入完整框架生命周期

### 5. `python-attrs/attrs#1479`

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

## 已从短名单移除

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

## 使用方式

每次准备扩容时，优先按下面顺序使用：

1. 先从本文件 Top 5 里选
2. 如果都不合适，再回到完整候选池
3. 一旦某条进入正式任务，就把它从 shortlist 中移除或下移
