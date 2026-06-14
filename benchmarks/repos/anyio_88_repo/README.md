# Semi-Real Scaffold

这个目录由 `scripts/scaffold_semi_real_task.py --from-candidate` 自动生成。

当前候选：

- repo: `agronholm/anyio`
- issue: `#88`
- title: `Parent task spuriously cancelled with asyncio`
- inferred module_path: `anyio/module.py`
- inferred test_path: `tests/test_fail_case.py`

接下来需要：

- 当前已完成：
  - 已把 issue 压成最小并发回归任务
  - 正常路径测试 `1` 条通过
  - 目标 asyncio 回归测试 `1` 条失败
- 下一步需要：
  - 继续观察是否应把目标模块从 `anyio/module.py` 收敛到更具体的 backend / task-group 路径
  - 用当前 bug repo 做单任务修复验证
  - 验证通过后再决定是否纳入正式 manifest
