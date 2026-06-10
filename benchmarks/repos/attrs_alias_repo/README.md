# attrs_alias_repo

这是从 `python-attrs/attrs#1479` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- 字段对象在 `field_transformer` 运行时还拿不到默认 alias
- 显式 alias 会提前可见，但默认 alias 要等类构建结束后才回填
- 这会让依赖 alias 做字段变换的逻辑在定义阶段拿到 `None`

期望行为：

- `field_transformer` 运行时就能读取最终 alias
- 默认 alias 应与字段名一致
- 显式 alias 的行为不回归
