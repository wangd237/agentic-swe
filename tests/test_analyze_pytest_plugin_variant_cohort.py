from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_pytest_plugin_variant_cohort


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_benchmark_summary(
    base_dir: Path,
    *,
    task_id: str,
    variant_deltas: list[dict],
) -> Path:
    summary_path = base_dir / f"{task_id}.json"
    write_json(
        summary_path,
        {
            "task_id": task_id,
            "test_command": "python -m pytest tests/test_demo.py -q",
            "repetitions": 3,
            "derived_metrics": {
                "variant_deltas": variant_deltas,
            },
        },
    )
    return summary_path


def test_build_pytest_plugin_variant_cohort_summary_aggregates_variants(tmp_path: Path) -> None:
    first = make_benchmark_summary(
        tmp_path,
        task_id="task_101",
        variant_deltas=[
            {
                "variant_name": "light_terminal_plugins",
                "wall_delta_sec": -0.03,
                "import_self_delta_us": -12000,
                "unique_module_delta": -8,
                "removed_modules": ["junitxml", "pastebin"],
            },
            {
                "variant_name": "minimal_safe_plugins",
                "wall_delta_sec": -0.05,
                "import_self_delta_us": -18000,
                "unique_module_delta": -15,
                "removed_modules": ["junitxml", "pastebin", "faulthandler"],
            },
        ],
    )
    second = make_benchmark_summary(
        tmp_path,
        task_id="task_102",
        variant_deltas=[
            {
                "variant_name": "light_terminal_plugins",
                "wall_delta_sec": -0.025,
                "import_self_delta_us": -10000,
                "unique_module_delta": -7,
                "removed_modules": ["junitxml", "pastebin"],
            },
            {
                "variant_name": "minimal_safe_plugins",
                "wall_delta_sec": -0.04,
                "import_self_delta_us": -16000,
                "unique_module_delta": -14,
                "removed_modules": ["junitxml", "pastebin", "faulthandler"],
            },
        ],
    )

    summary = analyze_pytest_plugin_variant_cohort.build_pytest_plugin_variant_cohort_summary(
        benchmark_summary_paths=[first, second],
        cohort_label="hotspots",
    )

    assert summary["task_count"] == 2
    assert summary["variant_aggregate"]["light_terminal_plugins"]["average_wall_delta_sec"] == -0.0275
    assert summary["variant_aggregate"]["minimal_safe_plugins"]["average_import_delta_us"] == -17000
    assert summary["variant_aggregate"]["minimal_safe_plugins"]["average_module_delta"] == -14
    assert summary["ranked_variants"][0]["variant_name"] == "minimal_safe_plugins"
    assert summary["variant_aggregate"]["minimal_safe_plugins"]["top_removed_modules"][0]["module"] == "junitxml"


def test_analyze_pytest_plugin_variant_cohort_writes_output_files(tmp_path: Path) -> None:
    first = make_benchmark_summary(
        tmp_path,
        task_id="task_101",
        variant_deltas=[
            {
                "variant_name": "minimal_safe_plugins",
                "wall_delta_sec": -0.05,
                "import_self_delta_us": -18000,
                "unique_module_delta": -15,
                "removed_modules": ["junitxml", "pastebin", "faulthandler"],
            },
        ],
    )

    output = analyze_pytest_plugin_variant_cohort.analyze_pytest_plugin_variant_cohort(
        benchmark_summary_paths=[first],
        cohort_label="hotspots",
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["analysis_id"] == "pytest_plugin_variants_cohort_hotspots_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
