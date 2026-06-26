"""Deterministic verifier layer for repair-agent results."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


VerificationLevel = Literal[
    "none",
    "local_smoke_success",
    "targeted_success",
    "full_verification_success",
    "official_resolved",
    "weak_verification_success",
]
RiskLevel = Literal["low", "medium", "high"]
EvidenceQuality = Literal["strong", "partial", "weak", "missing"]
AcceptedFinalStatus = Literal[
    "accepted_success",
    "local_smoke_success",
    "targeted_only_success",
    "weak_verification_success",
    "not_accepted",
]


class VerifierReport(BaseModel):
    """Structured verification judgment for a completed repair run."""

    model_config = ConfigDict(extra="forbid")

    verification_level: VerificationLevel
    risk_level: RiskLevel
    evidence_quality: EvidenceQuality = "missing"
    missing_evidence: list[str] = Field(default_factory=list)
    accepted: bool
    caveats: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class VerificationEvidence(BaseModel):
    """Machine-readable evidence used by the verifier judgment."""

    model_config = ConfigDict(extra="forbid")

    patch_applied: bool
    modified_files: list[str] = Field(default_factory=list)
    verification_scope: str
    pre_test: dict[str, Any] = Field(default_factory=dict)
    post_test: dict[str, Any] = Field(default_factory=dict)
    official_harness: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def build_verification_evidence(
    *,
    patch_applied: bool,
    modified_files: list[str],
    verification_strength: str,
    test_command: str,
    pre_test_exit_code: int | None,
    post_test_exit_code: int | None,
    pre_test_summary: str = "",
    post_test_summary: str = "",
    observed_failure: str = "",
    source_type: str = "",
    task_metadata: dict[str, Any] | None = None,
) -> VerificationEvidence:
    """Build a compact evidence contract for the verifier decision."""

    metadata = task_metadata or {}
    official_resolved = bool(metadata.get("official_resolved"))
    official_required = source_type == "swe_bench_lite" or bool(
        metadata.get("official_harness_required") or metadata.get("swebench_instance_id")
    )

    return VerificationEvidence(
        patch_applied=patch_applied,
        modified_files=modified_files,
        verification_scope=verification_strength,
        pre_test={
            "command": test_command,
            "exit_code": pre_test_exit_code,
            "summary": pre_test_summary,
            "observed_failure": observed_failure,
        },
        post_test={
            "command": test_command,
            "exit_code": post_test_exit_code,
            "summary": post_test_summary,
        },
        official_harness={
            "required": official_required,
            "resolved": official_resolved,
            "source_type": source_type,
            "instance_id": metadata.get("swebench_instance_id", ""),
        },
    )


def assess_evidence_quality(
    evidence: VerificationEvidence,
) -> tuple[EvidenceQuality, list[str]]:
    """Classify whether verification evidence is strong enough to trust."""

    missing: list[str] = []
    has_patch = evidence.patch_applied and bool(evidence.modified_files)
    pre_exit_code = evidence.pre_test.get("exit_code")
    post_exit_code = evidence.post_test.get("exit_code")
    scope = evidence.verification_scope
    official_required = bool(evidence.official_harness.get("required"))
    official_resolved = bool(evidence.official_harness.get("resolved"))

    if not has_patch:
        missing.append("patch")
    if pre_exit_code is None:
        missing.append("pre_test")
    elif pre_exit_code == 0:
        missing.append("pre_test_failure")
    if post_exit_code is None:
        missing.append("post_test")
    elif post_exit_code != 0:
        missing.append("post_test_success")
    if scope != "full":
        missing.append("full_verification")
    if official_required and not official_resolved:
        missing.append("official_harness")

    if not has_patch or post_exit_code is None:
        return "missing", missing
    if post_exit_code != 0:
        return "weak", missing
    if scope == "weak":
        return "weak", missing
    if scope == "targeted":
        return "partial", missing
    if official_required and not official_resolved:
        return "partial", missing
    if pre_exit_code not in {None, 0} and scope == "full":
        return "strong", missing
    return "partial", missing


def build_verifier_report(
    *,
    final_status: str,
    verification_strength: str,
    patch_applied: bool,
    modified_files: list[str],
    pre_test_exit_code: int | None,
    post_test_exit_code: int | None,
    source_type: str = "",
    task_metadata: dict[str, Any] | None = None,
    verification_evidence: VerificationEvidence | None = None,
) -> VerifierReport:
    """Map raw run outcomes to a product-facing verification judgment."""

    metadata = task_metadata or {}
    caveats: list[str] = []
    recommendations: list[str] = []
    is_swebench_lite = source_type == "swe_bench_lite" or bool(metadata.get("swebench_instance_id"))
    official_resolved = bool(metadata.get("official_resolved"))
    evidence_quality: EvidenceQuality = "missing"
    missing_evidence: list[str] = []
    if verification_evidence is not None:
        evidence_quality, missing_evidence = assess_evidence_quality(verification_evidence)

    if official_resolved and final_status == "success":
        return VerifierReport(
            verification_level="official_resolved",
            risk_level="low",
            evidence_quality=evidence_quality,
            missing_evidence=missing_evidence,
            accepted=True,
            caveats=[],
            recommendations=[],
        )

    if not patch_applied:
        return VerifierReport(
            verification_level="none",
            risk_level="high",
            evidence_quality=evidence_quality,
            missing_evidence=missing_evidence or ["patch"],
            accepted=False,
            caveats=["No patch was applied."],
            recommendations=["Generate a patch before reporting a repair result."],
        )

    if final_status == "success" and verification_strength == "full" and post_test_exit_code == 0:
        verification_level: VerificationLevel = "full_verification_success"
        risk_level: RiskLevel = "low"
        accepted = True
    elif final_status == "success_weak_verification":
        verification_level = "weak_verification_success"
        risk_level = "high"
        accepted = False
        caveats.append("Only weak or static verification is available.")
        recommendations.append("Run a concrete failing test or full test command before accepting the patch.")
    elif verification_strength == "targeted" and post_test_exit_code == 0:
        verification_level = "targeted_success"
        risk_level = "medium"
        accepted = False
        caveats.append("Only targeted verification passed; full verification did not run or was not confirmed.")
        recommendations.append("Run the full test command before accepting the patch.")
    else:
        verification_level = "none"
        risk_level = "high"
        accepted = False
        caveats.append("The repair did not reach a trusted verification state.")
        recommendations.append("Inspect trace, patch, and test output before accepting the result.")

    if is_swebench_lite and verification_level == "full_verification_success":
        verification_level = "local_smoke_success"
        risk_level = "medium"
        accepted = False
        caveats.append("SWE-bench Lite local smoke success is not the same as official resolved.")
        caveats.append("Official SWE-bench Docker harness was not run.")
        if metadata.get("official_harness_required", True):
            recommendations.append("Evaluate the exported prediction JSONL with the official SWE-bench harness.")

    if pre_test_exit_code not in {1, None} and post_test_exit_code == 0:
        caveats.append("Pre-test did not clearly fail before patching; reproduction evidence may be weak.")

    if missing_evidence:
        caveats.append("Verification evidence is incomplete: " + ", ".join(missing_evidence) + ".")
    if evidence_quality == "weak":
        risk_level = "high"
    elif evidence_quality == "partial" and risk_level == "low":
        risk_level = "medium"

    if len(modified_files) > 1:
        risk_level = "medium" if risk_level == "low" else risk_level
        caveats.append(f"Patch modified {len(modified_files)} files; review scope carefully.")

    return VerifierReport(
        verification_level=verification_level,
        risk_level=risk_level,
        evidence_quality=evidence_quality,
        missing_evidence=missing_evidence,
        accepted=accepted,
        caveats=caveats,
        recommendations=recommendations,
    )


def accepted_final_status_from_report(report: VerifierReport) -> AcceptedFinalStatus:
    """Convert verifier judgment into the product-facing final status."""

    if report.accepted and report.verification_level in {
        "full_verification_success",
        "official_resolved",
    }:
        return "accepted_success"
    if report.verification_level == "local_smoke_success":
        return "local_smoke_success"
    if report.verification_level == "targeted_success":
        return "targeted_only_success"
    if report.verification_level == "weak_verification_success":
        return "weak_verification_success"
    return "not_accepted"
