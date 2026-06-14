# Semi-Real Scaffold

这个目录由 `scripts/scaffold_semi_real_task.py --from-candidate` 自动生成，并已补成最小可运行 bug repo。

当前候选：

- repo: `agronholm/anyio`
- issue: `#1111`
- title: `100% CPU spin in asyncio _deliver_cancellation due to missing task.done() check`
- module_path: `anyio/_backends/_asyncio.py`
- test_path: `tests/test__asyncio.py`

当前状态：

- 已还原 `_deliver_cancellation` 缺少 `task.done()` 检查的最小缺陷
- 已补成 2 条稳定测试
- 目标口径应为：
  - 正常路径通过
  - 已完成 task 残留时触发目标回归失败
