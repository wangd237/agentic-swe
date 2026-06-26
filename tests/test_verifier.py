from __future__ import annotations

from app.agent.verifier import accepted_final_status_from_report, build_verifier_report


def test_verifier_accepts_full_verified_non_benchmark_success() -> None:
    report = build_verifier_report(
        final_status="success",
        verification_strength="full",
        patch_applied=True,
        modified_files=["pkg/app.py"],
        pre_test_exit_code=1,
        post_test_exit_code=0,
        source_type="synthetic",
        task_metadata={},
    )

    assert report.verification_level == "full_verification_success"
    assert report.risk_level == "low"
    assert report.accepted is True
    assert report.caveats == []
    assert accepted_final_status_from_report(report) == "accepted_success"


def test_verifier_marks_swebench_smoke_as_unaccepted_local_smoke() -> None:
    report = build_verifier_report(
        final_status="success",
        verification_strength="full",
        patch_applied=True,
        modified_files=["pydicom/valuerep.py"],
        pre_test_exit_code=1,
        post_test_exit_code=0,
        source_type="swe_bench_lite",
        task_metadata={
            "swebench_instance_id": "pydicom__pydicom-1139",
            "official_harness_required": True,
        },
    )

    assert report.verification_level == "local_smoke_success"
    assert report.risk_level == "medium"
    assert report.accepted is False
    assert any("official resolved" in caveat for caveat in report.caveats)
    assert report.recommendations
    assert accepted_final_status_from_report(report) == "local_smoke_success"


def test_verifier_rejects_weak_verification_success() -> None:
    report = build_verifier_report(
        final_status="success_weak_verification",
        verification_strength="weak",
        patch_applied=True,
        modified_files=["pkg/app.py"],
        pre_test_exit_code=None,
        post_test_exit_code=0,
        source_type="synthetic",
        task_metadata={},
    )

    assert report.verification_level == "weak_verification_success"
    assert report.risk_level == "high"
    assert report.accepted is False
    assert "weak" in " ".join(report.caveats).lower()
    assert accepted_final_status_from_report(report) == "weak_verification_success"


def test_verifier_maps_targeted_success_to_unaccepted_targeted_status() -> None:
    report = build_verifier_report(
        final_status="success",
        verification_strength="targeted",
        patch_applied=True,
        modified_files=["pkg/app.py"],
        pre_test_exit_code=1,
        post_test_exit_code=0,
        source_type="synthetic",
        task_metadata={},
    )

    assert report.verification_level == "targeted_success"
    assert report.accepted is False
    assert accepted_final_status_from_report(report) == "targeted_only_success"
