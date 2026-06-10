# jsonschema_single_label_hostname_repo

这是从 `python-jsonschema/jsonschema#1162` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- `example.com` 这类多标签 hostname 可以通过
- `localhost` 这类单标签 hostname 会被错误拒绝

期望行为：

- 单标签 hostname 也应被视为合法
- 现有多标签合法场景保持通过
- 明显非法的 hostname 仍应返回失败
