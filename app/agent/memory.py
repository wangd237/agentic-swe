"""Structured state for a single LLM agent repair run."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


PhaseName = Literal["understand", "reproduce", "localize", "patch", "verify", "final"]
VerificationStrength = Literal["none", "weak", "targeted", "full"]
ReproductionEvidenceKind = Literal["none", "test", "weak_static"]


class FailureSignature(BaseModel):
    """Compact fingerprint of the current observed test failure."""

    model_config = ConfigDict(extra="forbid")

    failed_tests: list[str] = Field(default_factory=list)
    assertion_lines: list[str] = Field(default_factory=list)
    locations: list[dict[str, Any]] = Field(default_factory=list)
    output_hash: str = ""

    @classmethod
    def from_failure_summary(cls, failure_summary: dict[str, Any]) -> "FailureSignature":
        payload = {
            "failed_tests": failure_summary.get("failed_tests", []),
            "assertion_lines": failure_summary.get("assertion_lines", []),
            "locations": failure_summary.get("locations", []),
            "short_summary": failure_summary.get("short_summary", ""),
        }
        payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return cls(
            failed_tests=list(payload["failed_tests"] or []),
            assertion_lines=list(payload["assertion_lines"] or []),
            locations=list(payload["locations"] or []),
            output_hash=hashlib.sha256(payload_text.encode("utf-8")).hexdigest()[:16],
        )


class LocalizationCandidate(BaseModel):
    """A file the agent has evidence to consider patching."""

    model_config = ConfigDict(extra="forbid")

    relative_path: str
    reason: str = ""
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class ReflectionDecision(BaseModel):
    """Structured self-correction decision after a failed repair attempt."""

    model_config = ConfigDict(extra="forbid")

    failure_delta: Literal["unchanged", "changed", "unknown"] = "unknown"
    likely_cause: Literal[
        "wrong_file",
        "wrong_hypothesis",
        "partial_fix",
        "test_env",
        "overfit",
        "low_confidence_localization",
        "unknown",
    ] = "unknown"
    next_phase: PhaseName = "localize"
    required_actions: list[str] = Field(default_factory=list)
    should_undo: bool = False


class AgentState(BaseModel):
    """Run-local memory used to enforce basic repair discipline."""

    model_config = ConfigDict(extra="forbid")

    phase: PhaseName = "understand"
    issue_summary: str = ""
    failure_signature: FailureSignature | None = None
    localization_candidates: list[LocalizationCandidate] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    modified_files: list[str] = Field(default_factory=list)
    read_files: list[str] = Field(default_factory=list)
    has_reproduction_evidence: bool = False
    reproduction_evidence_kind: ReproductionEvidenceKind = "none"
    verification_strength: VerificationStrength = "none"
    workspace_generation: int = 0
    diff_observed_generation: int | None = None

    def snapshot(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def remember_read_file(self, relative_path: str) -> None:
        normalized = relative_path.replace("\\", "/")
        if normalized and normalized not in self.read_files:
            self.read_files.append(normalized)

    def remember_candidate(self, relative_path: str, *, reason: str, evidence: str, confidence: float = 0.5) -> None:
        normalized = relative_path.replace("\\", "/")
        if not normalized:
            return
        for candidate in self.localization_candidates:
            if candidate.relative_path == normalized:
                if evidence and evidence not in candidate.evidence:
                    candidate.evidence.append(evidence)
                candidate.confidence = max(candidate.confidence, confidence)
                return
        self.localization_candidates.append(
            LocalizationCandidate(
                relative_path=normalized,
                reason=reason,
                evidence=[evidence] if evidence else [],
                confidence=confidence,
            )
        )

    def remember_modified_file(self, relative_path: str) -> None:
        normalized = relative_path.replace("\\", "/")
        if normalized and normalized not in self.modified_files:
            self.modified_files.append(normalized)

    def remember_hypothesis(self, text: str, *, max_chars: int = 500, max_items: int = 8) -> None:
        normalized = " ".join(text.strip().split())
        if not normalized:
            return
        if len(normalized) > max_chars:
            normalized = normalized[: max_chars - 3].rstrip() + "..."
        if normalized in self.hypotheses:
            return
        self.hypotheses.append(normalized)
        if len(self.hypotheses) > max_items:
            self.hypotheses = self.hypotheses[-max_items:]

    def set_localization_candidates(self, candidates: list[LocalizationCandidate]) -> None:
        self.localization_candidates = candidates

    def remember_workspace_write(self) -> None:
        self.workspace_generation += 1

    def remember_diff_observed(self) -> None:
        self.diff_observed_generation = self.workspace_generation
