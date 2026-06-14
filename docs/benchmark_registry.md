# Benchmark 注册表

本文件用于把当前正式 benchmark 任务压缩成可快速检索的目录。

建议用途：

- 快速确认当前已经覆盖了哪些缺陷类型
- 找到某条任务首次通过的 policy 版本
- 规划下一条 issue 时避免语义重复
- 判断某条任务是否应该进入后续冻结集合
- 区分哪些任务属于正式主集，哪些属于 challenge 集

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
| `task_071` | `python-poetry/tomlkit#383` | `tomlkit_proxy_repo` | `OutOfOrderTableProxy.pop()` 未同步删除底层键 | `improved_v38` | `-` |
| `task_073` | `python-poetry/tomlkit#431` | `tomlkit_super_table_repo` | super table 下新增 dotted key 时父级前缀丢失 | `improved_v39` | `-` |
| `task_075` | `pallets/jinja#2151` | `jinja_async_repr_repo` | `AsyncLoopContext.__repr__` 暴露协程对象并触发未 awaited 警告 | `improved_v40` | `-` |
| `task_077` | `pallets/jinja#2176` | `jinja_indent_repo` | `indent` 首行空白时错误无视 `blank=False` | `improved_v41` | `-` |
| `task_079` | `python-poetry/tomlkit#440` | `tomlkit_inline_newline_repo` | dotted inline table 后续追加普通键时缺少换行 | `improved_v42` | `40` |
| `task_081` | `python-poetry/tomlkit#504` | `tomlkit_scalar_capture_repo` | 中间表替换成标量后被错误吸附到相邻表作用域 | `improved_v43` | `40` |
| `task_083` | `pypa/packaging#1204` | `packaging_pickle_repo` | Requirement pickle 后丢失 `specifier.prereleases` 显式状态 | `improved_v44` | `-` |
| `task_085` | `pydantic/pydantic#13257` | `pydantic_fraction_repo` | fraction 零分母输入未被统一映射为 `ValidationError` | `improved_v45` | `-` |
| `task_087` | `python-poetry/tomlkit#439` | `tomlkit_repr_repo` | 代理视图 `repr` 漏掉同父路径早期 dotted key 子项 | `improved_v46` | `-` |
| `task_089` | `pallets/jinja#2165` | `jinja_map_default_repo` | `map(attribute=..., default=None)` 未回落 `None` 默认值 | `improved_v47` | `-` |
| `task_091` | `pypa/packaging#1240` | `packaging_direct_url_repo` | file URL scheme 大小写与单斜杠形式校验错误 | `improved_v48` | `-` |
| `task_093` | `pallets/click#3572` | `click_confirm_repo` | `confirm(color=False)` 未去除 ANSI 提示颜色 | `improved_v49` | `-` |
| `task_095` | `pallets/click#3125` | `click_version_repo` | `version_option(package_name=...)` 忽略显式包名 | `improved_v50` | `-` |
| `task_097` | `pallets/click#3571` | `click_progressbar_repo` | `show_pos=True` 且 `update_min_steps` 不整除时结束态位置未显示完整进度 | `improved_v51` | `-` |
| `task_099` | `pallets/jinja#2108` | `jinja_include_repo` | macro 内部 `include without context` 错误输出 generator repr | `improved_v52` | `-` |
| `task_101` | `python-poetry/tomlkit#505` | `tomlkit_out_of_order_repo` | out-of-order table 访问阶段重复 array table 与同级子表共存时触发重复键异常 | `improved_v53` | `-` |
| `task_103` | `python-poetry/tomlkit#295` | `tomlkit_comment_anchor_repo` | AoT 条目追加子表后原有注释锚点跑偏 | `improved_v54` | `-` |
| `task_105` | `pytest-dev/pytest#14189` | `pytest_caplog_filter_repo` | 嵌套 caplog filtering 提前移除外层 filter | `improved_v55` | `-` |
| `task_107` | `python-poetry/tomlkit#430` | `tomlkit_single_key_repo` | 单元素列表 key 规范被错误构造成 DottedKey | `improved_v56` | `-` |
| `task_109` | `pypa/packaging#1231` | `packaging_name_normalization_repo` | `is_normalized_name()` 错误拒绝 `canonicalize_name()` 已稳定的前后连字符名称 | `improved_v57` | `-` |
| `task_111` | `pallets/click#3362` | `click_usage_repo` | usage 换行时在连字符处分裂长选项 | `improved_v58` | `-` |
| `task_113` | `pypa/distlib#238` | `distlib_wheel_repo` | WHEEL metadata 漏写 `Build:` 行 | `improved_v59` | `-` |
| `task_115` | `pytest-dev/pytest#14474` | `pytest_expression_repo` | marker expression 扫描字符串字面量时错误检查整个输入里的反斜杠 | `improved_v60` | `-` |
| `task_117` | `python-poetry/tomlkit#346` | `tomlkit_negative_int_repo` | 负整数原地翻转时文本符号循环污染 | `improved_v61` | `-` |
| `task_119` | `python-poetry/tomlkit#450` | `tomlkit_bool_comment_repo` | table 中 bool 项退化成原生值导致 comment API 丢失 | `improved_v62` | `-` |
| `task_121` | `python-poetry/tomlkit#412` | `tomlkit_int_key_repo` | 容器接口对整数 key 的规范化与解析路径语义不一致 | `improved_v63` | `-` |
| `task_122` | `fsspec/filesystem_spec#979` | `fsspec_unstrip_protocol_repo` | `unstrip_protocol()` 在前缀相似路径上错误返回原串 | `improved_v64` | `-` |
| `task_123` | `agronholm/anyio#1109` | `anyio_taskgroup_reentry_repo` | 重复进入 `TaskGroup` 时泄漏内部 `_exceptions` 属性错误 | `improved_v65` | `-` |
| `task_124` | `agronholm/anyio#1111` | `anyio_cancellation_spin_repo` | `_deliver_cancellation()` 遇到已完成 task 时持续自我重排 | `improved_v66` | `-` |
| `task_125` | `agronholm/anyio#1113` | `anyio_check_cancelled_repo` | `from_thread.check_cancelled()` 在 asyncio backend 下泄漏取消异常 | `improved_v69` | `-` |
| `task_128` | `agronholm/anyio#82` | `anyio_82_repo` | asyncio / curio backend 在嵌套 task group 中泄漏取消异常 | `improved_v71` | `-` |
| `task_129` | `agronholm/anyio#88` | `anyio_88_repo` | asyncio backend 下父任务在子任务失败后被额外取消 | `improved_v70` | `-` |

## Challenge 任务

| task_id | 来源 issue | semi_real repo | 当前状态 | 备注 |
| --- | --- | --- | --- | --- |
| `task_126` | `samuelcolvin/watchfiles#266` | `watchfiles_266_repo` | `accepted + ready + in_challenge_manifest` | 当前更适合作为系统边界展示题，暂不并入正式主集 |
| `task_127` | `samuelcolvin/watchfiles#110` | `watchfiles_110_repo` | `accepted + ready + in_challenge_manifest` | 当前更适合作为 hard case challenge 题，暂不并入正式主集 |
| `task_130` | `samuelcolvin/watchfiles#169` | `watchfiles_169_repo` | `accepted + ready + in_challenge_manifest` | WSL / Docker / Linux-like metadata-write 事件过滤边界题 |
| `task_131` | `samuelcolvin/watchfiles#215` | `watchfiles_215_repo` | `accepted + ready + in_challenge_manifest` | 编辑器保存行为下 Remove(File) 事件语义边界题 |
| `task_132` | `Textualize/rich#2411` | `rich_windows_rule_repo` | `accepted + ready + in_challenge_manifest` | Windows-like legacy 编码流字符降级边界题 |
| `task_133` | `Textualize/rich#2457` | `rich_windows_no_color_repo` | `accepted + ready + in_challenge_manifest` | Windows-like legacy console 下 no_color 语义边界题 |

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
- 代理容器删除语义
- super table / dotted key 组合渲染
- async runtime 表示层
- filter 参数交互边界
- inline table 后续渲染换行边界
- table 替换成 scalar 后的作用域保真
- pickle / unpickle 后的显式配置状态保真
- 验证器异常映射与用户态错误语义保真
- 代理视图表示层与真实嵌套语义一致性
- filter 默认值语义与显式 `None` 回落一致性
- URL scheme 规范化与 file URL 合法形式兼容性
- prompt / confirm 输出链路中的 ANSI 清理一致性
- 版本选项元数据渲染与显式参数优先级
- progressbar 结束态位置渲染与中间刷新位置解耦
- macro 内部 include 渲染与 without-context 语义保真
- out-of-order table 代理重建与 repeated array table 聚合语义保真
- array-of-tables 条目扩写后的注释锚点与原始文档相对位置保真
- 嵌套日志过滤上下文与外层 filter 生命周期保真
- 单元素列表 key 规范与单字符串 key 语义一致性
- 名称规范化 roundtrip 语义与边界连字符 canonical 输出一致性
- usage 帮助文本换行与连字符长选项的原子性保真
- wheel metadata 生成与 build tag 文本保真
- marker expression 扫描作用域与字符串字面量边界保真
- 数值原地更新后的文本符号规范化保真
- item 包装保真与后续链式 comment API 可用性
- 容器接口 key 规范化与解析入口语义一致性

## 当前仍相对欠缺的方向

- profile 驱动的排序 / 分派语义

## 相关文件

- 当前正式 manifest：
  - `benchmarks/manifests/real_issue_tasks.json`
- 当前 challenge manifest：
  - `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- challenge 说明文档：
  - `docs/challenge_set.md`
- 当前冻结 manifest：
  - `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_18_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_20_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_40_v1.json`
- 候选池：
  - `benchmarks/real_world_candidates.json`
