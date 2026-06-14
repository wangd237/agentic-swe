from __future__ import annotations

import json
from pathlib import Path

from app.agent.patcher import apply_rule_based_patch
from app.agent.policy import PolicyConfig
from app.schemas.task_schema import Task


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_improved_v72_repairs_legacy_windows_no_color_branch(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    module_path = repo_path / "rich_windows_no_color_repo" / "console.py"
    _write_text(
        module_path,
        '"""从 rich#2457 提炼出的最小 Windows-like no_color 回归实现。"""\n\n'
        "from __future__ import annotations\n\n"
        "from dataclasses import dataclass\n\n\n"
        "@dataclass(frozen=True)\n"
        "class WindowsConsoleFeatures:\n"
        '    """只保留当前回归题所需的最小 Windows 控制台特性。"""\n\n'
        "    vt: bool = False\n"
        "    truecolor: bool = False\n\n\n"
        "class Console:\n"
        '    """模拟 Rich 在不同控制台能力下的最小着色输出行为。"""\n\n'
        "    def __init__(self, *, no_color: bool = False, legacy_windows: bool = False, features: WindowsConsoleFeatures | None = None) -> None:\n"
        "        self.no_color = no_color\n"
        "        self.legacy_windows = legacy_windows\n"
        "        self.features = features or WindowsConsoleFeatures()\n\n"
        "    def render(self, text: str, *, style: str | None = None) -> str:\n"
        "        if style is None:\n"
        "            return text\n\n"
        "        if self.legacy_windows and not self.features.vt:\n"
        "            # 这里故意保留 rich#2457 的缺陷：Windows 旧控制台分支忽略 no_color。\n"
        '            return f"<WIN:{style}>{text}</WIN:{style}>"\n\n'
        "        if self.no_color:\n"
        "            return text\n\n"
        '        return f"\\x1b[31m{text}\\x1b[0m"\n',
    )

    task = Task.model_validate(
        {
            "task_id": "task_133",
            "repo_name": "rich_windows_no_color_repo",
            "repo_path": "benchmarks/repos/rich_windows_no_color_repo",
            "issue_title": "[BUG] Console(no_color=True) does not work on Windows 10",
            "issue_text": "demo",
            "test_command": "python -m pytest tests/test_console.py -q",
            "success_criteria": "demo",
            "difficulty": "medium",
            "tags": ["semi-real", "challenge"],
            "target_files_hint": ["rich_windows_no_color_repo/console.py"],
            "source_type": "semi_real",
            "metadata": {"candidate_id": "Textualize_rich_issue_2457"},
        }
    )
    policy = PolicyConfig.model_validate(
        json.loads(
            Path(
                "E:/My_Projects/agentic-software-engineering-roadmap/optimization/policy_versions/improved_v72.json"
            ).read_text(encoding="utf-8")
        )
    )

    result = apply_rule_based_patch(
        task=task,
        repo_path=str(repo_path),
        candidate_files=["rich_windows_no_color_repo/console.py"],
        policy_config=policy,
    )

    updated_content = module_path.read_text(encoding="utf-8")
    assert result["ok"] is True
    assert result["modified_files"] == ["rich_windows_no_color_repo/console.py"]
    assert "no_color" in result["patch_reason"]
    assert "if self.no_color:\n            return text\n\n        if self.legacy_windows and not self.features.vt:" in updated_content
