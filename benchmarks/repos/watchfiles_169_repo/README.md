# Watchfiles Semi-Real Task

这个目录对应 `samuelcolvin/watchfiles#169` 的最小 semi-real challenge 草稿。

当前口径：

- 目标模块：`watchfiles/main.py`
- 测试入口：`tests/test_main.py`
- 已从自动脚手架推进到可运行最小回归任务
- 当前已纳入 challenge manifest，作为第 3 条 challenge hard case 持续观察

当前缩题策略：

- 不直接复刻 `Windows / WSL / Docker` 的真实文件系统事件环境
- 把 issue 里真正可迁移的语义压成：
  - 目标文件已经变化
  - 但 Linux-like 环境只上报 `metadata-write`
  - 当前实现错误地把这类事件过滤掉，导致不触发 reload

当前测试覆盖：

- `wsl` 下 `metadata-write` 事件命中目标文件时，当前错误地不触发 reload
- 非目标文件路径不应误触发 reload
- 普通 `modified` 事件路径应继续正常工作
