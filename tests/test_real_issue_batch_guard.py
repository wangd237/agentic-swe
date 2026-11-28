import json

import pytest

from app.runtime import batch_runner


def test_frozen_real_issue_cannot_use_legacy_batch(tmp_path, monkeypatch):
    task = {
        "task_id": "real_full_sample_1", "repo_name": "sample", "repo_path": "sample",
        "issue_title": "sample", "issue_text": "sample", "test_command": "true",
        "success_criteria": "sample", "difficulty": "easy", "tags": [],
        "source_type": "real_issue",
    }
    path = tmp_path / "task.json"
    path.write_text(json.dumps(task), encoding="utf-8")
    monkeypatch.setattr(batch_runner, "run_agent", lambda **kwargs: pytest.fail("legacy Agent invoked"))
    with pytest.raises(RuntimeError, match="independent Evaluator"):
        batch_runner.run_batch(tmp_path, [path])
