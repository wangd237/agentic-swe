# Benchmark 注册表

本文件用于把当前正式 benchmark 任务压缩成可快速检索的目录。

建议用途：

- 快速确认当前已经覆盖了哪些缺陷类型
- 找到某条任务首次通过的 policy 版本
- 规划下一条 issue 时避免语义重复
- 判断某条任务是否应该进入后续冻结集合

## 正式真实任务

| task_id | 来源 issue | semi_real repo | 缺陷类型 | 首个通过版本 | 冻结集 |
| --- | --- | --- | --- | --- | --- |
| `task_006` | `psf/requests#6432` | `requests_compat_repo` | 依赖约束上界放宽 | `improved_v3` | `15/18/20` |
| `task_008` | `psf/requests#7234` | `requests_encoding_repo` | quoted charset 去引号解析 | `improved_v4` | `15/18/20` |
| `task_010` | `Textualize/rich#4090` | `rich_ansi_repo` | CRLF ANSI 行拆分 | `improved_v5` | `15/18/20` |
| `task_013` | `Textualize/rich#3877` | `rich_handler_repo` | 时区偏移格式化 | `improved_v6` | `15/18/20` |
| `task_016` | `pallets/click#3111` | `click_flag_repo` | 负向 boolean flag 默认值 | `improved_v7` | `15/18/20` |
| `task_017` | `pytest-dev/pytest#14329` | `pytest_marker_repo` | 最近 marker 覆盖优先 | `improved_v8` | `15/18/20` |
| `task_019` | `dateutil/dateutil#1432` | `dateutil_tz_repo` | UTC/GMT 零偏移回落 | `improved_v9` | `15/18/20` |
| `task_022` | `dateutil/dateutil#1442` | `dateutil_parser_repo_v2` | 9 位时间串解析 | `improved_v10` | `15/18/20` |
| `task_024` | `pallets/jinja#2069` | `jinja_meta_repo` | 分支全赋值变量分析 | `improved_v11` | `15/18/20` |
| `task_026` | `pallets/jinja#2118` | `jinja_slice_repo` | `slice(fill_with)` 整除边界 | `improved_v12` | `15/18/20` |
| `task_028` | `python-poetry/tomlkit#494` | `tomlkit_array_repo` | 数组下一行逗号风格 append | `improved_v13` | `15/18/20` |
| `task_030` | `python-poetry/tomlkit#495` | `tomlkit_inline_table_repo` | dotted inline table 分隔修复 | `improved_v14` | `15/18/20` |
| `task_032` | `pypa/packaging#873` | `packaging_wheel_repo` | wheel 版本 normalization 校验 | `improved_v15` | `15/18/20` |
| `task_034` | `python-jsonschema/jsonschema#1157` | `jsonschema_extras_repo` | mixed-type extras 错误消息渲染 | `improved_v16` | `15/18/20` |
| `task_036` | `python-jsonschema/jsonschema#1121` | `jsonschema_hostname_repo` | hostname 格式检查异常回落 | `improved_v17` | `15/18/20` |
| `task_038` | `python-jsonschema/jsonschema#1159` | `jsonschema_multipleof_repo` | integer-valued `multipleOf` 浮点数数值语义 | `improved_v18` | `18/20` |
| `task_040` | `pypa/packaging#845` | `packaging_requirement_repo` | Requirement extra 字符串规范化 | `improved_v19` | `18/20` |
| `task_042` | `pallets/click#2402` | `click_alias_repo` | `cmd is None` 异常回落 | `improved_v20` | `18/20` |
| `task_044` | `dateutil/dateutil#384` | `dateutil_month_year_repo` | `MM.YYYY` 月年格式解析 | `improved_v21` | `20` |
| `task_046` | `python-jsonschema/jsonschema#1162` | `jsonschema_single_label_hostname_repo` | single-label hostname 合法性判定 | `improved_v22` | `20` |
| `task_048` | `pypa/packaging#810` | `packaging_specifier_repo` | `Specifier >` 在 `dev+local` 场景下的比较语义 | `improved_v23` | `-` |
| `task_050` | `dateutil/dateutil#1191` | `dateutil_attached_comma_repo` | 年份前紧贴逗号时的 parser token 识别 | `improved_v24` | `-` |
| `task_052` | `python-jsonschema/jsonschema#1328` | `jsonschema_error_tree_repo` | 访问缺失索引时的 ErrorTree 状态污染 | `improved_v25` | `-` |
| `task_054` | `python-jsonschema/jsonschema#1125` | `jsonschema_extend_repo` | `extend()` 丢失 `applicable_validators` 语义 | `improved_v26` | `-` |
| `task_056` | `simonw/sqlite-utils#159` | `sqlite_delete_repo` | `delete_where()` 删除后未提交事务 | `improved_v27` | `-` |
| `task_057` | `pydantic/pydantic#9582` | `pydantic_inheritance_repo` | 子类 `model_validator` 覆盖父类校验链 | `improved_v28` | `-` |
| `task_058` | `python-attrs/attrs#1479` | `attrs_alias_repo` | `field_transformer` 阶段默认 alias 不可见 | `improved_v29` | `-` |
| `task_059` | `simonw/sqlite-utils#488` | `sqlite_transform_repo` | 数值列转换时空字符串保留为 `""` | `improved_v30` | `-` |
| `task_060` | `simonw/sqlite-utils#186` | `sqlite_extract_repo` | extract 时为 `None` 生成冗余维表记录 | `improved_v31` | `-` |
| `task_063` | `pypa/packaging#638` | `packaging_marker_repo` | `Marker.evaluate(extra=None)` 对 `None` 调用 `.lower()` | `improved_v34` | `-` |
| `task_065` | `pypa/packaging#788` | `packaging_prerelease_repo` | `< prerelease` 比较错误排除了更早的合法 prerelease | `improved_v35` | `-` |
| `task_067` | `pypa/packaging#909` | `packaging_tag_order_repo` | wheel compressed tag set 未排序时仍被错误接受 | `improved_v36` | `-` |
| `task_069` | `python-poetry/tomlkit#442` | `tomlkit_boolean_repo` | `boolean(True)` 被错误序列化为 `false` | `improved_v37` | `-` |

## 当前覆盖的缺陷类型分布

- 依赖约束 / requirement 范围
- 字符串解析 / 引号处理
- 换行与文本拆分
- 时间格式化 / 时区偏移
- 参数默认值语义
- 继承 / 覆盖优先级
- 时区解析边界
- 时间串解析边界
- 月年 parser 容错
- 控制流分支分析
- 切片 / 填充值边界
- 序列化 / 分隔符保真
- 版本规范校验
- 错误消息渲染
- 异常回落与普通失败语义
- single-label hostname 规范边界
- 数值语义 / 浮点与整数一致性
- marker / requirement 字符串规范化
- `dev/local` 版本比较边界
- 紧贴标点时的日期年份 token 识别
- 容器状态污染 / 惰性访问副作用
- validator 扩展时的 legacy 关键字适用范围继承
- 数据库多连接下的事务提交可见性
- 模型继承链上的 validator 追加执行
- CLI 命令解析回落
- TOML 布尔字面量序列化

## 当前仍相对欠缺的方向

- profile 驱动的排序 / 分派语义
- super table / dotted key 组合渲染
- async runtime 表示层与告警边界

## 相关文件

- 当前正式 manifest：
  - `benchmarks/manifests/real_issue_tasks.json`
- 当前冻结 manifest：
  - `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_18_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_20_v1.json`
- 候选池：
  - `benchmarks/real_world_candidates.json`
