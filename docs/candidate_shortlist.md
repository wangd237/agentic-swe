# 候选短名单

本文件只保留“当前最值得推进”的候选 issue，避免每次都从完整候选池重新筛。

筛选依据：

- 符合 `docs/issue_sourcing_spec.md`
- 尽量单函数 / 单模块
- 容易缩成 `1` 到 `3` 个稳定回归测试
- 能与现有 benchmark 类型形成增量，而不是重复

## 当前 Top 5

### 1. `dateutil/dateutil#1191`

- 标题：
  - `Incorrect year is returned when parsing a date string such as "may15,2021"`
- 推荐级别：`high`
- 为什么适合：
  - 仍然是 parser 类 bug，但与 `task_044` 的 `MM.YYYY` 路径不同
  - 输入输出样例清晰，容易还原成 `2` 个回归测试
  - 能继续强化 `dateutil` parser 子类能力
- 预期目标文件：
  - 日期 token 切分或逗号处理逻辑
- 预期测试形态：
  - `may15,2021 -> 2021-05-15`
  - 加空格版本继续保持正确
- 主要风险：
  - 需要小心不要把问题缩得过度依赖具体 tokenizer 细节

### 2. `python-jsonschema/jsonschema#1328`

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

### 3. `python-jsonschema/jsonschema#1125`

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

### 4. `simonw/sqlite-utils#159`

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

### 5. `pydantic/pydantic#9582`

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

## 暂不优先

### `python-attrs/attrs#1479`

- 原因：
  - 更像框架生命周期 / 语义预期问题
  - 容易落到“设计是否如此”而不是“实现明确错误”

## 使用方式

每次准备扩容时，优先按下面顺序使用：

1. 先从本文件 Top 5 里选
2. 如果都不合适，再回到完整候选池
3. 一旦某条进入正式任务，就把它从 shortlist 中移除或下移
