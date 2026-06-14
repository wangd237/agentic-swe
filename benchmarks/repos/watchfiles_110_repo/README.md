# Watchfiles Semi-Real Task

这个目录对应 `samuelcolvin/watchfiles#110` 的最小 semi-real 回归任务。

当前口径：

- 目标模块：`watchfiles/main.py`
- 测试入口：`tests/test_main.py`
- 已压成可运行回归任务
- 当前已纳入 challenge manifest，作为第 2 条 challenge hard case 持续观察

当前缩题策略：

- 不直接复刻 `Windows + Ctrl+C + Rust watcher` 的真实平台环境
- 把 issue 里真正可迁移的语义压成：
  - 当 stop 请求发生在底层 `watch()` 阻塞期间
  - 当前 awatch 循环不会及时退出
  - 而是仍会等到底层返回一个事件后才结束

当前测试覆盖：

- stop 请求发生在 `watch()` 期间时，当前错误地返回事件
- stop 请求如果在进入 `watch()` 之前出现，应立即退出
- 没有 stop 请求时，正常事件路径仍应工作
