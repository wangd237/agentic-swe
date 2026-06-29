from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import run_code_intelligence_ab


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_graph_policy_preserves_baseline_and_enables_backend() -> None:
    baseline = {
        "policy_id": "llm_demo",
        "description": "demo",
        "agent_type": "llm",
        "llm_model": "fake-model",
    }

    graph_policy = run_code_intelligence_ab.build_graph_policy(
        baseline_policy=baseline,
        graph_policy_id="llm_demo_graph",
        codebase_memory_binary="codebase-memory-mcp.exe",
        timeout_sec=12,
        max_results=4,
        index_mode="fast",
    )

    assert graph_policy["policy_id"] == "llm_demo_graph"
    assert graph_policy["agent_type"] == "llm"
    assert graph_policy["llm_model"] == "fake-model"
    assert graph_policy["code_intelligence_backend"] == "codebase_memory_cli"
    assert graph_policy["codebase_memory_binary"] == "codebase-memory-mcp.exe"
    assert graph_policy["codebase_memory_always_shadow_copy"] is True
    assert graph_policy["code_intelligence_timeout_sec"] == 12
    assert graph_policy["code_intelligence_max_results"] == 4
    assert graph_policy["codebase_memory_index_mode"] == "fast"


def test_run_code_intelligence_ab_dry_run_writes_plan_and_graph_policy(tmp_path: Path) -> None:
    repo_root = tmp_path
    tasks_dir = repo_root / "benchmarks" / "tasks"
    manifest_path = repo_root / "benchmarks" / "manifests" / "dev_tasks.json"
    baseline_policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"
    task_path = tasks_dir / "task_001.json"
    output_dir = repo_root / "logs" / "summaries"

    write_json(
        task_path,
        {
            "task_id": "task_001",
            "repo_name": "demo",
            "repo_path": "benchmarks/repos/demo",
            "issue_title": "demo",
            "issue_text": "DemoIssue fails",
            "test_command": "python -m pytest",
            "success_criteria": "pass",
            "difficulty": "easy",
            "tags": [],
            "target_files_hint": ["demo/app.py", "tests/test_app.py"],
        },
    )
    write_json(
        manifest_path,
        {
            "manifest_id": "dev",
            "tasks": ["benchmarks/tasks/task_001.json"],
        },
    )
    write_json(
        baseline_policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "llm_model": "fake-model",
        },
    )

    output = run_code_intelligence_ab.run_code_intelligence_ab(
        manifest=manifest_path,
        tasks_dir=tasks_dir,
        baseline_policy_path=baseline_policy_path,
        cohort_label="dry",
        codebase_memory_binary="codebase-memory-mcp.exe",
        timeout_sec=12,
        max_results=4,
        index_mode="fast",
        dry_run=True,
        output_dir=output_dir,
    )

    summary = output["summary"]
    graph_policy_path = Path(summary["graph_policy_path"])
    targets_json_path = Path(summary["targets_json_path"])
    graph_policy = json.loads(graph_policy_path.read_text(encoding="utf-8"))
    targets = json.loads(targets_json_path.read_text(encoding="utf-8"))
    assert output["eval_id"] == "code_intelligence_ab_dry_001"
    assert summary["dry_run"] is True
    assert summary["preflight_only"] is False
    assert summary["task_count"] == 1
    assert summary["target_files_by_task"] == {
        "task_001": ["demo/app.py", "tests/test_app.py"]
    }
    assert summary["targets_json_path"] == str(targets_json_path)
    assert targets == {"task_001": ["demo/app.py", "tests/test_app.py"]}
    assert summary["outputs"] == {}
    assert summary["preflight"]["ready_for_real_ab"] is False
    assert "missing_llm_api_key:LLM_API_KEY" in summary["preflight"]["blockers"]
    assert "missing_external_llm_data_consent" in summary["preflight"]["blockers"]
    assert "codebase_memory_binary_unavailable" in summary["preflight"]["blockers"]
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
    assert graph_policy["code_intelligence_backend"] == "codebase_memory_cli"
    assert graph_policy["codebase_memory_binary"] == "codebase-memory-mcp.exe"
    assert graph_policy["codebase_memory_always_shadow_copy"] is True


def test_run_code_intelligence_ab_preflight_loads_env_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tasks_dir = tmp_path / "benchmarks" / "tasks"
    manifest_path = tmp_path / "benchmarks" / "manifests" / "dev_tasks.json"
    baseline_policy_path = tmp_path / "optimization" / "policy_versions" / "llm_demo.json"
    task_path = tasks_dir / "task_001.json"
    binary = tmp_path / "codebase-memory-mcp.exe"
    binary.write_text("", encoding="utf-8")
    (tmp_path / ".env").write_text("DEMO_API_KEY=from-env-file\n", encoding="utf-8")
    monkeypatch.delenv("DEMO_API_KEY", raising=False)
    monkeypatch.setattr(run_code_intelligence_ab, "REPO_ROOT", tmp_path)

    write_json(
        task_path,
        {
            "task_id": "task_001",
            "repo_name": "demo",
            "repo_path": "benchmarks/repos/demo",
            "issue_title": "demo",
            "issue_text": "DemoIssue fails",
            "test_command": "python -m pytest",
            "success_criteria": "pass",
            "difficulty": "easy",
            "tags": [],
            "target_files_hint": ["demo/app.py"],
        },
    )
    write_json(manifest_path, {"manifest_id": "dev", "tasks": ["benchmarks/tasks/task_001.json"]})
    write_json(
        baseline_policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "llm_model": "fake-model",
            "llm_api_key_env": "DEMO_API_KEY",
            "llm_base_url": "https://example.test",
        },
    )

    def fake_run(args, capture_output, text, encoding, errors, timeout, check):
        return subprocess.CompletedProcess(args, 0, stdout="codebase-memory-mcp 0.8.1\n", stderr="")

    monkeypatch.setattr(run_code_intelligence_ab.subprocess, "run", fake_run)

    output = run_code_intelligence_ab.run_code_intelligence_ab(
        manifest=manifest_path,
        tasks_dir=tasks_dir,
        baseline_policy_path=baseline_policy_path,
        cohort_label="envfile",
        codebase_memory_binary=str(binary),
        preflight_only=True,
        confirm_external_llm_data=True,
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["summary"]["preflight"]["ready_for_real_ab"] is True
    assert output["summary"]["preflight"]["llm"]["api_key_present"] is True
    assert output["summary"]["preflight"]["llm"]["external_data_consent"] is True


def test_build_preflight_report_ready_when_env_and_binary_exist(
    tmp_path: Path,
    monkeypatch,
) -> None:
    binary = tmp_path / "codebase-memory-mcp.exe"
    binary.write_text("", encoding="utf-8")
    task_path = tmp_path / "task_001.json"
    write_json(
        task_path,
        {
            "task_id": "task_001",
            "repo_name": "demo",
            "repo_path": "benchmarks/repos/demo",
            "issue_title": "demo",
            "issue_text": "DemoIssue fails",
            "test_command": "python -m pytest",
            "success_criteria": "pass",
            "difficulty": "easy",
            "tags": [],
            "target_files_hint": ["demo/app.py"],
        },
    )

    monkeypatch.setenv("DEMO_API_KEY", "secret")

    def fake_run(args, capture_output, text, encoding, errors, timeout, check):
        return subprocess.CompletedProcess(args, 0, stdout="codebase-memory-mcp 0.8.1\n", stderr="")

    monkeypatch.setattr(run_code_intelligence_ab.subprocess, "run", fake_run)

    report = run_code_intelligence_ab.build_preflight_report(
        baseline_policy={
            "llm_provider": "openai_compatible",
            "llm_model": "demo-model",
            "llm_api_key_env": "DEMO_API_KEY",
            "llm_base_url": "https://example.test",
        },
        graph_policy={"codebase_memory_index_mode": "fast", "codebase_memory_always_shadow_copy": True},
        codebase_memory_binary=str(binary),
        task_paths=[task_path],
        target_files_by_task={"task_001": ["demo/app.py"]},
        external_llm_data_consent=True,
        minimum_task_count=1,
    )

    assert report["ready_for_real_ab"] is True
    assert report["blockers"] == []
    assert report["llm"]["api_key_present"] is True
    assert report["llm"]["external_data_consent"] is True
    assert report["codebase_memory"]["binary_available"] is True
    assert report["codebase_memory"]["version"] == "codebase-memory-mcp 0.8.1"
    assert report["tasks"]["with_target_files"] == 1


def test_build_preflight_report_blocks_without_external_llm_data_consent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    binary = tmp_path / "codebase-memory-mcp.exe"
    binary.write_text("", encoding="utf-8")
    task_path = tmp_path / "task_001.json"
    write_json(
        task_path,
        {
            "task_id": "task_001",
            "repo_name": "demo",
            "repo_path": "benchmarks/repos/demo",
            "issue_title": "demo",
            "issue_text": "DemoIssue fails",
            "test_command": "python -m pytest",
            "success_criteria": "pass",
            "difficulty": "easy",
            "tags": [],
            "target_files_hint": ["demo/app.py"],
        },
    )

    monkeypatch.setenv("DEMO_API_KEY", "secret")

    def fake_run(args, capture_output, text, encoding, errors, timeout, check):
        return subprocess.CompletedProcess(args, 0, stdout="codebase-memory-mcp 0.8.1\n", stderr="")

    monkeypatch.setattr(run_code_intelligence_ab.subprocess, "run", fake_run)

    report = run_code_intelligence_ab.build_preflight_report(
        baseline_policy={
            "llm_provider": "openai_compatible",
            "llm_model": "demo-model",
            "llm_api_key_env": "DEMO_API_KEY",
            "llm_base_url": "https://example.test",
        },
        graph_policy={"codebase_memory_index_mode": "fast", "codebase_memory_always_shadow_copy": True},
        codebase_memory_binary=str(binary),
        task_paths=[task_path],
        target_files_by_task={"task_001": ["demo/app.py"]},
        minimum_task_count=1,
    )

    assert report["ready_for_real_ab"] is False
    assert report["blockers"] == ["missing_external_llm_data_consent"]
    assert report["llm"]["api_key_present"] is True
    assert report["llm"]["external_data_consent"] is False
    assert report["codebase_memory"]["binary_available"] is True


def test_build_external_data_preview_uses_metadata_not_full_issue_text(tmp_path: Path) -> None:
    task_path = tmp_path / "task_001.json"
    write_json(
        task_path,
        {
            "task_id": "task_001",
            "repo_name": "demo",
            "repo_path": "benchmarks/repos/demo",
            "issue_title": "Sensitive bug",
            "issue_text": "SECRET_TOKEN should never appear in the preview payload.",
            "test_command": "python -m pytest",
            "success_criteria": "pass when SECRET_TOKEN is handled",
            "difficulty": "easy",
            "tags": ["preview"],
            "target_files_hint": ["demo/app.py"],
            "metadata": {"source_url": "https://example.test/issue/1"},
        },
    )

    preview = run_code_intelligence_ab.build_external_data_preview(
        baseline_policy={"llm_provider": "openai_compatible", "llm_model": "demo-model"},
        graph_policy={"code_intelligence_backend": "codebase_memory_cli"},
        task_paths=[task_path],
        target_files_by_task={"task_001": ["demo/app.py"]},
    )

    serialized = json.dumps(preview, ensure_ascii=False)
    assert preview["contains_full_issue_text"] is False
    assert preview["contains_code_snippets"] is False
    assert preview["task_count"] == 1
    assert preview["total_issue_text_chars"] == len("SECRET_TOKEN should never appear in the preview payload.")
    assert preview["tasks"][0]["issue_title"] == "Sensitive bug"
    assert preview["tasks"][0]["issue_text_char_count"] == len(
        "SECRET_TOKEN should never appear in the preview payload."
    )
    assert preview["tasks"][0]["metadata_keys"] == ["source_url"]
    assert "SECRET_TOKEN should never appear" not in serialized
    assert "pass when SECRET_TOKEN is handled" not in serialized


def test_run_code_intelligence_ab_aborts_real_run_on_preflight_blocker(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tasks_dir = tmp_path / "benchmarks" / "tasks"
    manifest_path = tmp_path / "benchmarks" / "manifests" / "dev_tasks.json"
    baseline_policy_path = tmp_path / "optimization" / "policy_versions" / "llm_demo.json"
    task_path = tasks_dir / "task_001.json"
    write_json(
        task_path,
        {
            "task_id": "task_001",
            "repo_name": "demo",
            "repo_path": "benchmarks/repos/demo",
            "issue_title": "demo",
            "issue_text": "DemoIssue fails",
            "test_command": "python -m pytest",
            "success_criteria": "pass",
            "difficulty": "easy",
            "tags": [],
            "target_files_hint": ["demo/app.py"],
        },
    )
    write_json(manifest_path, {"manifest_id": "dev", "tasks": ["benchmarks/tasks/task_001.json"]})
    write_json(
        baseline_policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "llm_model": "fake-model",
        },
    )

    def fail_run_batch(**kwargs):  # noqa: ANN003
        raise AssertionError("run_batch should not be called when preflight blocks")

    monkeypatch.setattr(run_code_intelligence_ab, "run_batch", fail_run_batch)

    output = run_code_intelligence_ab.run_code_intelligence_ab(
        manifest=manifest_path,
        tasks_dir=tasks_dir,
        baseline_policy_path=baseline_policy_path,
        cohort_label="blocked",
        codebase_memory_binary="missing-codebase-memory",
        output_dir=tmp_path / "logs" / "summaries",
    )

    summary = output["summary"]
    assert summary["dry_run"] is False
    assert summary["preflight_only"] is False
    assert summary["aborted_by_preflight"] is True
    assert summary["outputs"]["aborted_reason"] == "preflight_blockers"
    assert "missing_llm_api_key:LLM_API_KEY" in summary["outputs"]["blockers"]


def test_run_code_intelligence_ab_external_data_preview_only_writes_preview_without_batch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tasks_dir = tmp_path / "benchmarks" / "tasks"
    manifest_path = tmp_path / "benchmarks" / "manifests" / "dev_tasks.json"
    baseline_policy_path = tmp_path / "optimization" / "policy_versions" / "llm_demo.json"
    task_path = tasks_dir / "task_001.json"
    write_json(
        task_path,
        {
            "task_id": "task_001",
            "repo_name": "demo",
            "repo_path": "benchmarks/repos/demo",
            "issue_title": "demo",
            "issue_text": "DemoIssue fails with private details",
            "test_command": "python -m pytest",
            "success_criteria": "pass",
            "difficulty": "easy",
            "tags": [],
            "target_files_hint": ["demo/app.py"],
        },
    )
    write_json(manifest_path, {"manifest_id": "dev", "tasks": ["benchmarks/tasks/task_001.json"]})
    write_json(
        baseline_policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "llm_model": "fake-model",
        },
    )

    def fail_run_batch(**kwargs):  # noqa: ANN003
        raise AssertionError("run_batch should not be called for preview-only")

    monkeypatch.setattr(run_code_intelligence_ab, "run_batch", fail_run_batch)

    output = run_code_intelligence_ab.run_code_intelligence_ab(
        manifest=manifest_path,
        tasks_dir=tasks_dir,
        baseline_policy_path=baseline_policy_path,
        cohort_label="preview",
        codebase_memory_binary="missing-codebase-memory",
        external_data_preview_only=True,
        output_dir=tmp_path / "logs" / "summaries",
    )

    summary = output["summary"]
    preview_path = Path(summary["external_data_preview_path"])
    targets_json_path = Path(summary["targets_json_path"])
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    targets = json.loads(targets_json_path.read_text(encoding="utf-8"))
    assert summary["external_data_preview_only"] is True
    assert summary["aborted_by_preflight"] is False
    assert summary["outputs"] == {}
    assert preview_path.exists()
    assert summary["external_data_preview"]["task_count"] == 1
    assert summary["external_data_preview"]["contains_full_issue_text"] is False
    assert targets == {"task_001": ["demo/app.py"]}
    assert preview["tasks"][0]["issue_text_char_count"] == len("DemoIssue fails with private details")
    assert "DemoIssue fails with private details" not in preview_path.read_text(encoding="utf-8")


def test_run_code_intelligence_ab_can_ignore_preflight_blockers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tasks_dir = tmp_path / "benchmarks" / "tasks"
    manifest_path = tmp_path / "benchmarks" / "manifests" / "dev_tasks.json"
    baseline_policy_path = tmp_path / "optimization" / "policy_versions" / "llm_demo.json"
    task_path = tasks_dir / "task_001.json"
    write_json(
        task_path,
        {
            "task_id": "task_001",
            "repo_name": "demo",
            "repo_path": "benchmarks/repos/demo",
            "issue_title": "demo",
            "issue_text": "DemoIssue fails",
            "test_command": "python -m pytest",
            "success_criteria": "pass",
            "difficulty": "easy",
            "tags": [],
            "target_files_hint": ["demo/app.py"],
        },
    )
    write_json(manifest_path, {"manifest_id": "dev", "tasks": ["benchmarks/tasks/task_001.json"]})
    write_json(
        baseline_policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "llm_model": "fake-model",
            "llm_api_key_env": "DEMO_API_KEY",
            "llm_base_url": "https://example.test",
        },
    )
    monkeypatch.setenv("DEMO_API_KEY", "secret")
    calls: list[str] = []

    def fake_run_batch(*, run_label, **kwargs):  # noqa: ANN003
        calls.append(run_label)
        return {
            "summary_json_path": f"{run_label}.json",
            "batch_summary": {"tasks": []},
        }

    monkeypatch.setattr(run_code_intelligence_ab, "run_batch", fake_run_batch)
    monkeypatch.setattr(
        run_code_intelligence_ab,
        "summarize_code_intelligence_runs",
        lambda **kwargs: {
            "summary_json_path": "ab.json",
            "summary_md_path": "ab.md",
            "summary": {
                "ab_aggregate": {"pair_count": 0},
                "v16_acceptance": {"ready_to_judge": False, "accepted": False},
            },
        },
    )

    output = run_code_intelligence_ab.run_code_intelligence_ab(
        manifest=manifest_path,
        tasks_dir=tasks_dir,
        baseline_policy_path=baseline_policy_path,
        cohort_label="ignored",
        codebase_memory_binary="missing-codebase-memory",
        ignore_preflight_blockers=True,
        confirm_external_llm_data=True,
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["summary"]["aborted_by_preflight"] is False
    assert output["summary"]["preflight"]["blockers"] == ["codebase_memory_binary_unavailable"]
    assert calls == ["ignored_baseline", "ignored_graph"]
    assert output["summary"]["outputs"]["ab_summary_json"] == "ab.json"
    assert output["summary"]["ab_aggregate"] == {"pair_count": 0}
    assert output["summary"]["v16_acceptance"] == {"ready_to_judge": False, "accepted": False}


def test_run_code_intelligence_ab_cannot_ignore_missing_external_llm_data_consent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tasks_dir = tmp_path / "benchmarks" / "tasks"
    manifest_path = tmp_path / "benchmarks" / "manifests" / "dev_tasks.json"
    baseline_policy_path = tmp_path / "optimization" / "policy_versions" / "llm_demo.json"
    task_path = tasks_dir / "task_001.json"
    binary = tmp_path / "codebase-memory-mcp.exe"
    binary.write_text("", encoding="utf-8")
    write_json(
        task_path,
        {
            "task_id": "task_001",
            "repo_name": "demo",
            "repo_path": "benchmarks/repos/demo",
            "issue_title": "demo",
            "issue_text": "DemoIssue fails",
            "test_command": "python -m pytest",
            "success_criteria": "pass",
            "difficulty": "easy",
            "tags": [],
            "target_files_hint": ["demo/app.py"],
        },
    )
    write_json(manifest_path, {"manifest_id": "dev", "tasks": ["benchmarks/tasks/task_001.json"]})
    write_json(
        baseline_policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "llm_model": "fake-model",
            "llm_api_key_env": "DEMO_API_KEY",
            "llm_base_url": "https://example.test",
        },
    )
    monkeypatch.setenv("DEMO_API_KEY", "secret")

    def fake_version(args, capture_output, text, encoding, errors, timeout, check):
        return subprocess.CompletedProcess(args, 0, stdout="codebase-memory-mcp 0.8.1\n", stderr="")

    def fail_run_batch(**kwargs):  # noqa: ANN003
        raise AssertionError("run_batch should not run without external LLM data consent")

    monkeypatch.setattr(run_code_intelligence_ab.subprocess, "run", fake_version)
    monkeypatch.setattr(run_code_intelligence_ab, "run_batch", fail_run_batch)

    output = run_code_intelligence_ab.run_code_intelligence_ab(
        manifest=manifest_path,
        tasks_dir=tasks_dir,
        baseline_policy_path=baseline_policy_path,
        cohort_label="consent_required",
        codebase_memory_binary=str(binary),
        ignore_preflight_blockers=True,
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["summary"]["aborted_by_preflight"] is True
    assert output["summary"]["outputs"]["blockers"] == ["missing_external_llm_data_consent"]


def test_run_code_intelligence_ab_can_ignore_technical_blockers_with_consent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tasks_dir = tmp_path / "benchmarks" / "tasks"
    manifest_path = tmp_path / "benchmarks" / "manifests" / "dev_tasks.json"
    baseline_policy_path = tmp_path / "optimization" / "policy_versions" / "llm_demo.json"
    task_path = tasks_dir / "task_001.json"
    write_json(
        task_path,
        {
            "task_id": "task_001",
            "repo_name": "demo",
            "repo_path": "benchmarks/repos/demo",
            "issue_title": "demo",
            "issue_text": "DemoIssue fails",
            "test_command": "python -m pytest",
            "success_criteria": "pass",
            "difficulty": "easy",
            "tags": [],
            "target_files_hint": ["demo/app.py"],
        },
    )
    write_json(manifest_path, {"manifest_id": "dev", "tasks": ["benchmarks/tasks/task_001.json"]})
    write_json(
        baseline_policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "llm_model": "fake-model",
            "llm_api_key_env": "DEMO_API_KEY",
            "llm_base_url": "https://example.test",
        },
    )
    monkeypatch.setenv("DEMO_API_KEY", "secret")
    calls: list[str] = []

    def fake_run_batch(*, run_label, **kwargs):  # noqa: ANN003
        calls.append(run_label)
        return {
            "summary_json_path": f"{run_label}.json",
            "batch_summary": {"tasks": []},
        }

    monkeypatch.setattr(run_code_intelligence_ab, "run_batch", fake_run_batch)
    monkeypatch.setattr(
        run_code_intelligence_ab,
        "summarize_code_intelligence_runs",
        lambda **kwargs: {"summary_json_path": "ab.json", "summary_md_path": "ab.md"},
    )

    output = run_code_intelligence_ab.run_code_intelligence_ab(
        manifest=manifest_path,
        tasks_dir=tasks_dir,
        baseline_policy_path=baseline_policy_path,
        cohort_label="technical_override",
        codebase_memory_binary="missing-codebase-memory",
        ignore_preflight_blockers=True,
        confirm_external_llm_data=True,
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["summary"]["aborted_by_preflight"] is False
    assert output["summary"]["preflight"]["blockers"] == ["codebase_memory_binary_unavailable"]
    assert calls == ["technical_override_baseline", "technical_override_graph"]


def test_main_returns_nonzero_when_preflight_aborts(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_code_intelligence_ab.py",
            "--baseline-policy",
            "policy.json",
        ],
    )
    monkeypatch.setattr(
        run_code_intelligence_ab,
        "run_code_intelligence_ab",
        lambda **kwargs: {
            "eval_id": "eval_001",
            "summary_json_path": "summary.json",
            "summary_md_path": "summary.md",
            "summary": {
                "dry_run": False,
                "preflight_only": False,
                "external_data_preview_only": False,
                "aborted_by_preflight": True,
                "task_count": 1,
                "preflight": {
                    "ready_for_real_ab": False,
                    "blockers": ["missing_llm_api_key:LLM_API_KEY"],
                    "warnings": [],
                },
                "graph_policy_path": "graph_policy.json",
                "targets_json_path": "targets.json",
                "external_data_preview_path": "preview.json",
            },
        },
    )

    assert run_code_intelligence_ab.main() == 2


def test_main_returns_zero_for_preflight_only_not_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_code_intelligence_ab.py",
            "--baseline-policy",
            "policy.json",
            "--preflight-only",
        ],
    )
    monkeypatch.setattr(
        run_code_intelligence_ab,
        "run_code_intelligence_ab",
        lambda **kwargs: {
            "eval_id": "eval_001",
            "summary_json_path": "summary.json",
            "summary_md_path": "summary.md",
            "summary": {
                "dry_run": False,
                "preflight_only": True,
                "external_data_preview_only": False,
                "aborted_by_preflight": False,
                "task_count": 1,
                "preflight": {
                    "ready_for_real_ab": False,
                    "blockers": ["missing_llm_api_key:LLM_API_KEY"],
                    "warnings": [],
                },
                "graph_policy_path": "graph_policy.json",
                "targets_json_path": "targets.json",
                "external_data_preview_path": "preview.json",
            },
        },
    )

    assert run_code_intelligence_ab.main() == 0


def test_main_returns_zero_for_preflight_only_with_require_v16_acceptance(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_code_intelligence_ab.py",
            "--baseline-policy",
            "policy.json",
            "--preflight-only",
            "--require-v16-acceptance",
        ],
    )
    monkeypatch.setattr(
        run_code_intelligence_ab,
        "run_code_intelligence_ab",
        lambda **kwargs: {
            "eval_id": "eval_001",
            "summary_json_path": "summary.json",
            "summary_md_path": "summary.md",
            "summary": {
                "dry_run": False,
                "preflight_only": True,
                "external_data_preview_only": False,
                "require_v16_acceptance": True,
                "aborted_by_preflight": False,
                "task_count": 1,
                "preflight": {
                    "ready_for_real_ab": False,
                    "blockers": ["missing_external_llm_data_consent"],
                    "warnings": [],
                },
                "graph_policy_path": "graph_policy.json",
                "targets_json_path": "targets.json",
                "external_data_preview_path": "preview.json",
                "v16_acceptance": {},
            },
        },
    )

    assert run_code_intelligence_ab.main() == 0


def test_main_passes_external_data_preview_only(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_code_intelligence_ab.py",
            "--baseline-policy",
            "policy.json",
            "--external-data-preview-only",
        ],
    )

    def fake_run_code_intelligence_ab(**kwargs):  # noqa: ANN003
        captured.update(kwargs)
        return {
            "eval_id": "eval_001",
            "summary_json_path": "summary.json",
            "summary_md_path": "summary.md",
            "summary": {
                "dry_run": False,
                "preflight_only": False,
                "external_data_preview_only": True,
                "aborted_by_preflight": False,
                "task_count": 1,
                "preflight": {
                    "ready_for_real_ab": False,
                    "blockers": ["missing_external_llm_data_consent"],
                    "warnings": [],
                },
                "graph_policy_path": "graph_policy.json",
                "targets_json_path": "targets.json",
                "external_data_preview_path": "preview.json",
            },
        }

    monkeypatch.setattr(run_code_intelligence_ab, "run_code_intelligence_ab", fake_run_code_intelligence_ab)

    assert run_code_intelligence_ab.main() == 0
    assert captured["external_data_preview_only"] is True


def test_main_passes_require_v16_acceptance_and_returns_3_when_not_accepted(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_code_intelligence_ab.py",
            "--baseline-policy",
            "policy.json",
            "--require-v16-acceptance",
        ],
    )

    def fake_run_code_intelligence_ab(**kwargs):  # noqa: ANN003
        captured.update(kwargs)
        return {
            "eval_id": "eval_001",
            "summary_json_path": "summary.json",
            "summary_md_path": "summary.md",
            "summary": {
                "dry_run": False,
                "preflight_only": False,
                "external_data_preview_only": False,
                "require_v16_acceptance": True,
                "aborted_by_preflight": False,
                "task_count": 8,
                "preflight": {
                    "ready_for_real_ab": True,
                    "blockers": [],
                    "warnings": [],
                },
                "graph_policy_path": "graph_policy.json",
                "targets_json_path": "targets.json",
                "external_data_preview_path": "preview.json",
                "v16_acceptance": {
                    "ready_to_judge": True,
                    "accepted": False,
                    "failed_check_ids": ["graph_hint_used_at_least_once"],
                },
            },
        }

    monkeypatch.setattr(run_code_intelligence_ab, "run_code_intelligence_ab", fake_run_code_intelligence_ab)

    assert run_code_intelligence_ab.main() == 3
    assert captured["require_v16_acceptance"] is True


def test_main_require_v16_acceptance_returns_0_when_accepted(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_code_intelligence_ab.py",
            "--baseline-policy",
            "policy.json",
            "--require-v16-acceptance",
        ],
    )
    monkeypatch.setattr(
        run_code_intelligence_ab,
        "run_code_intelligence_ab",
        lambda **kwargs: {
            "eval_id": "eval_001",
            "summary_json_path": "summary.json",
            "summary_md_path": "summary.md",
            "summary": {
                "dry_run": False,
                "preflight_only": False,
                "external_data_preview_only": False,
                "require_v16_acceptance": True,
                "aborted_by_preflight": False,
                "task_count": 8,
                "preflight": {
                    "ready_for_real_ab": True,
                    "blockers": [],
                    "warnings": [],
                },
                "graph_policy_path": "graph_policy.json",
                "targets_json_path": "targets.json",
                "external_data_preview_path": "preview.json",
                "v16_acceptance": {
                    "ready_to_judge": True,
                    "accepted": True,
                    "failed_check_ids": [],
                },
            },
        },
    )

    assert run_code_intelligence_ab.main() == 0
