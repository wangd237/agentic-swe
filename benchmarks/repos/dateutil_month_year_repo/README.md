# dateutil_month_year_repo

这是从 `dateutil/dateutil#384` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- `MM/YYYY` 可以正确解析成年月
- `MM.YYYY` 却走了错误分支，导致年月顺序被错误解释

期望行为：

- `05.2016` 应与 `05/2016` 保持一致
- 都应被解析成 `2016-05` 这一组年月语义
