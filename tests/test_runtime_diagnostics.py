from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.task_runner import run_observation_task
from app.tools.run_tests import _build_failure_summary, _inject_pytest_flags, run_tests


def test_inject_pytest_flags_only_appends_for_pytest_commands() -> None:
    assert _inject_pytest_flags("python -m pytest tests/test_demo.py -q", ["-p no:unraisableexception"]) == (
        "python -m pytest tests/test_demo.py -q --tb=short --no-header --disable-warnings -p no:unraisableexception"
    )
    assert _inject_pytest_flags("python -m unittest -q", ["-p no:unraisableexception"]) == "python -m unittest -q"
    assert _inject_pytest_flags(
        "python -m pytest tests/test_demo.py -q --tb=short --no-header --disable-warnings -p no:unraisableexception",
        ["-p no:unraisableexception"],
    ) == "python -m pytest tests/test_demo.py -q --tb=short --no-header --disable-warnings -p no:unraisableexception"


def test_run_tests_returns_split_duration_metrics(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    test_file = repo_dir / "test_pass.py"
    test_file.write_text(
        "def test_pass():\n"
        "    assert True\n",
        encoding="utf-8",
    )

    result = run_tests(str(repo_dir), "python -m pytest test_pass.py -q", timeout_sec=30)

    assert result["ok"] is True
    assert isinstance(result["data"]["resolve_repo_path_duration_sec"], float)
    assert isinstance(result["data"]["env_setup_duration_sec"], float)
    assert isinstance(result["data"]["pre_execution_duration_sec"], float)
    assert isinstance(result["data"]["command_execution_duration_sec"], float)
    assert isinstance(result["data"]["subprocess_duration_sec"], float)
    assert isinstance(result["data"]["summary_extraction_duration_sec"], float)
    assert result["data"]["pre_execution_duration_sec"] >= 0.0
    assert result["data"]["command_execution_duration_sec"] >= 0.0
    assert result["data"]["subprocess_duration_sec"] >= 0.0
    assert result["data"]["summary_extraction_duration_sec"] >= 0.0
    assert result["data"]["subprocess_duration_sec"] == result["data"]["command_execution_duration_sec"]
    assert result["data"]["duration_sec"] >= result["data"]["pre_execution_duration_sec"]
    assert result["data"]["duration_sec"] >= result["data"]["subprocess_duration_sec"]


def test_run_tests_forces_utf8_subprocess_io(tmp_path: Path, monkeypatch) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    observed_kwargs: dict[str, object] = {}

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed_kwargs.update(kwargs)
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_tests(str(repo_dir), "python -m pytest test_pass.py -q", timeout_sec=30)

    assert result["ok"] is True
    assert observed_kwargs["encoding"] == "utf-8"
    assert observed_kwargs["errors"] == "replace"
    assert observed_kwargs["text"] is True
    env = observed_kwargs["env"]
    assert isinstance(env, dict)
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["PYTHONUTF8"] == "1"


def test_run_tests_prioritizes_workspace_src_on_pythonpath(tmp_path: Path, monkeypatch) -> None:
    repo_dir = tmp_path / "repo"
    external_dir = tmp_path / "external"
    (repo_dir / "src" / "demo_pkg").mkdir(parents=True)
    (external_dir / "demo_pkg").mkdir(parents=True)
    (repo_dir / "src" / "demo_pkg" / "__init__.py").write_text("VALUE = 'workspace'\n", encoding="utf-8")
    (external_dir / "demo_pkg" / "__init__.py").write_text("VALUE = 'external'\n", encoding="utf-8")
    (repo_dir / "test_import.py").write_text(
        "from demo_pkg import VALUE\n\n"
        "def test_workspace_src_wins():\n"
        "    assert VALUE == 'workspace'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONPATH", str(external_dir))

    result = run_tests(str(repo_dir), "python -m pytest test_import.py -q", timeout_sec=30)

    assert result["ok"] is True
    assert result["data"]["pythonpath_prefix"] == [str(repo_dir.resolve()), str((repo_dir / "src").resolve())]


def test_run_tests_records_injected_pytest_flags(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    test_file = repo_dir / "test_pass.py"
    test_file.write_text(
        "def test_pass():\n"
        "    assert True\n",
        encoding="utf-8",
    )

    result = run_tests(
        str(repo_dir),
        "python -m pytest test_pass.py -q",
        timeout_sec=30,
        additional_pytest_flags=["-p no:unraisableexception"],
    )

    assert result["ok"] is True
    assert result["data"]["original_command"] == "python -m pytest test_pass.py -q"
    assert result["data"]["additional_pytest_flags"] == ["-p no:unraisableexception"]
    assert result["data"]["command"].endswith("-p no:unraisableexception")


def test_build_failure_summary_extracts_pytest_assertion_details() -> None:
    pytest_output = """
=================================== FAILURES ===================================
__________________________________ test_value __________________________________

    def test_value():
>       assert value() == 2
E       assert 1 == 2
E        +  where 1 = value()

tests/test_app.py:4: AssertionError
=========================== short test summary info ============================
FAILED tests/test_app.py::test_value - assert 1 == 2
"""

    summary = _build_failure_summary(pytest_output, "", 1)

    assert summary["failed_tests"] == ["tests/test_app.py::test_value - assert 1 == 2"]
    assert "assert value() == 2" in summary["assertion_lines"]
    assert "assert 1 == 2" in summary["assertion_lines"]
    assert summary["locations"] == [
        {
            "path": "tests/test_app.py",
            "line": 4,
            "error": "AssertionError",
        }
    ]
    assert "tests/test_app.py::test_value" in summary["short_summary"]
    assert "tests/test_app.py:4" in summary["short_summary"]
    assert "assert 1 == 2" in summary["short_summary"]
    assert summary["short_summary"].index("assert 1 == 2") < summary["short_summary"].index("tests/test_app.py::test_value")
    assert "E       assert 1 == 2" in summary["output_excerpt"]


def test_build_failure_summary_includes_output_excerpt_for_unittest_failures() -> None:
    pytest_output = """
=================================== FAILURES ===================================
___________ SpecifierContainsTests.test_larger_dev_with_local_is_greater ___________

self = <tests.test_specifiers.SpecifierContainsTests testMethod=test_larger_dev_with_local_is_greater>

    def test_larger_dev_with_local_is_greater(self) -> None:
        spec = Specifier(">4.1.0a2.dev1234")

>       self.assertTrue(spec.contains("4.1.0a2.dev1235+local", prereleases=True))
E       AssertionError: False is not true

tests/test_specifiers.py:36: AssertionError
"""

    summary = _build_failure_summary(pytest_output, "", 1)

    assert "self.assertTrue" in summary["output_excerpt"]
    assert "False is not true" in summary["output_excerpt"]
    assert summary["locations"][0]["path"] == "tests/test_specifiers.py"


def test_build_failure_summary_extracts_plain_traceback_exception_signal() -> None:
    traceback_output = """
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    assert 'S' in ds.PatientName
TypeError: argument of type 'PersonName' is not iterable
"""

    summary = _build_failure_summary("", traceback_output, 1)

    assert summary["exception"] == {
        "type": "TypeError",
        "message": "argument of type 'PersonName' is not iterable",
    }
    assert summary["possible_symbols"] == ["PersonName"]
    assert "TypeError" in summary["short_summary"]
    assert "PersonName" in summary["short_summary"]
    assert "not iterable" in summary["output_excerpt"]


def test_run_tests_returns_failure_summary(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    test_file = repo_dir / "test_fail.py"
    test_file.write_text(
        "def value():\n"
        "    return 1\n\n"
        "def test_value():\n"
        "    assert value() == 2\n",
        encoding="utf-8",
    )

    result = run_tests(str(repo_dir), "python -m pytest test_fail.py -q", timeout_sec=30)

    failure_summary = result["data"]["failure_summary"]
    assert result["ok"] is False
    assert "--tb=short" in result["data"]["command"]
    assert "--no-header" in result["data"]["command"]
    assert "--disable-warnings" in result["data"]["command"]
    assert failure_summary["failed_tests"]
    assert any("test_value" in item for item in failure_summary["failed_tests"])
    assert failure_summary["locations"]
    assert failure_summary["locations"][0]["path"] == "test_fail.py"
    assert failure_summary["assertion_lines"]
    assert "assert value() == 2" in failure_summary["short_summary"]
    assert "assert value() == 2" in failure_summary["output_excerpt"]


def test_run_tests_preserves_non_ascii_pytest_output(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    test_file = repo_dir / "test_fail_unicode.py"
    test_file.write_text(
        "def test_unicode_value():\n"
        "    assert '实际' == '期望'\n",
        encoding="utf-8",
    )

    result = run_tests(str(repo_dir), "python -m pytest test_fail_unicode.py -q", timeout_sec=30)

    failure_summary = result["data"]["failure_summary"]
    assert result["ok"] is False
    assert "实际" in result["data"]["stdout"]
    assert "期望" in result["data"]["stdout"]
    assert any("实际" in line for line in failure_summary["assertion_lines"])
    assert any("期望" in line for line in failure_summary["assertion_lines"])


def test_run_observation_task_writes_trace_tool_metrics() -> None:
    output = run_observation_task(
        task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
        repo_root=REPO_ROOT,
        policy_path=None,
    )

    trace = output["trace"]
    assert trace["started_at"]
    assert trace["finished_at"]
    assert output["result"]["modified_files"] == ["sample_repo/parser.py"]
    patch_diff = Path(output["run_paths"]["patch_diff_path"]).read_text(encoding="utf-8")
    assert "diff --git a/sample_repo/parser.py b/sample_repo/parser.py" in patch_diff
    assert "+    if not items:" in patch_diff

    run_test_steps = [step for step in trace["steps"] if step["tool_name"] == "run_tests"]
    assert len(run_test_steps) == 2
    for step in run_test_steps:
        assert "resolve_repo_path_duration_sec" in step["tool_metrics"]
        assert "env_setup_duration_sec" in step["tool_metrics"]
        assert "pre_execution_duration_sec" in step["tool_metrics"]
        assert "command_execution_duration_sec" in step["tool_metrics"]
        assert "subprocess_duration_sec" in step["tool_metrics"]
        assert "summary_extraction_duration_sec" in step["tool_metrics"]
        assert step["duration_sec"] is not None

    workspace_steps = [step for step in trace["steps"] if step["tool_name"] == "copy_workspace"]
    assert len(workspace_steps) == 1
    assert workspace_steps[0]["action_type"] == "workspace_prep"
    assert workspace_steps[0]["duration_sec"] is not None

    patch_steps = [step for step in trace["steps"] if step["tool_name"] == "rule_based_patch"]
    assert len(patch_steps) == 1
    assert "patch_applied" in patch_steps[0]["tool_metrics"]


def test_run_observation_task_passes_policy_pytest_flags(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "policy_id": "test_policy",
                "description": "test",
                "patch_strategy": "baseline",
                "pytest_additional_flags": ["-p no:unraisableexception"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    observed_flags: list[list[str]] = []
    original_run_tests = run_tests

    def wrapped_run_tests(repo_path: str, command: str, timeout_sec: int = 120, additional_pytest_flags: list[str] | None = None) -> dict:
        observed_flags.append(additional_pytest_flags or [])
        return original_run_tests(
            repo_path,
            command,
            timeout_sec=timeout_sec,
            additional_pytest_flags=additional_pytest_flags,
        )

    with patch("app.runtime.task_runner.run_tests", side_effect=wrapped_run_tests):
        output = run_observation_task(
            task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
            repo_root=REPO_ROOT,
            policy_path=policy_path,
        )

    assert observed_flags == [["-p no:unraisableexception"], ["-p no:unraisableexception"]]
    run_test_steps = [step for step in output["trace"]["steps"] if step["tool_name"] == "run_tests"]
    assert run_test_steps[0]["tool_input"]["additional_pytest_flags"] == ["-p no:unraisableexception"]
    assert output["result"]["tool_stats"]["policy_id"] == "test_policy"
