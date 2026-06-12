# tomlkit Out-Of-Order Repo

这个 semi-real repo 对应 `python-poetry/tomlkit#505`。

当前最小化场景聚焦：

- `parse_document()` 能接受一个合法的最小 TOML 文本
- 但后续 `doc.get("hooks")` 在代理重建阶段会错误抛出 `KeyAlreadyPresent`
- 触发条件是：重复 array table 与同级子表同时存在

体验方式：

- 先运行 `python -m pytest tests/test_proxy.py -q` 观察失败
- 再用 benchmark 主链运行 `task_101`
