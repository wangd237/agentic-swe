# Semi-Real Scaffold

这个目录对应 `python-jsonschema/jsonschema#1159` 的最小化 semi-real 任务。

当前状态：

- 已按真实 issue 还原最小 bug 场景
- 目标问题是 `multipleOf=11.0` 这样的整数值浮点数没有按数学整数处理
- 修复后应让整数值浮点数与整数 divisor 的行为保持一致
