# sqlite_extract_repo

这是从 `simonw/sqlite-utils#186` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- 对某列做提取时，`None` 也会被当成一个需要落入维表的值
- 这会生成一个值为 `None` 的冗余记录
- 主表里的外键映射也会错误指向这条“空值记录”

期望行为：

- `None` 不应参与维表提取
- 非空值仍应正常生成维表记录并建立映射
- 原始空值在主表中应继续保留为 `None`
