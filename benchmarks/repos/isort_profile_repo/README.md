# isort_profile_repo

这是从 `PyCQA/isort#1815` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- tuple/list 这类容器格式化分支没有正确继承 `profile` 对应的布局策略
- 即使调用方传入 `profile="black"`，tuple 仍按默认紧凑风格排版
- 结果会与 profile 驱动的整体格式期望不一致

期望行为：

- tuple 格式化应考虑 profile 提供的布局风格
- `profile="black"` 时应使用多行缩进布局
- 默认 profile 行为不回归
