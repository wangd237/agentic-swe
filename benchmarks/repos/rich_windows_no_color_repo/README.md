# Semi-Real Scaffold

这个目录由 `scripts/scaffold_semi_real_task.py --from-candidate` 自动生成，随后已人工压成可运行 challenge 题。

当前候选：

- repo: `Textualize/rich`
- issue: `#2457`
- title: `[BUG] Console(no_color=True) does not work on Windows 10`
- inferred module_path: `rich_windows_no_color_repo/console.py`
- inferred test_path: `tests/test_console.py`

当前缩题口径：

- 不依赖真实 Windows 10 / cmd.exe / Cmder
- 只保留 `legacy_windows=True + vt=False` 这条最小平台语义分支
- 用 `no_color=True` 是否仍错误输出 Windows 样式标记来表达原 issue
- 相邻保留路径：
  - `no_color=False` 时仍保留 Windows 样式
  - 非 Windows / 支持 VT 的路径继续遵守 `no_color`

当前目标文件：

- `rich_windows_no_color_repo/console.py`
- `tests/test_console.py`
