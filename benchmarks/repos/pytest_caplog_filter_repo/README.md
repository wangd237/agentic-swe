# pytest caplog filter benchmark

这是从 `pytest-dev/pytest#14189` 提炼出的最小 `semi_real` benchmark。

当前保留的缺陷是：

- 嵌套使用相同 filter 的过滤上下文时
- 内层退出会把外层仍在使用的 filter 提前移除
- 导致外层上下文后半段错误开始重新捕获日志
