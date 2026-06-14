# 案例分析归档 v1

以下内容归档自旧版 [docs/case_studies.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/case_studies.md)。

保留这份归档的目的不是继续把它当作对外展示材料，而是：

- 保存早期逐题逐版本的完整记录
- 方便追溯某条任务最早是在哪个版本进入基准集
- 让新的精选案例文档可以专注讲“最值得讲的故事”

---

# 案例分析

## 成功案例 1：`task_003`

- repo：`multi_bug_repo`
- 代表版本：`improved_v1`
- 现象：
  - baseline_v1 只能修掉空输入问题
  - 修复后仍会在 `None.strip()` 处失败
- 改进点：
  - `improved_v1` 在 patch 中补充了中间 `None` 元素过滤
- 结果：
  - `task_003` 从 `Patch Incorrect` 变成完全通过

## 成功案例 2：`task_004`

- repo：`leading_none_repo`
- 代表版本：`improved_v2`
- 现象：
  - `improved_v1` 能处理空输入和中间 `None`
  - 但首元素为 `None` 时仍会在 `first_item.strip()` 处失败
- 改进点：
  - `improved_v2` 把策略升级为“归一化前先过滤所有 `None`”
- 结果：
  - `task_004` 从失败变为完全通过

## 成功案例 3：`task_006`

- repo：`requests_compat_repo`
- 来源：`psf/requests#6432`
- 代表版本：`improved_v3`
- 现象：
  - `improved_v2` 无法对依赖约束类问题生成 patch
  - `task_006` 会以 `Premature Finish` 失败
- 改进点：
  - `improved_v3` 新增 urllib3 上界放宽策略
- 结果：
  - `task_006` 从失败变为完全通过

## 成功案例 4：`task_008`

- repo：`requests_encoding_repo`
- 来源：`psf/requests#7234`
- 代表版本：`improved_v4`
- 现象：
  - `improved_v3` 还不具备 quoted charset 的解析修复能力
  - `task_008` 会以 `Premature Finish` 失败
- 改进点：
  - `improved_v4` 新增 quoted charset 去引号策略
- 结果：
  - `task_008` 从失败变为完全通过

## 成功案例 5：`task_010`

- repo：`rich_ansi_repo`
- 来源：`Textualize/rich#4090`
- 代表版本：`improved_v5`
- 现象：
  - `improved_v4` 还不具备 ANSI 文本 CRLF 行尾拆分修复能力
  - `task_010` 会以 `Premature Finish` 失败
- 改进点：
  - `improved_v5` 新增 CRLF 兼容的 `splitlines(keepends=True)` 修复策略
- 结果：
  - `task_010` 从失败变为完全通过

## 成功案例 6：`task_013`

- repo：`rich_handler_repo`
- 来源：`Textualize/rich#3877`
- 代表版本：`improved_v6`
- 现象：
  - `improved_v5` 还不具备 RichHandler 时区偏移保留能力
  - `task_013` 会以 `Premature Finish` 失败
- 改进点：
  - `improved_v6` 让时间格式化显式使用时区信息
- 结果：
  - `task_013` 从失败变为完全通过

## 成功案例 7：`task_016`

- repo：`click_flag_repo`
- 来源：`pallets/click#3111`
- 代表版本：`improved_v7`
- 现象：
  - `improved_v6` 还不具备负向 boolean flag 默认值修复能力
  - `task_016` 会以 `Premature Finish` 失败
- 改进点：
  - `improved_v7` 修正了 `default=True` 在负向 flag 场景下被错误覆盖的问题
- 结果：
  - `task_016` 从失败变为完全通过

## 成功案例 8：`task_017`

- repo：`pytest_marker_repo`
- 来源：`pytest-dev/pytest#14329`
- 代表版本：`improved_v8`
- 现象：
  - `improved_v7` 还不具备最近 marker 覆盖优先修复能力
  - `task_017` 会以 `Premature Finish` 失败
- 改进点：
  - `improved_v8` 把 marker 查找顺序改成从继承链尾部反向查找
- 结果：
  - `task_017` 从失败变为完全通过

## 成功案例 9：`task_019`

- repo：`dateutil_tz_repo`
- 来源：`dateutil/dateutil#1432`
- 代表版本：`improved_v9`
- 现象：
  - `improved_v8` 还不具备 UTC/GMT 无 offset 时的零偏移回落修复能力
  - `task_019` 会以 `Premature Finish` 失败
- 改进点：
  - `improved_v9` 让 `tzstr` 在未显式提供 offset 时回落为 `0`
- 结果：
  - `task_019` 从失败变为完全通过

## 成功案例 10：`task_022`

- repo：`dateutil_parser_repo_v2`
- 来源：`dateutil/dateutil#1442`
- 代表版本：`improved_v10`
- 现象：
  - `improved_v9` 还不具备 9 位时间串按 HHMMSSmmm 解析的修复能力
  - `task_022` 会以 `Premature Finish` 失败
- 改进点：
  - `improved_v10` 让 9 位时间串直接走时间解析路径，而不是继续抛出格式错误
- 结果：
  - `task_022` 从失败变为完全通过

## 成功案例 11：`task_024`

- repo：`jinja_meta_repo`
- 来源：`pallets/jinja#2069`
- 代表版本：`improved_v11`
- 现象：
  - `improved_v10` 还不具备模板变量控制流分析修复能力
  - `task_024` 会以 `Premature Finish` 失败
- 改进点：
  - `improved_v11` 让所有分支都已赋值的变量不再被判定为 undeclared
- 结果：
  - `task_024` 从失败变为完全通过

## 成功案例 12：`task_026`

- repo：`jinja_slice_repo`
- 来源：`pallets/jinja#2118`
- 代表版本：`improved_v12`
- 现象：
  - 当切片数能整除输入长度时
  - 旧策略还不具备 `fill_with` 边界补位修复能力
- 改进点：
  - `improved_v12` 让 `fill_with` 只在存在余数时才补入尾部分片
- 结果：
  - `task_026` 在扩容后的真实任务集上完全通过

## 成功案例 13：`task_028`

- repo：`tomlkit_array_repo`
- 来源：`python-poetry/tomlkit#494`
- 代表版本：`improved_v13`
- 现象：
  - 当数组原始风格把逗号放在下一行时
  - 旧策略还不具备序列化追加时的重复逗号修复能力
- 改进点：
  - `improved_v13` 保留原始下一行逗号风格，但避免 append 后生成双逗号
- 结果：
  - `task_028` 在扩容后的真实任务集上完全通过

## 成功案例 14：`task_030`

- repo：`tomlkit_inline_table_repo`
- 来源：`python-poetry/tomlkit#495`
- 代表版本：`improved_v14`
- 现象：
  - dotted inline table 追加新键时
  - 旧策略还不具备 inline table 分隔修复能力
- 改进点：
  - `improved_v14` 为新增键值对补上逗号和空格分隔，避免结构被黏连破坏
- 结果：
  - `task_030` 在扩容后的真实任务集上完全通过

## 成功案例 15：`task_032`

- repo：`packaging_wheel_repo`
- 来源：`pypa/packaging#873`
- 代表版本：`improved_v15`
- 现象：
  - wheel 文件名中的未 normalized 版本号
  - 旧策略还不具备拒绝逻辑
- 改进点：
  - `improved_v15` 为非 normalized 版本号增加显式拒绝分支
- 结果：
  - `task_032` 在扩容后的真实任务集上完全通过

## 成功案例 16：`task_034`

- repo：`jsonschema_extras_repo`
- 来源：`python-jsonschema/jsonschema#1157`
- 代表版本：`improved_v16`
- 现象：
  - `extras_msg` 在 mixed-type extras 场景下
  - 会因为 `sorted(extras)` 无法比较 `bool` 和 `str` 而直接抛出 `TypeError`
- 改进点：
  - `improved_v16` 在保持同类型 extras 排序输出的前提下
  - 为 mixed-type extras 增加排序失败回落逻辑
- 结果：
  - `task_034` 在扩容后的真实任务集上完全通过

## 成功案例 17：`task_036`

- repo：`jsonschema_hostname_repo`
- 来源：`python-jsonschema/jsonschema#1121`
- 代表版本：`improved_v17`
- 现象：
  - hostname 格式检查在空字符串场景下
  - 会把底层 `ValueError` 直接抛给调用方
- 改进点：
  - `improved_v17` 为空字符串场景增加异常回落
  - 让格式检查返回普通失败而不是中断执行
- 结果：
  - `task_036` 在扩容任务集和冻结同集合评测里都完全通过

## 成功案例 18：`task_038`

- repo：`jsonschema_multipleof_repo`
- 来源：`python-jsonschema/jsonschema#1159`
- 代表版本：`improved_v18`
- 现象：
  - `multipleOf=11` 时超大整数能通过
  - 但 `multipleOf=11.0` 时旧逻辑会错误走浮点路径并失败
- 改进点：
  - `improved_v18` 先识别“整数值浮点数”
  - 再按数学整数语义执行可整除判断
- 结果：
  - `task_038` 在扩容到 16 条任务后的正式任务集上完全通过

## 成功案例 19：`task_040`

- repo：`packaging_requirement_repo`
- 来源：`pypa/packaging#845`
- 代表版本：`improved_v19`
- 现象：
  - 单独的 `extra == "mariadb_connector"` 会被规范化
  - 但复合 marker 表达式里的 `extra` 仍保留下划线
- 改进点：
  - `improved_v19` 统一走 marker 表达式级别的 extra 规范化
  - 不再只处理单独 extra marker 的特例
- 结果：
  - `task_040` 在扩容到 17 条任务后的正式任务集上完全通过

## 成功案例 20：`task_042`

- repo：`click_alias_repo`
- 来源：`pallets/click#2402`
- 代表版本：`improved_v20`
- 现象：
  - 缺失命令场景下，底层返回 `cmd=None`
  - 旧逻辑仍直接访问 `cmd.name`，导致 `AttributeError`
- 改进点：
  - 通过增加空命令分支，让命令解析回落到正常报错路径
- 结果：
  - `task_042` 在扩容后的真实任务集上完全通过

> 其余旧版条目保持原样归档，后续如果需要逐版本追溯，可继续查阅这份文件以及 [docs/results.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/results.md)。
