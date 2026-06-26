from __future__ import annotations

from pathlib import Path

from scripts import run_issue_agent


def test_run_issue_agent_prints_verification_quality_summary(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    task_path = tmp_path / "task.json"
    policy_path = tmp_path / "policy.json"
    task_path.write_text("{}", encoding="utf-8")
    policy_path.write_text("{}", encoding="utf-8")

    def fake_run_agent(**_: object) -> dict:
        return {
            "task": {"task_id": "swe_demo"},
            "result": {
                "run_id": "run_001",
                "final_status": "success",
                "accepted_final_status": "local_smoke_success",
                "verifier_report": {
                    "verification_level": "local_smoke_success",
                    "evidence_quality": "partial",
                    "missing_evidence": ["official_harness"],
                    "accepted": False,
                    "risk_level": "medium",
                },
                "verification_evidence": {
                    "verification_scope": "full",
                    "official_harness": {"required": True},
                },
                "tool_stats": {
                    "policy_id": "fake_policy",
                    "agent_type": "llm",
                    "llm_provider": "fake_provider",
                    "llm_model": "fake_model",
                    "total_tool_calls": 3,
                    "verification_strength": "full",
                },
            },
            "run_paths": {
                "trace_json_path": str(tmp_path / "trace.json"),
                "result_json_path": str(tmp_path / "result.json"),
                "summary_md_path": str(tmp_path / "summary.md"),
            },
        }

    monkeypatch.setattr(run_issue_agent, "run_agent", fake_run_agent)
    monkeypatch.setattr(
        run_issue_agent,
        "REPO_ROOT",
        tmp_path,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_issue_agent.py",
            "--task",
            str(task_path),
            "--policy",
            str(policy_path),
        ],
    )

    assert run_issue_agent.main() == 0
    captured = capsys.readouterr()

    assert "=== Issue Agent Run Summary ===" in captured.out
    assert "final_status: success" in captured.out
    assert "accepted_final_status: local_smoke_success" in captured.out
    assert "verification_level: local_smoke_success" in captured.out
    assert "evidence_quality: partial" in captured.out
    assert "missing_evidence: official_harness" in captured.out
    assert "verifier_accepted: False" in captured.out
    assert "risk_level: medium" in captured.out
    assert "evidence_official_harness_required: True" in captured.out
