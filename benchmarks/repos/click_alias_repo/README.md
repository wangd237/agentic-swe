# click_alias_repo

这是从 `pallets/click#2402` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- `AliasedGroup.resolve_command()` 直接访问 `cmd.name`
- 当底层解析结果里 `cmd` 为 `None` 时，会抛出 `AttributeError`

期望行为：

- 缺失命令或拼写错误时，不应因为 `cmd is None` 而直接崩溃
- 应保持“未解析到命令”的普通返回语义
