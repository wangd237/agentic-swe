"""Observable test evidence; deliberately no repair-cause or action classification."""
from __future__ import annotations

import json
import re
from typing import Any

from app.core.state import AgentState

# Only explicit node outcomes are compared. A missing node is never a pass.
_NODE = re.compile(r"^(?P<node>\S+::\S+)\s+(?P<status>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b", re.M)
_FAILED = re.compile(r"^FAILED\s+(?P<node>\S+::\S+)", re.M)
_STARTUP = re.compile(r"Plugin already registered under a different name|ERROR collecting|errors? during collection|INTERNALERROR>|UsageError:|pytest: error:", re.I)


def record_test_evidence(state: AgentState, result: dict[str, Any], *,
                         scope: str, generation: int) -> dict[str, Any]:
    data = result.get("data") or {}
    error = result.get("error") or {}
    failure = data.get("failure_summary") or {}
    stdout, stderr = data.get("stdout") or "", data.get("stderr") or ""
    def as_text(value: Any) -> str:
        return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
    output = as_text(stdout) + "\n" + as_text(stderr)
    exit_code = data.get("exit_code")
    timed_out = error.get("type") == "timeout"
    startup = _STARTUP.search(output)
    blocked = bool(data.get("policy_blocked"))
    nodes = {m["node"]: m["status"].lower() for m in _NODE.finditer(output)}
    nodes.update({m["node"]: "failed" for m in _FAILED.finditer(output)})
    nodes.update({m["node"]: "passed" for m in re.finditer(r"^PASSED\s+(?P<node>\S+::\S+)", output, re.M)})
    nodes.update({m["node"]: "error" for m in re.finditer(r"^ERROR\s+(?P<node>\S+::\S+)", output, re.M)})
    if startup or timed_out or blocked or exit_code is None:
        comparable = False
    else:
        comparable = bool(nodes)
    command = data.get("command") or data.get("original_command")
    key = json.dumps([scope, command], ensure_ascii=False)
    previous = state.test_observations.get(key) if command else None
    delta = None
    if comparable and previous and previous["comparable"]:
        before = previous["nodes"]
        common = before.keys() & nodes.keys()
        bad = {"failed", "error"}
        delta = {
            "fixed_tests": sorted(n for n in common if before[n] in bad and nodes[n] == "passed"),
            "still_failing_tests": sorted(n for n in common if before[n] in bad and nodes[n] in bad),
            "newly_failed_tests": sorted(n for n in common if before[n] == "passed" and nodes[n] in bad),
            "previously_observed_not_reported": sorted(before.keys() - nodes.keys()),
            "comparison_basis": "explicit node outcomes only; same command and scope; test contents may differ",
            "previous_generation": previous["generation"],
        }
    if command and not blocked:
        state.test_observations[key] = {"nodes": nodes, "comparable": comparable, "generation": generation}
    evidence = {
        "command": command, "scope": scope, "workspace_generation": generation,
        "exit_code": exit_code, "timed_out": timed_out,
        "tool_error_type": error.get("type"), "policy_blocked": blocked,
        "startup_or_collection_signal": startup.group(0) if startup else None,
        "observed_node_outcomes": nodes, "test_delta": delta,
        "collection_completed": False if startup else None,
        "observed_node_count": len(nodes),
        "exception": failure.get("exception") or None,
        "output_excerpt": (output[-4000:] if output.strip() else error.get("message", "")),
    }
    if not blocked:
        state.recovery_active = generation > 0 and not result.get("ok", False)
    return evidence


def is_non_product_signal(evidence: dict[str, Any]) -> bool:
    """Suppress automatic localization from unreliable execution evidence."""
    return bool(evidence["startup_or_collection_signal"] or evidence["timed_out"]
                or evidence["policy_blocked"] or evidence["exit_code"] is None)


def evidence_message(evidence: dict[str, Any], changed_files: list[str] | None = None) -> str:
    # Bound the model-visible payload while retaining complete observations in trace.
    view = {**evidence, "changed_files": changed_files}
    nodes = evidence["observed_node_outcomes"]
    view["observed_node_outcomes"] = dict(list(nodes.items())[:40])
    view["node_outcomes_truncated"] = len(nodes) > 40
    if evidence["test_delta"] is not None:
        view["test_delta"] = {
            key: {"count": len(value), "sample": value[:40]} if isinstance(value, list) else value
            for key, value in evidence["test_delta"].items()
        }
    return (
        "TEST_EVIDENCE (observations, not a diagnosis):\n"
        + json.dumps(view, ensure_ascii=False)
        + "\nInfer whether this is a product failure, environment issue, expected experiment "
          "or unknown. Missing outcomes are unknown. Decide whether to inspect, experiment, "
          "continue patching, undo or verify; no cause or action is prescribed. "
          "Do not treat startup errors or a changed failure signature as proof of patch failure or progress."
    )
