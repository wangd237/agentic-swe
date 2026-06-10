# jsonschema_extend_repo

这是从 `python-jsonschema/jsonschema#1125` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- `extend()` 会复制 validator 的 `VALIDATORS`
- 但没有保留 legacy validator 的 `applicable_validators`
- 含有 `$ref` 的 schema 在扩展后会重新考虑同级关键字
- 从而破坏 Draft4 一类 legacy validator 的历史语义

期望行为：

- 扩展后的 validator 继续保留原始 `applicable_validators`
- `$ref` 场景下仍只应用 legacy validator 允许的关键字
