# Semi-Real Scaffold

这个目录对应 `python-jsonschema/jsonschema#1121` 的最小化 semi-real 任务。

当前状态：

- 已按真实 issue 还原最小 bug 场景
- 目标问题是 hostname 格式检查在空字符串场景下错误抛出 `ValueError`
- 修复后应改为普通格式校验失败，而不是异常中断
