# 候选短名单

本文件只保留“当前最值得推进”的候选 issue，避免每次都从完整候选池重新筛。

筛选依据：

- 符合 `docs/issue_sourcing_spec.md`
- 尽量单函数 / 单模块
- 容易缩成 1 到 3 个稳定回归测试
- 能与现有 benchmark 类型形成增量，而不是重复

## 当前 Top 5

### 1. `dateutil/dateutil#384`

- 标题：
  - `parser fails to parse MM.YYYY`
- 推荐级别：`high`
- 为什么适合：
  - parser 类问题，输入输出非常明确
  - 与当前 dateutil 任务不同，能补月份年份格式容错
  - 很适合单函数解析任务
- 预期目标文件：
  - 一个最小 `parse_month_year` 或 parser 分支
- 预期测试形态：
  - `05.2016 -> 2016-05`
  - 对照 `04/2014` 继续保持正确
- 主要风险：
  - 需要决定默认 day 如何处理，最好缩题成“只断言年月”

### 2. `python-jsonschema/jsonschema#1162`

- 标题：
  - `Hostname format check does not allow single labels`
- 推荐级别：`high`
- 为什么适合：
  - 与 `task_036` 同域但不是同一问题
  - 可形成 hostname 系列第二条任务
  - 很适合最小 repo 和清晰测试
- 预期目标文件：
  - hostname 校验函数
- 预期测试形态：
  - `localhost` 应通过
  - `example.com` 继续通过
- 主要风险：
  - 与 `task_036` 太相近，连续做会降低 benchmark 语义多样性

### 3. `pypa/packaging#810`

- 标题：
  - ``Specifier` Greater than comparison returns incorrect result for a version with dev+local parts`
- 推荐级别：`medium-high`
- 为什么适合：
  - 版本比较边界问题，输入输出可明确收敛
  - 与现有 `packaging` 任务同仓库但语义不同
- 预期目标文件：
  - specifier 比较逻辑
- 预期测试形态：
  - 1 个 dev+local 边界例子
  - 1 个普通比较回归例子
- 主要风险：
  - 需要先确认最小可复现版本，避免引入完整版本比较矩阵

### 4. `dateutil/dateutil#1191`

- 标题：
  - `Incorrect year is returned when parsing a date string such as "may15,2021"`
- 推荐级别：`medium-high`
- 为什么适合：
  - 仍然是 parser 类 bug，但和 `MM.YYYY` 的 token 化路径不同
  - 输入输出样例清晰，容易还原成 2 个回归测试
- 预期目标文件：
  - 日期 token 切分或逗号处理逻辑
- 预期测试形态：
  - `may15,2021 -> 2021-05-15`
  - 加空格版本保持正确
- 主要风险：
  - 需要小心不要把问题缩得过度依赖具体 tokenizer 细节

### 5. `python-jsonschema/jsonschema#1328`

- 标题：
  - `The return of __iter__() and __contains__() change after accessing of an index with no error`
- 推荐级别：`medium`
- 为什么适合：
  - 可以补“容器状态污染 / 惰性访问副作用”这一类目前较缺的缺陷
  - 行为差异明确，适合做状态前后对照测试
- 预期目标文件：
  - 一个最小 `ErrorTree` 风格容器对象
- 预期测试形态：
  - 访问空索引前后，`__contains__` / `__iter__` 结果应保持一致
- 主要风险：
  - 需要缩题得足够小，避免把整个错误树结构都搬进 benchmark

## 暂不优先

### `python-attrs/attrs#1479`

- 原因：
  - 更像框架生命周期 / 语义预期问题
  - 容易落到“设计是否如此”而不是“实现明确错误”

### `simonw/sqlite-utils#159`

- 原因：
  - 虽然表面简单，但会天然引入事务 / 提交语义
  - 缩题时需要额外处理数据库状态，不如当前 shortlist 轻

### `PyCQA/isort#1815`

- 原因：
  - 需要 profile 与格式化风格联动
  - 缩成稳定最小任务可能会略重

## 使用方式

每次准备扩容时，优先按下面顺序使用：

1. 先从本文件 Top 5 里选
2. 如果都不合适，再回到完整候选池
3. 一旦某条进入正式任务，就把它从 shortlist 中移除或下移
