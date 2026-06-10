# sqlite_delete_repo

这是从 `simonw/sqlite-utils#159` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- `insert()` 与 `upsert()` 都会自动提交事务
- 但 `delete_where()` 删除后没有提交事务
- 这会导致其他数据库连接看不到最新删除结果

期望行为：

- `delete_where()` 应与其他写操作保持一致
- 删除完成后立即提交事务
- 后续读取应能立刻观察到最新状态
