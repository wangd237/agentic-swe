from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import rebuild_pytest_policy_pair_calibrated_views


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_calibrated_view_summary_chains_existing_aggregators(tmp_path: Path, monkeypatch) -> None:
    phase_compare = tmp_path / "phase_compare.json"
    importtime_compare = tmp_path / "importtime_compare.json"
    matrix_summary = tmp_path / "matrix_summary.json"
    write_json(phase_compare, {"kind": "pytest_phases"})
    write_json(importtime_compare, {"kind": "pytest_importtime"})
    write_json(matrix_summary, {"matrix_label": "triage"})

    def fake_analyze_cohort(**kwargs: object) -> dict:
        cohort_label = str(kwargs["cohort_label"])
        kind = "pytest_phases" if "phase" in cohort_label else "pytest_importtime"
        runtime_equivalent_task_count = 4 if kind == "pytest_phases" else 3
        summary = {
            "kind": kind,
            "cohort_label": cohort_label,
            "runtime_equivalent_task_count": runtime_equivalent_task_count,
        }
        summary_path = tmp_path / f"{cohort_label}.json"
        write_json(summary_path, summary)
        return {
            "analysis_id": cohort_label,
            "summary_json_path": str(summary_path),
            "summary_md_path": str(summary_path.with_suffix(".md")),
            "summary": summary,
        }

    def fake_analyze_matrix_set(**kwargs: object) -> dict:
        set_label = str(kwargs["set_label"])
        summary = {
            "set_label": set_label,
            "aggregate": {
                "runtime_equivalent_matrix_count": 3,
            },
        }
        summary_path = tmp_path / f"{set_label}.json"
        write_json(summary_path, summary)
        return {
            "analysis_id": set_label,
            "summary_json_path": str(summary_path),
            "summary_md_path": str(summary_path.with_suffix(".md")),
            "summary": summary,
        }

    monkeypatch.setattr(
        rebuild_pytest_policy_pair_calibrated_views,
        "analyze_pytest_policy_pair_cohort",
        fake_analyze_cohort,
    )
    monkeypatch.setattr(
        rebuild_pytest_policy_pair_calibrated_views,
        "analyze_pytest_policy_pair_matrix_set",
        fake_analyze_matrix_set,
    )

    summary = rebuild_pytest_policy_pair_calibrated_views.build_calibrated_view_summary(
        phase_compare_paths=[phase_compare],
        importtime_compare_paths=[importtime_compare],
        matrix_summary_paths=[matrix_summary],
        view_label="v68_v69_hotspots",
        output_dir=tmp_path,
    )

    assert summary["view_label"] == "v68_v69_hotspots"
    assert summary["phase_output"]["summary"]["runtime_equivalent_task_count"] == 4
    assert summary["importtime_output"]["summary"]["runtime_equivalent_task_count"] == 3
    assert summary["matrix_output"]["summary"]["aggregate"]["runtime_equivalent_matrix_count"] == 3


def test_rebuild_calibrated_views_writes_index_files(tmp_path: Path, monkeypatch) -> None:
    def fake_build(**_: object) -> dict:
        return {
            "created_at": "2026-06-13T12:00:00+00:00",
            "view_label": "v68_v69_hotspots",
            "phase_compare_count": 4,
            "importtime_compare_count": 4,
            "matrix_summary_count": 3,
            "phase_compare_paths": [],
            "importtime_compare_paths": [],
            "matrix_summary_paths": [],
            "phase_output": {
                "summary_json_path": str(tmp_path / "phase.json"),
                "summary_md_path": str(tmp_path / "phase.md"),
                "summary": {"runtime_equivalent_task_count": 4},
            },
            "importtime_output": {
                "summary_json_path": str(tmp_path / "importtime.json"),
                "summary_md_path": str(tmp_path / "importtime.md"),
                "summary": {"runtime_equivalent_task_count": 4},
            },
            "matrix_output": {
                "summary_json_path": str(tmp_path / "matrix.json"),
                "summary_md_path": str(tmp_path / "matrix.md"),
                "summary": {"aggregate": {"runtime_equivalent_matrix_count": 3}},
            },
        }

    monkeypatch.setattr(
        rebuild_pytest_policy_pair_calibrated_views,
        "build_calibrated_view_summary",
        fake_build,
    )

    output = rebuild_pytest_policy_pair_calibrated_views.rebuild_pytest_policy_pair_calibrated_views(
        phase_compare_paths=[tmp_path / "phase_compare.json"],
        importtime_compare_paths=[tmp_path / "importtime_compare.json"],
        matrix_summary_paths=[tmp_path / "matrix_summary.json"],
        view_label="v68_v69_hotspots",
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["analysis_id"] == "pytest_policy_pair_calibrated_view_v68_v69_hotspots_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
