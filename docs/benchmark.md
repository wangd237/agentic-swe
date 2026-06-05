# Benchmark 说明

## 当前 benchmark 分层

当前项目已经把 benchmark 拆成三层，分别服务不同阶段：

### 1. Dev Set

当前 manifest：

- `benchmarks/manifests/dev_tasks.json`

当前任务：

- `benchmarks/tasks/task_001.json`
- `benchmarks/tasks/task_002.json`

当前 repo：

- `benchmarks/repos/sample_repo`

用途：

- 联调单任务 patch 闭环
- 验证 batch runner 是否稳定
- 作为早期开发阶段的回归集

### 2. Report Set

当前 manifest：

- `benchmarks/manifests/report_tasks.json`

当前任务：

- `benchmarks/tasks/task_001.json`
- `benchmarks/tasks/task_003.json`

当前 repo：

- `benchmarks/repos/sample_repo`
- `benchmarks/repos/multi_bug_repo`

用途：

- 执行 baseline vs improved 的正式对比
- 生成可展示的 batch run / batch eval / compare 报告
- 验证优化动作是否真的带来指标提升

### 3. Future GitHub Real-Issue Set

当前状态：

- 暂未纳入仓库内的正式 manifest

后续规划：

- 选择 GitHub 上体量较小、测试可运行、issue 边界清晰的真实仓库
- 将真实 issue 转成结构化任务定义
- 作为项目后期更正式、更有说服力的外部评测集

这部分会在项目主链路更稳定后逐步接入。

## 当前任务设计

### `sample_repo`

主要问题：

- `parse_items([])` 会抛出 `IndexError`
- 正确行为应为返回空列表

相关文件：

- `sample_repo/parser.py`
- `tests/test_parser.py`

### `multi_bug_repo`

主要问题：

- `parse_items([])` 会抛出异常
- `parse_items([' A ', None, 'B '])` 会因为 `None.strip()` 失败
- 正确行为应为：
  - 空输入返回空列表
  - 归一化时忽略 `None`

相关文件：

- `multi_bug_repo/parser.py`
- `tests/test_parser.py`

## 当前为什么要分层

这样拆分的好处是：

- `Dev Set` 可以保持小而快，适合高频联调
- `Report Set` 可以保持相对稳定，适合做版本对比
- `Future GitHub Real-Issue Set` 可以作为更真实的最终展示与评测来源

## 环境偏差记录

规格书默认推荐 `pytest`，当前环境已安装完成。

当前 benchmark 测试命令为：

- `python -m pytest tests/test_parser.py -q`

测试代码仍保持 `unittest` 风格，因此同时兼容：

- `pytest`
- `unittest`
