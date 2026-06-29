"""Run a tiny local Ollama repair smoke for the current CPU-only environment."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_env_file() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _run_tests(*, cwd: Path, command: str, timeout_sec: int) -> dict[str, Any]:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    return {
        "command": command,
        "exit_code": completed.returncode,
        "duration_sec": round(time.perf_counter() - started, 4),
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def _extract_json_object(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    start = 0
    while True:
        brace_index = text.find("{", start)
        if brace_index < 0:
            return None
        try:
            value, end_index = decoder.raw_decode(text[brace_index:])
        except json.JSONDecodeError:
            start = brace_index + 1
            continue
        if isinstance(value, dict):
            return value
        start = brace_index + max(end_index, 1)


def _ollama_chat(
    *,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    timeout_sec: int,
) -> dict[str, Any]:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.URLError as error:
        return {
            "ok": False,
            "duration_sec": round(time.perf_counter() - started, 4),
            "error": str(error),
        }
    data = json.loads(raw)
    return {
        "ok": True,
        "duration_sec": round(time.perf_counter() - started, 4),
        "response": data,
    }


def _response_text_and_usage(llm_result: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if not llm_result.get("ok"):
        return "", {}
    response = llm_result["response"]
    return (
        str(response["choices"][0]["message"].get("content", "")),
        response.get("usage") or {},
    )


def _candidate_files(task: dict[str, Any]) -> list[str]:
    hints = [str(path).replace("\\", "/") for path in task.get("target_files_hint", [])]
    implementation_hints = [
        path for path in hints
        if not path.startswith("tests/") and "/tests/" not in path
    ]
    return implementation_hints or hints


def _read_hint_files(workspace: Path, task: dict[str, Any], *, max_chars_per_file: int) -> dict[str, str]:
    files: dict[str, str] = {}
    for relative_path in task.get("target_files_hint", []):
        normalized = str(relative_path).replace("\\", "/")
        path = workspace / normalized
        if path.exists() and path.is_file():
            files[normalized] = path.read_text(encoding="utf-8")[:max_chars_per_file]
    return files


def _build_prompt(
    *,
    task: dict[str, Any],
    file_texts: dict[str, str],
    candidate_files: list[str],
) -> list[dict[str, str]]:
    system = (
        "You are a patch generator. Return only one JSON object. "
        "No markdown, no explanation. The JSON schema is: "
        '{"relative_path":"...","old_string":"...","new_string":"..."}. '
        "Escape quotes inside JSON strings with backslashes."
    )
    files_block = "\n\n".join(
        f"File {relative_path}:\n{text}"
        for relative_path, text in file_texts.items()
    )
    user = (
        f"Issue: {task['issue_title']}\n\n"
        f"Details: {task['issue_text']}\n\n"
        f"Success: {task['success_criteria']}\n\n"
        f"Candidate implementation files: {', '.join(candidate_files)}\n\n"
        f"{files_block}\n\n"
        "Produce the smallest exact string replacement needed to pass the test. "
        "Choose relative_path only from the candidate implementation files."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _build_retry_message(
    *,
    assistant_text: str,
    patch_payload: dict[str, Any] | None,
    apply_result: dict[str, Any],
) -> dict[str, str]:
    return {
        "role": "user",
        "content": (
            "The previous patch was not usable.\n"
            f"assistant_text:\n{assistant_text}\n\n"
            f"parsed_patch:\n{json.dumps(patch_payload, ensure_ascii=False)}\n\n"
            f"apply_result:\n{json.dumps(apply_result, ensure_ascii=False)}\n\n"
            "Return exactly one valid JSON object with properly escaped strings. "
            "The old_string must be an exact substring from the target file. "
            "The new_string must fully fix the failing test."
        ),
    }


def _apply_patch_json(workspace: Path, patch_payload: dict[str, Any], *, allowed_paths: list[str]) -> dict[str, Any]:
    relative_path = str(patch_payload.get("relative_path", "")).replace("\\", "/")
    old_string = patch_payload.get("old_string")
    new_string = patch_payload.get("new_string")
    if relative_path not in allowed_paths or not isinstance(old_string, str) or not isinstance(new_string, str):
        return {
            "ok": False,
            "reason": "invalid_patch_schema",
            "relative_path": relative_path,
            "allowed_paths": allowed_paths,
        }
    target = workspace / relative_path
    content = target.read_text(encoding="utf-8")
    if old_string not in content:
        return {
            "ok": False,
            "reason": "old_string_not_found",
            "relative_path": relative_path,
            "old_string": old_string,
        }
    target.write_text(content.replace(old_string, new_string, 1), encoding="utf-8")
    return {
        "ok": True,
        "relative_path": relative_path,
        "old_string": old_string,
        "new_string": new_string,
    }


def _diff_summary(*, before_texts: dict[str, str], after_texts: dict[str, str]) -> dict[str, Any]:
    parts: list[str] = []
    changed_files: list[str] = []
    for relative_path, before_text in before_texts.items():
        after_text = after_texts.get(relative_path, "")
        if before_text == after_text:
            continue
        changed_files.append(relative_path)
        parts.append(
            "".join(
                unified_diff(
                    before_text.splitlines(keepends=True),
                    after_text.splitlines(keepends=True),
                    fromfile=f"a/{relative_path}",
                    tofile=f"b/{relative_path}",
                )
            )
        )
    diff = "".join(parts)
    return {
        "diff": diff,
        "diff_chars": len(diff),
        "changed_files": changed_files,
    }


def run_smoke(
    task_path: Path,
    *,
    max_tokens: int,
    llm_timeout_sec: int,
    test_timeout_sec: int,
    max_chars_per_file: int,
) -> dict[str, Any]:
    _load_env_file()
    task = _read_json(task_path)
    source_repo = (REPO_ROOT / task["repo_path"]).resolve()
    smoke_id = "ollama_minimal_smoke_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = REPO_ROOT / "logs" / "local_smoke" / smoke_id
    workspace = run_dir / "workspace"
    shutil.copytree(source_repo, workspace)

    base_url = os.environ.get("DEEPSEEK_BASE_URL", "http://127.0.0.1:11434/v1").strip()
    model = os.environ.get("DEEPSEEK_MODEL", "qwen2.5-coder:7b-instruct-q4_k_m").strip()
    candidate_files = _candidate_files(task)
    file_texts = _read_hint_files(workspace, task, max_chars_per_file=max_chars_per_file)
    before_candidate_texts = {
        relative_path: (workspace / relative_path).read_text(encoding="utf-8")
        for relative_path in candidate_files
        if (workspace / relative_path).exists()
    }
    messages = _build_prompt(
        task=task,
        file_texts=file_texts,
        candidate_files=candidate_files,
    )

    total_started = time.perf_counter()
    pre_test = _run_tests(cwd=workspace, command=task["test_command"], timeout_sec=test_timeout_sec)
    llm_results: list[dict[str, Any]] = []
    llm_result = _ollama_chat(
        base_url=base_url,
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        timeout_sec=llm_timeout_sec,
    )
    llm_results.append(llm_result)
    assistant_text, usage = _response_text_and_usage(llm_result)
    patch_payload = _extract_json_object(assistant_text) if assistant_text else None
    apply_result = _apply_patch_json(workspace, patch_payload or {}, allowed_paths=candidate_files)
    if not apply_result.get("ok"):
        retry_messages = [
            *messages,
            {"role": "assistant", "content": assistant_text},
            _build_retry_message(
                assistant_text=assistant_text,
                patch_payload=patch_payload,
                apply_result=apply_result,
            ),
        ]
        retry_result = _ollama_chat(
            base_url=base_url,
            model=model,
            messages=retry_messages,
            max_tokens=max_tokens,
            timeout_sec=llm_timeout_sec,
        )
        llm_results.append(retry_result)
        retry_text, retry_usage = _response_text_and_usage(retry_result)
        if retry_text:
            assistant_text = retry_text
            call_usages = [
                (item.get("response") or {}).get("usage", {})
                for item in llm_results
            ]
            usage = {
                "prompt_tokens": sum(int(item.get("prompt_tokens") or 0) for item in call_usages),
                "completion_tokens": sum(int(item.get("completion_tokens") or 0) for item in call_usages),
                "total_tokens": sum(int(item.get("total_tokens") or 0) for item in call_usages),
                "last_call": retry_usage,
            }
            patch_payload = _extract_json_object(assistant_text)
            apply_result = _apply_patch_json(workspace, patch_payload or {}, allowed_paths=candidate_files)
    post_test = None
    after_candidate_texts = {
        relative_path: (workspace / relative_path).read_text(encoding="utf-8")
        for relative_path in before_candidate_texts
    }
    diff = _diff_summary(
        before_texts=before_candidate_texts,
        after_texts=after_candidate_texts,
    )
    if apply_result.get("ok"):
        post_test = _run_tests(cwd=workspace, command=task["test_command"], timeout_sec=test_timeout_sec)

    accepted = bool(
        pre_test["exit_code"] != 0
        and apply_result.get("ok")
        and post_test
        and post_test["exit_code"] == 0
    )
    result = {
        "smoke_id": smoke_id,
        "task_id": task["task_id"],
        "repo_name": task["repo_name"],
        "model": model,
        "base_url": re.sub(r"//.*@", "//***@", base_url),
        "max_tokens": max_tokens,
        "llm_timeout_sec": llm_timeout_sec,
        "test_timeout_sec": test_timeout_sec,
        "max_chars_per_file": max_chars_per_file,
        "candidate_files": candidate_files,
        "hint_files_read": list(file_texts),
        "duration_sec": round(time.perf_counter() - total_started, 4),
        "pre_test": pre_test,
        "llm": {
            "ok": llm_result.get("ok", False),
            "duration_sec": round(sum(float(item.get("duration_sec") or 0) for item in llm_results), 4),
            "call_count": len(llm_results),
            "usage": usage,
            "assistant_text": assistant_text,
            "error": llm_result.get("error"),
            "calls": [
                {
                    "ok": item.get("ok", False),
                    "duration_sec": item.get("duration_sec"),
                    "usage": (item.get("response") or {}).get("usage", {}),
                    "error": item.get("error"),
                }
                for item in llm_results
            ],
        },
        "patch_payload": patch_payload,
        "apply_result": apply_result,
        "post_test": post_test,
        "diff": diff,
        "accepted": accepted,
        "paths": {
            "run_dir": str(run_dir),
            "workspace": str(workspace),
            "result_json": str(run_dir / "result.json"),
            "summary_md": str(run_dir / "summary.md"),
        },
    }
    _write_json(run_dir / "result.json", result)
    _write_text(
        run_dir / "summary.md",
        "\n".join(
            [
                "# Ollama Minimal Smoke",
                "",
                f"- smoke_id: `{smoke_id}`",
                f"- task_id: `{task['task_id']}`",
                f"- model: `{model}`",
                f"- accepted: `{accepted}`",
                f"- duration_sec: `{result['duration_sec']}`",
                f"- pre_test_exit_code: `{pre_test['exit_code']}`",
                f"- llm_duration_sec: `{llm_result.get('duration_sec')}`",
                f"- llm_call_count: `{len(llm_results)}`",
                f"- llm_total_tokens: `{usage.get('total_tokens')}`",
                f"- apply_ok: `{apply_result.get('ok')}`",
                f"- post_test_exit_code: `{post_test['exit_code'] if post_test else None}`",
                f"- diff_chars: `{diff['diff_chars']}`",
            ]
        )
        + "\n",
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a tiny local Ollama repair smoke.")
    parser.add_argument("--task", default="benchmarks/tasks/task_006.json")
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--llm-timeout-sec", type=int, default=240)
    parser.add_argument("--test-timeout-sec", type=int, default=60)
    parser.add_argument("--max-chars-per-file", type=int, default=5000)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_smoke(
        REPO_ROOT / args.task,
        max_tokens=args.max_tokens,
        llm_timeout_sec=args.llm_timeout_sec,
        test_timeout_sec=args.test_timeout_sec,
        max_chars_per_file=args.max_chars_per_file,
    )
    print("=== Ollama Minimal Smoke ===")
    print(f"smoke_id: {result['smoke_id']}")
    print(f"task_id: {result['task_id']}")
    print(f"accepted: {result['accepted']}")
    print(f"duration_sec: {result['duration_sec']}")
    print(f"pre_test_exit_code: {result['pre_test']['exit_code']}")
    print(f"llm_duration_sec: {result['llm']['duration_sec']}")
    print(f"llm_total_tokens: {result['llm']['usage'].get('total_tokens')}")
    print(f"apply_ok: {result['apply_result'].get('ok')}")
    print(f"post_test_exit_code: {result['post_test']['exit_code'] if result['post_test'] else None}")
    print(f"result_json: {result['paths']['result_json']}")
    print(f"summary_md: {result['paths']['summary_md']}")
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
