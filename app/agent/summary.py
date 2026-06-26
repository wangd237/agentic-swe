"""User-facing run summary helpers."""

from __future__ import annotations

from typing import Any


def format_missing_evidence(verifier_report: dict[str, Any]) -> str:
    missing = verifier_report.get("missing_evidence", [])
    if isinstance(missing, list) and missing:
        return ", ".join(str(item) for item in missing)
    return "none"


def build_verification_summary_fields(result: dict[str, Any]) -> dict[str, Any]:
    """Return compact verification fields for CLI summaries."""

    tool_stats = result.get("tool_stats", {})
    if not isinstance(tool_stats, dict):
        tool_stats = {}
    verifier_report = result.get("verifier_report", {})
    if not isinstance(verifier_report, dict):
        verifier_report = {}
    verification_evidence = result.get("verification_evidence", {})
    if not isinstance(verification_evidence, dict):
        verification_evidence = {}
    official_harness = verification_evidence.get("official_harness", {})
    if not isinstance(official_harness, dict):
        official_harness = {}

    return {
        "final_status": result.get("final_status", "unknown"),
        "accepted_final_status": result.get("accepted_final_status", "unknown"),
        "verification_strength": tool_stats.get("verification_strength", "unknown"),
        "verification_level": verifier_report.get("verification_level", "unknown"),
        "evidence_quality": verifier_report.get("evidence_quality", "unknown"),
        "missing_evidence": format_missing_evidence(verifier_report),
        "verifier_accepted": verifier_report.get("accepted", False),
        "risk_level": verifier_report.get("risk_level", "unknown"),
        "evidence_scope": verification_evidence.get("verification_scope", "unknown"),
        "evidence_official_harness_required": official_harness.get("required", False),
    }
