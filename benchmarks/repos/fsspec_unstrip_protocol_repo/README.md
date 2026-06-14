# Semi-Real Scaffold

这个目录由 `scripts/scaffold_semi_real_task.py --from-candidate` 自动生成。

当前候选：

- repo: `fsspec/filesystem_spec`
- issue: `#979`
- title: `bug: unstrip_protocol incorrectly returns original path`
- inferred module_path: `fsspec/spec.py`
- inferred test_path: `fsspec/tests/test_spec.py`

接下来需要：

- 人工 review 自动推断出的模块与测试路径
- 按真实 issue 还原最小 bug 场景
- 把 TODO 测试改成稳定回归测试
- 完成后再把该任务加入正式 manifest
