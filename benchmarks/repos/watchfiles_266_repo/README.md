# Watchfiles Semi-Real Task

这个目录对应 `samuelcolvin/watchfiles#266` 的最小 semi-real 回归任务。

当前口径：

- 目标模块：`watchfiles/main.py`
- 测试入口：`tests/test_main.py`
- 已压成可运行回归任务
- 仍未纳入正式 `real_issue_tasks.json`

当前缩题策略：

- 不直接复刻 WSL / Docker / Windows 挂载环境
- 把 issue 里真正可迁移的语义压成：
  - 当 `ignore_permission_denied=True` 时
  - `error_handler` 抛出的底层 watcher `OSError`
  - 不应再被重新包装后继续中断上层调用

当前测试覆盖：

- `FileNotFoundError` 在标志开启时仍会被错误包装抛出
- `PermissionError` 在标志开启时会被忽略
- 标志关闭时仍应继续抛错
