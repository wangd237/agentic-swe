# 候选短名单

本文件只保留“当前最值得推进”的候选 issue，避免每次都从完整候选池重新筛。

筛选依据：

- 符合 `docs/issue_sourcing_spec.md`
- 尽量单函数 / 单模块
- 容易缩成 1 到 3 个稳定回归测试
- 能与现有 benchmark 类型形成增量，而不是重复

## 当前 Top 5

### 1. `pypa/packaging#845`

- 标题：
  - `Inconsistent extra normalisation in Requirement.__str__`
- 推荐级别：`high`
- 为什么适合：
  - 字符串规范化问题，边界明确
  - 很适合最小化为单函数 `Requirement.__str__` 风格任务
  - 与当前 `packaging_wheel_repo` 同仓库但缺陷类型不同
- 预期目标文件：
  - requirement 字符串输出逻辑
- 预期测试形态：
  - 1 个不一致例子
  - 1 个正常例子
- 主要风险：
  - 要先选定“正确规范化方向”，避免变成规范讨论

### 2. `dateutil/dateutil#384`

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

### 3. `pallets/click#2402`

- 标题：
  - `resolve_command fails if cmd is None`
- 推荐级别：`medium-high`
- 为什么适合：
  - CLI 解析异常回落问题，和 `task_036` 的“异常应回落为普通失败”相近但不重复
  - 可能只要一个保护分支
- 预期目标文件：
  - `resolve_command` 最小实现
- 预期测试形态：
  - typo / missing command 不应再抛 traceback
- 主要风险：
  - 需要把 CLI 行为缩成最小纯函数，避免带完整命令行环境

### 4. `python-jsonschema/jsonschema#1162`

- 标题：
  - `Hostname format check does not allow single labels`
- 推荐级别：`medium-high`
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

### 5. `pypa/packaging#810`

- 标题：
  - ``Specifier` Greater than comparison returns incorrect result for a version with dev+local parts`
- 推荐级别：`medium`
- 为什么适合：
  - 版本比较边界问题，输入输出可明确收敛
  - 与现有 `packaging#873` 同仓库但不重复
- 预期目标文件：
  - specifier 比较逻辑
- 预期测试形态：
  - 1 个 dev+local 边界例子
  - 1 个普通比较回归例子
- 主要风险：
  - 需要先确认最小可复现版本，避免引入完整版本比较矩阵

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
