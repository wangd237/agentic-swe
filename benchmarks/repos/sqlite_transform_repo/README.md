# sqlite_transform_repo

这是从 `simonw/sqlite-utils#488` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- 文本列转换成 `integer` 或 `float` 时，空字符串仍被保留成 `""`
- 这会让“空值”与“合法数值字符串”在结果里混在一起
- 下游读取时不能把它当成真正的 `null`

期望行为：

- 转成 `integer` 或 `float` 时，空字符串应回落为 `None`
- 非空数字字符串仍应正常转换
- 不在目标列中的普通文本值不回归
