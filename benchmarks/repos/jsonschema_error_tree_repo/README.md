# jsonschema_error_tree_repo

这是从 `python-jsonschema/jsonschema#1328` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- `ErrorTree` 初始只包含真正有错误的索引
- 但访问一个原本没有错误的索引时
- `__getitem__` 会把这个空索引写回内部结构
- 从而污染后续的 `__iter__()` 与 `__contains__()` 结果

期望行为：

- 访问不存在的索引可以返回一个空节点
- 但不能改变树本身有哪些错误索引
