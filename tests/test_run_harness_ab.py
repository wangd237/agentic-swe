"""Tests for the paired Harness experiment orchestration."""
import json
from pathlib import Path

from app.runtime.logger import write_json
from scripts import run_harness_ab as ab


def test_pair_summary_keeps_infrastructure_errors_separate():
    def row(mode, accepted):
        return {"harness_mode": mode, "outcome": "accepted" if accepted else "not_accepted",
                "llm_model": "model", "llm_provider": "provider",
                "total_tokens": 20, "missing_usage_count": 0, "duration_sec": 1}
    pairs = [
        {"task_id": "a", "strict": row("strict", False), "weak": row("weak", True)},
        {"task_id": "b", "strict": row("strict", True), "weak": row("weak", True)},
        {"task_id": "c", "strict": {"error": "TimeoutError"}, "weak": row("weak", True)},
    ]
    result = ab.summarize_pairs(pairs)
    assert result["complete_pairs"] == 2
    assert result["excluded_or_incomplete_pairs"] == 1
    assert result["matrix"]["weak_only"] == 1
    assert result["arms"]["strict"]["accepted_rate"] == 0.5
    assert result["discordant_task_ids"] == ["a"]


def test_local_smoke_is_not_official_resolution():
    assert ab.classify_result({"accepted_final_status": "local_smoke_success"}) == "not_accepted"


def test_experiment_frozen_memory_and_independent_outputs(tmp_path, monkeypatch):
    (tmp_path / "repo").mkdir()
    paths = []
    for task_id in ("a", "b"):
        path = tmp_path / f"{task_id}.json"
        write_json(path, {
            "task_id": task_id, "repo_name": "repo", "repo_path": "repo",
            "issue_title": "issue", "issue_text": "text", "test_command": "pytest",
            "success_criteria": "pass", "difficulty": "easy", "tags": [],
        })
        paths.append(path)
    policy_path = tmp_path / "policy.json"
    write_json(policy_path, {"policy_id": "base", "description": "base", "agent_type": "llm"})
    seed = tmp_path / "seed.jsonl"
    seed.write_bytes(b"frozen")
    order = []
    def fake_batch(*, repo_root, task_paths, policy_path, run_label, summary_dir):
        policy = json.loads(policy_path.read_text())
        root = Path(policy["run_log_root"])
        memory = root / "agent_memory/strategy_memory.jsonl"
        assert memory.read_bytes() == b"frozen"
        memory.write_bytes(b"changed")
        assert summary_dir == root / "summaries"
        order.append(run_label)
        result_path = root / "result.json"
        write_json(result_path, {
            "accepted_final_status": "accepted_success",
            "tool_stats": {"harness_mode": run_label, "llm_model": "model", "llm_provider": "provider"},
        })
        return {"batch_summary": {"tasks": [{"result_path": str(result_path), "trace_path": str(root / "trace.json")}]}}
    monkeypatch.setattr(ab, "run_batch", fake_batch)
    output = tmp_path / "experiment"
    result = ab.run_experiment(repo_root=tmp_path, task_paths=paths, policy_path=policy_path,
                               output_dir=output, memory_seed=seed)
    assert result["complete_pairs"] == 2
    assert order == ["strict", "weak", "weak", "strict"]
    assert seed.read_bytes() == b"frozen"
    assert len(list(output.glob("pair_*/*/result.json"))) == 4
