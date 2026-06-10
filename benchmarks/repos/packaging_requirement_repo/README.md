# packaging_requirement_repo

这是从 `pypa/packaging#845` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- `Requirement.__str__()` 只会在 marker 以 `extra == "..."` 开头时规范化 extra 名称
- 当 `extra` 出现在复合 marker 表达式中时，输出会保留下划线，导致行为不一致

期望行为：

- 无论 `extra` 出现在单独 marker 还是复合 marker 中
- 输出时都应统一把 extra 名称规范化为连字符风格
