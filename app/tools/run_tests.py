"""测试执行工具实现。"""

from __future__ import annotations

import os
import re
import subprocess
from time import perf_counter

from app.tools.common import resolve_repo_path


FAILED_TEST_PATTERN = re.compile(r"^FAILED\s+(.+)$", re.MULTILINE)
FAILURE_LOCATION_PATTERN = re.compile(r"^(?P<path>.+?):(?P<line>\d+): (?P<error>.+)$", re.MULTILINE)


def _summarize_test_output(stdout: str, stderr: str, exit_code: int) -> tuple[str, str]:
    # 尽量从 pytest 输出中提炼出一条“失败发生在哪里”的摘要。
    combined_output = "\n".join(part for part in [stdout, stderr] if part).strip()
    failed_test_match = FAILED_TEST_PATTERN.search(combined_output)
    failure_location_match = FAILURE_LOCATION_PATTERN.search(combined_output)

    failed_test = failed_test_match.group(1).strip() if failed_test_match else ""
    if failure_location_match:
        failure_location = (
            f"{failure_location_match.group('path')}:{failure_location_match.group('line')} "
            f"({failure_location_match.group('error')})"
        )
    else:
        failure_location = ""

    if exit_code == 0:
        return "测试命令执行成功，目标测试已通过。", ""
    if failed_test and failure_location:
        return f"测试失败：{failed_test}，失败位置 {failure_location}。", failure_location
    if failed_test:
        return f"测试失败：{failed_test}。", failed_test
    if failure_location:
        return f"测试失败，定位到 {failure_location}。", failure_location
    return "测试命令执行失败，但未能从输出中提取明确失败位置。", ""


def run_tests(repo_path: str, command: str, timeout_sec: int = 120) -> dict:
    # 通过受控子进程运行测试，并关闭 pytest 自动插件加载，减少环境噪声。
    try:
        resolved_repo_path = resolve_repo_path(repo_path)
        env = dict(os.environ)
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        started_at = perf_counter()

        completed_process = subprocess.run(
            command,
            cwd=resolved_repo_path,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=env,
        )
        subprocess_duration_sec = round(perf_counter() - started_at, 4)

        summary_started_at = perf_counter()
        test_summary, observed_failure = _summarize_test_output(
            stdout=completed_process.stdout,
            stderr=completed_process.stderr,
            exit_code=completed_process.returncode,
        )
        summary_extraction_duration_sec = round(perf_counter() - summary_started_at, 4)
        duration_sec = round(subprocess_duration_sec + summary_extraction_duration_sec, 4)

        return {
            "ok": completed_process.returncode == 0,
            "tool_name": "run_tests",
            "summary": test_summary,
            "data": {
                "repo_path": str(resolved_repo_path),
                "command": command,
                "timeout_sec": timeout_sec,
                "exit_code": completed_process.returncode,
                "stdout": completed_process.stdout,
                "stderr": completed_process.stderr,
                "duration_sec": duration_sec,
                "subprocess_duration_sec": subprocess_duration_sec,
                "summary_extraction_duration_sec": summary_extraction_duration_sec,
                "observed_failure": observed_failure,
            },
            "error": None if completed_process.returncode == 0 else {
                "type": "test_failure",
                "message": test_summary,
            },
        }
    except subprocess.TimeoutExpired as error:
        return {
            "ok": False,
            "tool_name": "run_tests",
            "summary": f"测试命令超时，超过 {timeout_sec} 秒。",
            "data": {
                "repo_path": repo_path,
                "command": command,
                "timeout_sec": timeout_sec,
                "exit_code": None,
                "stdout": error.stdout or "",
                "stderr": error.stderr or "",
                "duration_sec": timeout_sec,
                "subprocess_duration_sec": timeout_sec,
                "summary_extraction_duration_sec": 0.0,
                "observed_failure": "",
            },
            "error": {"type": "timeout", "message": str(error)},
        }
    except FileNotFoundError as error:
        return {
            "ok": False,
            "tool_name": "run_tests",
            "summary": "仓库路径不存在，无法运行测试。",
            "data": {"repo_path": repo_path, "command": command, "timeout_sec": timeout_sec},
            "error": {"type": "not_found", "message": str(error)},
        }
    except NotADirectoryError as error:
        return {
            "ok": False,
            "tool_name": "run_tests",
            "summary": "给定路径不是仓库目录。",
            "data": {"repo_path": repo_path, "command": command, "timeout_sec": timeout_sec},
            "error": {"type": "invalid_path", "message": str(error)},
        }
    except Exception as error:
        return {
            "ok": False,
            "tool_name": "run_tests",
            "summary": "运行测试时发生异常。",
            "data": {"repo_path": repo_path, "command": command, "timeout_sec": timeout_sec},
            "error": {"type": "unknown_error", "message": str(error)},
        }
