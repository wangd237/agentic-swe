# Watchfiles Semi-Real Task

这个目录对应 `samuelcolvin/watchfiles#215` 的最小 semi-real challenge 回归任务。

当前口径：

- 目标模块：`watchfiles/main.py`
- 测试入口：`tests/test_main.py`
- 已压成可运行的最小回归任务
- 当前已纳入 challenge manifest，作为第 4 条 challenge hard case 持续观察

当前缩题策略：

- 不直接依赖真实 `vim`、文件系统事件或实时 watcher 环境
- 把 issue 里真正可迁移的语义压成：
  - 单文件 watch 下收到 `remove` 后，当前实现错误地把目标文件当成真实删除
  - 结果是不再 reload，也不再继续保持对目标文件的 watch

当前测试覆盖：

- `vim` 风格保存事件序列下，当前错误地停止 reload 与继续 watch
- 目录式替换事件序列不应被误判成删除目标文件
- 普通 `modified` 事件路径应继续正常工作
