# AnyIO TaskGroup Reentry Repo

这个目录是从 `agronholm/anyio#1109` 提炼出的最小 semi-real bug repo。

当前保留的核心语义：

- 公开入口：
  - `anyio.create_task_group()`
  - `anyio.run(...)`
- 目标模块：
  - `anyio/_backends/_asyncio.py`
- 回归测试：
  - `tests/test_taskgroups.py`

当前故意保留的 bug：

- 同一个 `TaskGroup` 第一次退出后会删除内部 `_exceptions`
- 第二次再次退出同一个 context manager 时，会因为 `_exceptions` 未重新初始化而触发 `AttributeError`

期望修复方向：

- 重复进入同一个 `TaskGroup` 时，应抛出受控错误
- 不应再泄漏内部属性缺失导致的 `AttributeError`
