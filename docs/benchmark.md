# Benchmark 说明

## 当前 benchmark 分层

当前项目已经把 benchmark 拆成三层，分别服务不同阶段：

### 1. Dev Set

当前 manifest：

- `benchmarks/manifests/dev_tasks.json`

当前任务：

- `benchmarks/tasks/task_001.json`
- `benchmarks/tasks/task_002.json`

当前 repo：

- `benchmarks/repos/sample_repo`

用途：

- 联调单任务 patch 闭环
- 验证 batch runner 是否稳定
- 作为早期开发阶段的回归集

### 2. Report Set

当前 manifest：

- `benchmarks/manifests/report_tasks.json`
- `benchmarks/manifests/real_issue_tasks.json`

当前任务：

- `benchmarks/tasks/task_001.json`
- `benchmarks/tasks/task_003.json`
- `benchmarks/tasks/task_004.json`
- `benchmarks/tasks/task_006.json`
- `benchmarks/tasks/task_008.json`
- `benchmarks/tasks/task_010.json`
- `benchmarks/tasks/task_013.json`
- `benchmarks/tasks/task_016.json`
- `benchmarks/tasks/task_017.json`
- `benchmarks/tasks/task_019.json`
- `benchmarks/tasks/task_022.json`
- `benchmarks/tasks/task_024.json`
- `benchmarks/tasks/task_026.json`
- `benchmarks/tasks/task_028.json`
- `benchmarks/tasks/task_030.json`
- `benchmarks/tasks/task_032.json`
- `benchmarks/tasks/task_034.json`
- `benchmarks/tasks/task_036.json`
- `benchmarks/tasks/task_038.json`
- `benchmarks/tasks/task_040.json`
- `benchmarks/tasks/task_042.json`
- `benchmarks/tasks/task_044.json`
- `benchmarks/tasks/task_046.json`
- `benchmarks/tasks/task_048.json`
- `benchmarks/tasks/task_050.json`

当前 repo：

- `benchmarks/repos/sample_repo`
- `benchmarks/repos/multi_bug_repo`
- `benchmarks/repos/leading_none_repo`
- `benchmarks/repos/requests_compat_repo`
- `benchmarks/repos/requests_encoding_repo`
- `benchmarks/repos/rich_ansi_repo`
- `benchmarks/repos/rich_handler_repo`
- `benchmarks/repos/click_flag_repo`
- `benchmarks/repos/pytest_marker_repo`
- `benchmarks/repos/dateutil_tz_repo`
- `benchmarks/repos/dateutil_parser_repo_v2`
- `benchmarks/repos/jinja_meta_repo`
- `benchmarks/repos/jinja_slice_repo`
- `benchmarks/repos/tomlkit_array_repo`
- `benchmarks/repos/tomlkit_inline_table_repo`
- `benchmarks/repos/packaging_wheel_repo`
- `benchmarks/repos/packaging_requirement_repo`
- `benchmarks/repos/jsonschema_extras_repo`
- `benchmarks/repos/jsonschema_hostname_repo`
- `benchmarks/repos/jsonschema_multipleof_repo`
- `benchmarks/repos/click_alias_repo`
- `benchmarks/repos/dateutil_month_year_repo`
- `benchmarks/repos/jsonschema_single_label_hostname_repo`
- `benchmarks/repos/packaging_specifier_repo`
- `benchmarks/repos/dateutil_attached_comma_repo`

用途：

- 执行 baseline vs improved 的正式对比
- 生成可展示的 batch run / batch eval / compare 报告
- 验证优化动作是否真的带来指标提升

### 3. Future GitHub Real-Issue Set

当前状态：

- 已接入 manifest：
  - `benchmarks/manifests/real_issue_tasks.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_18_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_20_v1.json`
- 已新增候选清单文件：
  - `benchmarks/real_world_candidates.json`
- 已新增导入脚本：
  - `scripts/import_github_issue.py`
- 已新增脚手架脚本：
  - `scripts/scaffold_semi_real_task.py`

后续规划：

- 选择 GitHub 上体量较小、测试可运行、issue 边界清晰的真实仓库
- 将真实 issue 转成结构化任务定义
- 作为项目后期更正式、更有说服力的外部评测集

当前建议的任务来源类型：

- `synthetic`
  - 完全自造联调任务
- `semi_real`
  - 基于真实 issue 改写的半真实任务
- `real_issue`
  - 直接对应 GitHub 真实 issue 的任务

后续接入真实 issue 时，建议优先从 `semi_real` 过渡到 `real_issue`，避免一开始就被复杂环境拖慢主线。

当前建议的导入步骤：

1. 用 `scripts/import_github_issue.py` 把 issue 先导入候选清单
2. 审查 issue 是否满足小仓库、测试清晰、边界明确等条件
3. 如适合继续推进，再生成 `real_issue` task 草稿
4. 用 `scripts/scaffold_semi_real_task.py` 生成 `semi_real` 脚手架
5. 人工补齐：
   - 本地 repo_path
   - test_command
   - target_files_hint
   - success_criteria
6. 缩题完成后再以 `--ready` 模式加入 `real_issue_tasks` manifest

当前候选状态建议按下面流转：

- `to_review`
- `drafted`
- `scaffolded`
- `accepted`
- `rejected`

当前阶段补充说明：

- 正式真实任务已经扩充到 `22` 条
- `frozen_20` 已经成为后续策略迭代的固定同集合基线
- 候选池状态已收敛到：
  - `accepted = 22`
  - `drafted = 1`
  - `to_review = 7`

这部分会在项目主链路更稳定后逐步接入。

## 当前任务设计

### `sample_repo`

主要问题：

- `parse_items([])` 会抛出 `IndexError`
- 正确行为应为返回空列表

相关文件：

- `sample_repo/parser.py`
- `tests/test_parser.py`

### `multi_bug_repo`

主要问题：

- `parse_items([])` 会抛出异常
- `parse_items([' A ', None, 'B '])` 会因为 `None.strip()` 失败
- 正确行为应为：
  - 空输入返回空列表
  - 归一化时忽略 `None`

相关文件：

- `multi_bug_repo/parser.py`
- `tests/test_parser.py`

### `leading_none_repo`

主要问题：

- `parse_items([])` 会抛出异常
- `parse_items([None, ' A ', 'B '])` 会因为首元素 `None` 失败
- `parse_items([' A ', None, 'B '])` 也应忽略中间 `None`
- 正确行为应为：
  - 空输入返回空列表
  - 归一化前先过滤所有 `None`

相关文件：

- `leading_none_repo/parser.py`
- `tests/test_parser.py`

### `requests_compat_repo`

来源：

- `psf/requests#6432`

主要问题：

- 依赖约束仍将 `urllib3` 固定在 `<1.27`
- 对 Python 3.7+ 而言，这会阻止 `urllib3 2.x` 安装

正确行为：

- 将 urllib3 上界放宽到允许 `2.x`
- 其余核心依赖保持存在

相关文件：

- `setup.py`
- `tests/test_setup.py`

### `requests_encoding_repo`

来源：

- `psf/requests#7234`

主要问题：

- `get_encoding_from_headers` 遇到带引号的 charset 会返回 `None`
- 未带引号的 charset 仍然工作正常

正确行为：

- 无论 charset 是否被单引号或双引号包裹，都应返回去引号后的编码值

相关文件：

- `requests_encoding_repo/utils.py`
- `tests/test_utils.py`

### `rich_ansi_repo`

来源：

- `Textualize/rich#4090`

主要问题：

- `Text.from_ansi` 在输入带 `\r\n` 行尾时会退化成空白行
- 普通 `\n` 行尾仍然工作正常

正确行为：

- CRLF 输入不应再解析成 `\n\n`
- 允许统一归一化到 LF，只要文本内容不丢失

相关文件：

- `rich_ansi_repo/ansi.py`
- `tests/test_ansi.py`

### `rich_handler_repo`

来源：

- `Textualize/rich#3877`

主要问题：

- `RichHandler` 的时间格式化会忽略时区偏移
- 当 `log_time_format` 包含 `%z` 时，输出没有按预期保留 `+0200` 一类偏移

正确行为：

- 时间格式化应显式保留时区偏移
- `%z` 应输出可预测的偏移字符串

相关文件：

- `rich_handler_repo/logging.py`
- `tests/test_logging.py`

### `click_flag_repo`

来源：

- `pallets/click#3111`

主要问题：

- 负向布尔 flag 在 `default=True` 且 `flag_value=False` 时会被错误特殊处理
- 默认情况下也会直接返回 `False`

正确行为：

- 未显式提供 flag 时，应保留 `default=True`
- 显式提供负向 flag 时，才应返回 `flag_value=False`

相关文件：

- `click_flag_repo/core.py`
- `tests/test_flags.py`

### `pytest_marker_repo`

来源：

- `pytest-dev/pytest#14329`

主要问题：

- `get_closest_marker` 会错误地优先返回继承链中更早的 marker
- 当子类重新定义同名 marker 时，返回值仍然落到父类 marker

正确行为：

- 子类覆盖的 marker 应优先返回
- 只有子类未定义时，才回退到父类 marker

相关文件：

- `pytest_marker_repo/markers.py`
- `tests/test_markers.py`

### `dateutil_tz_repo`

来源：

- `dateutil/dateutil#1432`

主要问题：

- `tzstr("UTC")` 或 `tzstr("GMT")` 在未显式提供 offset 时会触发 `TypeError`
- 根因是内部继续对 `None` 做符号变换

正确行为：

- UTC / GMT 在没有 offset 时应回落到零偏移
- 不应再抛出 `TypeError`

相关文件：

- `dateutil_tz_repo/tz.py`
- `tests/test_tz.py`

### `dateutil_parser_repo_v2`

来源：

- `dateutil/dateutil#1442`

主要问题：

- 9 位时间串本应按 `HHMMSSmmm` 解释
- 当前却被错误当成不支持格式，无法得到正确的时间解析结果

正确行为：

- `040506789` 应被解析为 `04:05:06.789`
- 带空格的等价 9 位时间串也应得到相同结果

相关文件：

- `dateutil_parser_repo_v2/parser.py`
- `tests/test_parser.py`

### `jinja_meta_repo`

来源：

- `pallets/jinja#2069`

主要问题：

- 模板分析中，某个变量即便在 `if / elif / else` 所有分支都被 `set`
- 当前仍被错误地判定为 undeclared variable

正确行为：

- 所有分支都已赋值的变量不应再被判定为 undeclared
- 真正未赋值的控制变量仍应保留在 undeclared 集合中

相关文件：

- `jinja_meta_repo/meta.py`
- `tests/test_meta.py`

### `jinja_slice_repo`

来源：

- `pallets/jinja#2118`

主要问题：

- 当可迭代对象长度能被切片数整除时
- 即便所有分片长度已经一致，`slice` 仍错误补入 `fill_with`

正确行为：

- 只有存在余数时，尾部较短分片才需要补入 `fill_with`
- 整除场景下不应再额外追加填充值

相关文件：

- `jinja_slice_repo/filters.py`
- `tests/test_filters.py`

### `tomlkit_array_repo`

来源：

- `python-poetry/tomlkit#494`

主要问题：

- 原始数组格式把逗号放在下一行时
- append 新元素后错误生成了重复逗号

正确行为：

- 应保留原始“下一行开头带逗号”的风格
- 但不应在追加元素时再补出第二个逗号

相关文件：

- `tomlkit_array_repo/formatter.py`
- `tests/test_formatter.py`

### `tomlkit_inline_table_repo`

来源：

- `python-poetry/tomlkit#495`

主要问题：

- dotted inline table 追加新键后
- 新键直接黏连到旧值末尾，导致输出结构损坏

正确行为：

- 追加新键值对时应补上合法的分隔符
- 输出仍应保持一行 inline table 结构

相关文件：

- `tomlkit_inline_table_repo/formatter.py`
- `tests/test_formatter.py`

### `packaging_wheel_repo`

来源：

- `pypa/packaging#873`

主要问题：

- wheel 文件名中的版本号即便没有经过 normalization
- 当前仍会被错误接受

正确行为：

- 非 normalized 版本号应被显式拒绝
- 合法 normalized 版本号仍应继续通过解析

相关文件：

- `packaging_wheel_repo/utils.py`
- `tests/test_utils.py`

### `jsonschema_extras_repo`

来源：

- `python-jsonschema/jsonschema#1157`

主要问题：

- `extras_msg` 在 `extras` 同时包含 `bool` 和 `str` 等不同类型时
- 当前会在 `sorted(extras)` 阶段抛出 `TypeError`

正确行为：

- mixed-type extras 不应再因为排序失败而中断错误消息生成
- 同类型 extras 仍应优先保留稳定排序输出

相关文件：

- `jsonschema_extras_repo/utils.py`
- `tests/test_utils.py`

### `jsonschema_hostname_repo`

来源：

- `python-jsonschema/jsonschema#1121`

主要问题：

- hostname 格式检查在空字符串场景下
- 当前会把底层 `ValueError` 直接冒泡出去

正确行为：

- 空字符串应被视为普通格式校验失败
- 不应再让格式检查函数直接抛出 `ValueError`

相关文件：

- `jsonschema_hostname_repo/hostname.py`
- `tests/test_hostname.py`

## 当前为什么要分层

这样拆分的好处是：

- `Dev Set` 可以保持小而快，适合高频联调
- `Report Set` 可以保持相对稳定，适合做版本对比
- `Future GitHub Real-Issue Set` 可以作为更真实的最终展示与评测来源

## 环境偏差记录

规格书默认推荐 `pytest`，当前环境已安装完成。

当前 benchmark 测试命令为：

- `python -m pytest tests/test_parser.py -q`

测试代码仍保持 `unittest` 风格，因此同时兼容：

- `pytest`
- `unittest`
