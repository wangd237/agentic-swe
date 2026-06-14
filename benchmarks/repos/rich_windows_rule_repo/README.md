# Semi-Real Scaffold

这个目录最初由 `scripts/scaffold_semi_real_task.py --from-candidate` 自动生成，随后已按 `Textualize/rich#2411` 手工压成可运行的最小 challenge semi-real repo。

当前问题：

- repo: `Textualize/rich`
- issue: `#2411`
- title: `[BUG] UnicodeEncodeError on Windows with ruler.`
- module_path: `rich_windows_rule_repo/console.py`
- test_path: `tests/test_console.py`

当前压缩口径：

- 不依赖真实 Windows / PowerShell / 控制台环境
- 只保留 `Console.rule()` / `Console.print("─")` 在 legacy 编码输出流上的安全降级语义
- `cp1252 / ascii` 路径应稳定降级为 `-`
- `utf-8` 路径仍保留 Unicode 横线
