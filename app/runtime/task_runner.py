"""任务运行入口与观察型 Agent 最小闭环。"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from app.agent.patcher import apply_rule_based_patch
from app.agent.policy import load_policy_config
from app.agent.planner import create_initial_plan, derive_search_queries
from app.runtime.harness import build_run_paths, next_run_id
from app.runtime.logger import write_json, write_text
from app.schemas.result_schema import Result
from app.schemas.task_schema import Task, load_task
from app.schemas.trace_schema import Trace, TraceStep
from app.tools.list_files import list_files
from app.tools.read_file import read_file
from app.tools.run_tests import run_tests
from app.tools.search_code import search_code
from app.tools.show_diff import show_diff


COPY_IGNORE_DIR_NAMES = {
    ".pytest_cache",
    "__pycache__",
}


def load_and_validate_task(task_path: str | Path) -> Task:
    # 任务加载和校验是所有 phase 的共同入口。
    return load_task(task_path)


def _utc_timestamp() -> str:
    # 统一 trace 时间格式，便于后续批量分析。
    return datetime.now(UTC).isoformat()


def _copy_repo_to_workspace(source_repo_path: Path, workspace_path: Path) -> None:
    # 复制 benchmark repo 时显式忽略缓存目录，避免测试运行污染原始基准输入。
    shutil.copytree(
        source_repo_path,
        workspace_path,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(*COPY_IGNORE_DIR_NAMES),
    )


def _append_tool_step(
    trace: Trace,
    tool_name: str,
    tool_input: dict,
    tool_output_summary: str,
    observation: str,
    decision: str,
) -> None:
    # 工具调用步骤统一从这里写入，保证 trace 结构稳定。
    trace.steps.append(
        TraceStep(
            step_index=len(trace.steps) + 1,
            action_type="tool_call",
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output_summary=tool_output_summary,
            observation=observation,
            decision=decision,
            timestamp=_utc_timestamp(),
        )
    )
    trace.total_tool_calls += 1


def _select_files_to_read(task: Task, search_results: list[dict]) -> list[str]:
    # 优先读任务 hint，其次读搜索命中文件，控制第一轮上下文范围。
    selected_files: list[str] = []
    seen: set[str] = set()

    for relative_path in task.target_files_hint:
        normalized_path = relative_path.replace("\\", "/")
        if normalized_path not in seen:
            seen.add(normalized_path)
            selected_files.append(normalized_path)

    for result in search_results:
        for relative_path in result["data"].get("match_files", []):
            normalized_path = relative_path.replace("\\", "/")
            if normalized_path in seen:
                continue
            seen.add(normalized_path)
            selected_files.append(normalized_path)
            if len(selected_files) >= 4:
                return selected_files

    return selected_files[:4]


def _build_summary(
    task: Task,
    policy_id: str,
    selected_files: list[str],
    search_queries: list[str],
    run_id: str,
    pre_test_result: dict,
    patch_result: dict,
    post_test_result: dict,
    diff_result: dict,
) -> str:
    # summary.md 需要自然语言说明当前 patch 阶段到底发现了什么、改了什么、结果如何。
    files_block = "\n".join(f"- `{file_path}`" for file_path in selected_files) or "- 暂未定位到候选文件"
    queries_block = "\n".join(f"- `{query}`" for query in search_queries) or "- 未生成搜索词"
    plan_block = "\n".join(f"- {item}" for item in create_initial_plan(task))
    observed_failure = pre_test_result["data"].get("observed_failure") or "未提取到明确失败位置"
    changed_files = diff_result["data"].get("changed_files", []) if diff_result["ok"] else []
    changed_files_block = "\n".join(f"- `{file_path}`" for file_path in changed_files) or "- 未产生代码改动"
    return f"""# Patch Run Summary

## Run

- task_id: `{task.task_id}`
- run_id: `{run_id}`
- phase: `Phase 3`
- policy_id: `{policy_id}`

## Task Understanding

- issue_title: `{task.issue_title}`
- issue_text: {task.issue_text}
- success_criteria: {task.success_criteria}

## Initial Plan

{plan_block}

## Search Queries

{queries_block}

## Recommended Files To Read Next

{files_block}

## Pre-Test Observation

- test_command: `{task.test_command}`
- test_exit_code: `{pre_test_result["data"].get("exit_code")}`
- test_summary: {pre_test_result["summary"]}
- observed_failure: {observed_failure}

## Patch Application

- patch_applied: `{patch_result["ok"]}`
- patch_summary: {patch_result["summary"]}
- patch_reason: {patch_result.get("patch_reason") or "未生成 patch 原因说明"}

## Modified Files

{changed_files_block}

## Post-Test Observation

- test_exit_code: `{post_test_result["data"].get("exit_code")}`
- test_summary: {post_test_result["summary"]}

## Conclusion

当前 patch 闭环已完成修复前测试、最小 patch 生成、代码写入、diff 记录和修复后测试。
若 post-test 已通过，则该任务已达到当前阶段的成功标准。
"""


def run_observation_task(task_path: str | Path, repo_root: str | Path, policy_path: str | Path | None = None) -> dict:
    # 这是当前单任务最小闭环：观察仓库、执行测试、生成 patch、回归验证并保存结果。
    started_at = perf_counter()
    repository_root = Path(repo_root).resolve()
    task = load_and_validate_task(task_path)
    policy_config = load_policy_config(policy_path)
    source_repo_path = (repository_root / task.repo_path).resolve()

    if not source_repo_path.exists():
        raise FileNotFoundError(f"任务 repo 不存在: {source_repo_path}")

    task_runs_dir = repository_root / "logs" / "trajectories" / task.task_id
    run_id = next_run_id(task_runs_dir)
    run_paths = build_run_paths(repository_root / "logs" / "trajectories", task.task_id, run_id)
    run_paths.run_dir.mkdir(parents=True, exist_ok=True)

    _copy_repo_to_workspace(source_repo_path, run_paths.workspace_dir)

    trace = Trace(task_id=task.task_id, run_id=run_id)
    write_json(run_paths.task_json_path, task)
    list_result = list_files(str(run_paths.workspace_dir))
    _append_tool_step(
        trace=trace,
        tool_name="list_files",
        tool_input={"repo_path": str(run_paths.workspace_dir), "recursive": True},
        tool_output_summary=list_result["summary"],
        observation=f"仓库中当前可见 {list_result['data'].get('count', 0)} 个文件。",
        decision="结合 issue 关键词筛选更可能相关的代码与测试文件。",
    )

    search_queries = derive_search_queries(task)
    search_results: list[dict] = []
    for query in search_queries:
        search_result = search_code(str(run_paths.workspace_dir), query)
        search_results.append(search_result)
        _append_tool_step(
            trace=trace,
            tool_name="search_code",
            tool_input={"repo_path": str(run_paths.workspace_dir), "query": query},
            tool_output_summary=search_result["summary"],
            observation=f"搜索词 `{query}` 关联文件: {', '.join(search_result['data'].get('match_files', [])) or '无命中'}。",
            decision="保留命中文件，用于决定接下来需要读取的上下文。",
        )

    files_to_read = _select_files_to_read(task, search_results)
    for relative_path in files_to_read:
        read_result = read_file(str(run_paths.workspace_dir), relative_path)
        _append_tool_step(
            trace=trace,
            tool_name="read_file",
            tool_input={"repo_path": str(run_paths.workspace_dir), "relative_path": relative_path},
            tool_output_summary=read_result["summary"],
            observation=f"已读取 `{relative_path}`，截断状态: {read_result['data'].get('truncated', False)}。",
            decision="继续汇总关键文件与可能的修复入口。",
        )
        if read_result["ok"]:
            trace.read_files.append(relative_path)

    pre_test_result = run_tests(str(run_paths.workspace_dir), task.test_command, timeout_sec=30)
    _append_tool_step(
        trace=trace,
        tool_name="run_tests",
        tool_input={
            "repo_path": str(run_paths.workspace_dir),
            "command": task.test_command,
            "timeout_sec": 30,
        },
        tool_output_summary=pre_test_result["summary"],
        observation=f"测试退出码: {pre_test_result['data'].get('exit_code')}，失败位置: {pre_test_result['data'].get('observed_failure') or '未提取'}。",
        decision="将测试失败位置纳入 patch 生成的重点上下文。",
    )

    write_text(run_paths.pre_test_stdout_path, pre_test_result["data"].get("stdout", ""))
    write_text(run_paths.pre_test_stderr_path, pre_test_result["data"].get("stderr", ""))

    patch_result = apply_rule_based_patch(
        task,
        str(run_paths.workspace_dir),
        files_to_read,
        policy_config=policy_config,
    )
    trace.steps.append(
        TraceStep(
            step_index=len(trace.steps) + 1,
            action_type="patch_apply",
            tool_name="rule_based_patch",
            tool_input={"candidate_files": files_to_read},
            tool_output_summary=patch_result["summary"],
            observation=patch_result.get("patch_reason", ""),
            decision="运行修复后测试，验证 patch 是否真正解决问题。",
            timestamp=_utc_timestamp(),
        )
    )

    if patch_result["write_result"] is not None:
        trace.total_tool_calls += 1

    post_test_result = run_tests(str(run_paths.workspace_dir), task.test_command, timeout_sec=30)
    _append_tool_step(
        trace=trace,
        tool_name="run_tests",
        tool_input={
            "repo_path": str(run_paths.workspace_dir),
            "command": task.test_command,
            "timeout_sec": 30,
        },
        tool_output_summary=post_test_result["summary"],
        observation=f"修复后测试退出码: {post_test_result['data'].get('exit_code')}。",
        decision="根据修复后测试结果决定当前任务是否成功。",
    )

    write_text(run_paths.post_test_stdout_path, post_test_result["data"].get("stdout", ""))
    write_text(run_paths.post_test_stderr_path, post_test_result["data"].get("stderr", ""))
    write_text(run_paths.test_stdout_path, post_test_result["data"].get("stdout", ""))
    write_text(run_paths.test_stderr_path, post_test_result["data"].get("stderr", ""))

    diff_result = show_diff(str(run_paths.workspace_dir), original_repo_path=str(source_repo_path))
    _append_tool_step(
        trace=trace,
        tool_name="show_diff",
        tool_input={
            "repo_path": str(run_paths.workspace_dir),
            "original_repo_path": str(source_repo_path),
        },
        tool_output_summary=diff_result["summary"],
        observation=f"检测到变更文件: {', '.join(diff_result['data'].get('changed_files', [])) or '无'}。",
        decision="将差异内容落盘，作为 patch 证据。",
    )
    write_text(run_paths.patch_diff_path, diff_result["data"].get("diff_text", ""))

    final_status = "success" if post_test_result["ok"] else "failed"
    trace.final_status = final_status
    duration_sec = round(perf_counter() - started_at, 4)
    summary_text = _build_summary(
        task,
        policy_config.policy_id,
        files_to_read,
        search_queries,
        run_id,
        pre_test_result,
        patch_result,
        post_test_result,
        diff_result,
    )
    result = Result(
        task_id=task.task_id,
        run_id=run_id,
        final_status=final_status,
        summary="单任务 patch 闭环已完成修复前测试、patch 应用与修复后验证。",
        test_command=task.test_command,
        test_exit_code=post_test_result["data"].get("exit_code"),
        pre_test_exit_code=pre_test_result["data"].get("exit_code"),
        post_test_exit_code=post_test_result["data"].get("exit_code"),
        pre_test_summary=pre_test_result["summary"],
        post_test_summary=post_test_result["summary"],
        test_summary=post_test_result["summary"],
        observed_failure=pre_test_result["data"].get("observed_failure", ""),
        patch_applied=patch_result["ok"],
        patch_summary=patch_result["summary"],
        modified_files=diff_result["data"].get("changed_files", []),
        duration_sec=duration_sec,
        tool_stats={
            "total_tool_calls": trace.total_tool_calls,
            "search_queries": search_queries,
            "read_file_count": len(trace.read_files),
            "policy_id": policy_config.policy_id,
        },
        recommended_files=files_to_read,
    )

    write_json(run_paths.trace_json_path, trace)
    write_json(run_paths.result_json_path, result)
    write_text(run_paths.summary_md_path, summary_text)

    return {
        "task": task.to_dict(),
        "trace": trace.to_dict(),
        "result": result.to_dict(),
        "run_paths": run_paths.to_dict(),
        "summary_text": summary_text,
    }
