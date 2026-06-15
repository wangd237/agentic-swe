"""测试执行工具实现。"""

from __future__ import annotations

import os
import re
import subprocess
from time import perf_counter

from app.tools.common import resolve_repo_path


FAILED_TEST_PATTERN = re.compile(r"^FAILED\s+(.+)$", re.MULTILINE)
FAILURE_LOCATION_PATTERN = re.compile(r"^(?P<path>.+?):(?P<line>\d+): (?P<error>.+)$", re.MULTILINE)
ASSERTION_LINE_PATTERN = re.compile(r"^\s*(?:E\s+|>\s*)?(?P<assertion>assert .+)$", re.MULTILINE)
OUTPUT_EXCERPT_MAX_CHARS = 1200
DEFAULT_PYTEST_FLAGS = ["--tb=short", "--no-header", "--disable-warnings"]


def _build_output_excerpt(output: str, *, max_chars: int = OUTPUT_EXCERPT_MAX_CHARS) -> str:
    """保留失败输出的尾部片段，给模型补充 unittest 等难以结构化提取的细节。"""

    compact_lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    compact_output = "\n".join(compact_lines)
    if len(compact_output) <= max_chars:
        return compact_output
    return "...<truncated>\n" + compact_output[-max_chars:]


def _inject_pytest_flags(command: str, additional_flags: list[str] | None = None) -> str:
    # 仅在 pytest 命令形态下追加额外 flags，避免污染非 pytest 测试命令。
    normalized_command = command.strip()
    if "pytest" not in normalized_command:
        return command
    for flag in [*DEFAULT_PYTEST_FLAGS, *(additional_flags or [])]:
        if flag in normalized_command:
            continue
        normalized_command = f"{normalized_command} {flag}"
    return normalized_command


def _build_failure_summary(stdout: str, stderr: str, exit_code: int) -> dict:
    if exit_code == 0:
        return {
            "failed_tests": [],
            "assertion_lines": [],
            "locations": [],
            "short_summary": "",
        }

    combined_output = "\n".join(part for part in [stdout, stderr] if part).strip()
    output_excerpt = _build_output_excerpt(combined_output)
    failed_tests = [match.strip() for match in FAILED_TEST_PATTERN.findall(combined_output)]
    assertion_lines = [
        match.group("assertion").strip()
        for match in ASSERTION_LINE_PATTERN.finditer(combined_output)
    ]
    locations = [
        {
            "path": match.group("path").strip(),
            "line": int(match.group("line")),
            "error": match.group("error").strip(),
        }
        for match in FAILURE_LOCATION_PATTERN.finditer(combined_output)
    ]
    summary_parts: list[str] = []
    if assertion_lines:
        summary_parts.append("断言: " + " | ".join(assertion_lines[:3]))
    if locations:
        location_text = "; ".join(
            f"{location['path']}:{location['line']} ({location['error']})"
            for location in locations[:3]
        )
        summary_parts.append("位置: " + location_text)
    if failed_tests:
        summary_parts.append("失败测试: " + "; ".join(failed_tests[:3]))
    if not summary_parts:
        summary_parts.append("测试命令执行失败，但未提取到明确 pytest 断言。")

    short_summary = "；".join(summary_parts)
    if len(short_summary) > 500:
        short_summary = f"{short_summary[:500]}..."
    return {
        "failed_tests": failed_tests,
        "assertion_lines": assertion_lines,
        "locations": locations,
        "output_excerpt": output_excerpt,
        "short_summary": short_summary,
    }


def _summarize_test_output(stdout: str, stderr: str, exit_code: int) -> tuple[str, str, dict]:
    # 尽量从 pytest 输出中提炼出一条“失败发生在哪里”的摘要。
    failure_summary = _build_failure_summary(stdout, stderr, exit_code)
    failed_tests = failure_summary["failed_tests"]
    locations = failure_summary["locations"]

    failed_test = failed_tests[0] if failed_tests else ""
    if locations:
        first_location = locations[0]
        failure_location = (
            f"{first_location['path']}:{first_location['line']} "
            f"({first_location['error']})"
        )
    else:
        failure_location = ""

    if exit_code == 0:
        return "测试命令执行成功，目标测试已通过。", "", failure_summary
    if failed_test and failure_location:
        return f"测试失败：{failed_test}，失败位置 {failure_location}。", failure_location, failure_summary
    if failed_test:
        return f"测试失败：{failed_test}。", failed_test, failure_summary
    if failure_location:
        return f"测试失败，定位到 {failure_location}。", failure_location, failure_summary
    return "测试命令执行失败，但未能从输出中提取明确失败位置。", "", failure_summary


def run_tests(
    repo_path: str,
    command: str,
    timeout_sec: int = 120,
    additional_pytest_flags: list[str] | None = None,
) -> dict:
    # 通过受控子进程运行测试，并关闭 pytest 自动插件加载，减少环境噪声。
    try:
        tool_started_at = perf_counter()
        resolve_started_at = perf_counter()
        resolved_repo_path = resolve_repo_path(repo_path)
        resolve_repo_path_duration_sec = round(perf_counter() - resolve_started_at, 4)

        effective_command = _inject_pytest_flags(command, additional_pytest_flags)

        env_setup_started_at = perf_counter()
        env = dict(os.environ)
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env_setup_duration_sec = round(perf_counter() - env_setup_started_at, 4)

        command_started_at = perf_counter()
        completed_process = subprocess.run(
            effective_command,
            cwd=resolved_repo_path,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            env=env,
        )
        command_execution_duration_sec = round(perf_counter() - command_started_at, 4)

        summary_started_at = perf_counter()
        test_summary, observed_failure, failure_summary = _summarize_test_output(
            stdout=completed_process.stdout,
            stderr=completed_process.stderr,
            exit_code=completed_process.returncode,
        )
        summary_extraction_duration_sec = round(perf_counter() - summary_started_at, 4)
        pre_execution_duration_sec = round(resolve_repo_path_duration_sec + env_setup_duration_sec, 4)
        duration_sec = round(perf_counter() - tool_started_at, 4)

        return {
            "ok": completed_process.returncode == 0,
            "tool_name": "run_tests",
            "summary": test_summary,
            "data": {
                "repo_path": str(resolved_repo_path),
                "command": effective_command,
                "original_command": command,
                "additional_pytest_flags": additional_pytest_flags or [],
                "timeout_sec": timeout_sec,
                "exit_code": completed_process.returncode,
                "stdout": completed_process.stdout,
                "stderr": completed_process.stderr,
                "duration_sec": duration_sec,
                "resolve_repo_path_duration_sec": resolve_repo_path_duration_sec,
                "env_setup_duration_sec": env_setup_duration_sec,
                "pre_execution_duration_sec": pre_execution_duration_sec,
                "command_execution_duration_sec": command_execution_duration_sec,
                "subprocess_duration_sec": command_execution_duration_sec,
                "summary_extraction_duration_sec": summary_extraction_duration_sec,
                "observed_failure": observed_failure,
                "failure_summary": failure_summary,
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
                "command": _inject_pytest_flags(command, additional_pytest_flags),
                "original_command": command,
                "additional_pytest_flags": additional_pytest_flags or [],
                "timeout_sec": timeout_sec,
                "exit_code": None,
                "stdout": error.stdout or "",
                "stderr": error.stderr or "",
                "duration_sec": timeout_sec,
                "resolve_repo_path_duration_sec": 0.0,
                "env_setup_duration_sec": 0.0,
                "pre_execution_duration_sec": 0.0,
                "command_execution_duration_sec": timeout_sec,
                "subprocess_duration_sec": timeout_sec,
                "summary_extraction_duration_sec": 0.0,
                "observed_failure": "",
                "failure_summary": {
                    "failed_tests": [],
                    "assertion_lines": [],
                    "locations": [],
                    "short_summary": f"测试命令超时，超过 {timeout_sec} 秒。",
                },
            },
            "error": {"type": "timeout", "message": str(error)},
        }
    except FileNotFoundError as error:
        return {
            "ok": False,
            "tool_name": "run_tests",
            "summary": "仓库路径不存在，无法运行测试。",
            "data": {
                "repo_path": repo_path,
                "command": _inject_pytest_flags(command, additional_pytest_flags),
                "original_command": command,
                "additional_pytest_flags": additional_pytest_flags or [],
                "timeout_sec": timeout_sec,
            },
            "error": {"type": "not_found", "message": str(error)},
        }
    except NotADirectoryError as error:
        return {
            "ok": False,
            "tool_name": "run_tests",
            "summary": "给定路径不是仓库目录。",
            "data": {
                "repo_path": repo_path,
                "command": _inject_pytest_flags(command, additional_pytest_flags),
                "original_command": command,
                "additional_pytest_flags": additional_pytest_flags or [],
                "timeout_sec": timeout_sec,
            },
            "error": {"type": "invalid_path", "message": str(error)},
        }
    except Exception as error:
        return {
            "ok": False,
            "tool_name": "run_tests",
            "summary": "运行测试时发生异常。",
            "data": {
                "repo_path": repo_path,
                "command": _inject_pytest_flags(command, additional_pytest_flags),
                "original_command": command,
                "additional_pytest_flags": additional_pytest_flags or [],
                "timeout_sec": timeout_sec,
            },
            "error": {"type": "unknown_error", "message": str(error)},
        }
