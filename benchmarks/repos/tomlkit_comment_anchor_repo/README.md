# tomlkit Comment Anchor Repo

这个 semi-real repo 对应 `python-poetry/tomlkit#295`。

当前最小化场景聚焦：

- 原始 TOML 里第二个 `[[routes]]` 前有一条注释
- 当给第一个 `routes` 条目追加子表后
- 重渲染结果错误把第二个 routes 的注释一起吸附到了新子表前

体验方式：

- 先运行 `python -m pytest tests/test_renderer.py -q` 观察失败
- 再用 benchmark 主链运行 `task_103`
