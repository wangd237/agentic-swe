# Current Task: Agent Core Upgrade

## Tracking Status

Status: **complete for Agent Core Upgrade v1**

Last verified command:

```text
python -m pytest tests/test_agent_memory.py tests/test_strategy_memory.py tests/test_verification.py tests/test_llm_agent.py tests/test_reflector.py tests/test_tool_policy.py tests/test_code_locator.py tests/test_run_metrics.py tests/test_read_file.py tests/test_tool_executor.py tests/test_runtime_diagnostics.py tests/test_repair_bug.py -q
```

Last verified result:

```text
110 passed
```

Current implementation evidence:

- Structured state and memory models exist in `app/agent/memory.py`.
- Phase-aware tool policy exists in `app/agent/tool_policy.py`.
- Code localization ranking exists in `app/agent/code_locator.py`.
- Graded verification helpers exist in `app/agent/verification.py`.
- Structured reflection helpers exist in `app/agent/reflector.py`.
- Agent-core metrics exist in `app/agent/run_metrics.py`.
- Strategy memory exists in `app/agent/strategy_memory.py`.
- The main LLM repair loop integrates phase state, tool policy, localization, verification, reflection, trace fields, and metrics in `app/agent/llm_agent.py`.
- Trace schema now carries `phase`, `state_snapshot`, `evidence_ids`, `reflection_type`, and `verification_strength`.
- Tests currently cover state models, tool policy gates, localization, verification grading, reflection decisions, strategy memory, trace/phase recording, read-file line ranges, tool executor behavior, and LLM-agent policy integration.
- A user-facing `repair_bug.run_repair_bug()` smoke test now creates a local buggy repo, generates a task through the CLI helper path, runs the real `LLMCodeAgent` core with a fake LLM client, reproduces the failing test, patches in an isolated workspace, performs automatic diff plus targeted/full verification, and reaches `final_status=success` with `verification_strength=full`.
- `pre_repro_rate` now treats a pre-patch failing `run_tests` result as valid reproduction evidence, because failing tests are the expected proof for bug repair.
- A weak/static user-entry smoke test now creates a local repo without tests, lets `repair_bug.run_repair_bug()` discover `pytest_fallback`, applies a patch through the real `LLMCodeAgent` core with a fake LLM client, and verifies that the result is downgraded to `final_status=success_weak_verification` with `incomplete_reason=weak_verification` and `verification_strength=weak`.
- The user-facing CLI summary now prints `verification_strength`, `incomplete_reason`, `pre_test_exit_code`, and `post_test_exit_code`, so users can distinguish full verification from weak/static verification.
- Weak/static reproduction evidence is preserved through fallback `run_tests` calls instead of being overwritten as normal test evidence.
- Dirty worktree review is complete for this task: files are classified below as Agent Core v1, user-entry validation, or deferred/peripheral work.

## Worktree Scope Classification

### Agent Core v1 Scope

These files are part of the current Agent Core Upgrade v1 implementation or its direct tests:

- `app/agent/llm_agent.py`
- `app/agent/llm_prompts.py`
- `app/agent/tool_definitions.py`
- `app/agent/tool_executor.py`
- `app/agent/code_locator.py`
- `app/agent/memory.py`
- `app/agent/reflector.py`
- `app/agent/run_metrics.py`
- `app/agent/strategy_memory.py`
- `app/agent/tool_policy.py`
- `app/agent/verification.py`
- `app/schemas/trace_schema.py`
- `app/tools/read_file.py`
- `app/runtime/harness.py`
- `tests/test_agent_memory.py`
- `tests/test_code_locator.py`
- `tests/test_harness.py`
- `tests/test_llm_agent.py`
- `tests/test_read_file.py`
- `tests/test_reflector.py`
- `tests/test_run_metrics.py`
- `tests/test_strategy_memory.py`
- `tests/test_tool_executor.py`
- `tests/test_tool_policy.py`
- `tests/test_verification.py`

### User-Entry Validation Scope

These files support the user-facing local-repo repair path used to validate the agent core:

- `scripts/repair_bug.py`
- `tests/test_repair_bug.py`

The GitHub repo/issue URL helpers in `scripts/repair_bug.py` are retained as input compatibility only. They should not become the next engineering focus.

### Documentation / Tracking Scope

These files document or track the current direction:

- `currentTask.md`
- `README.md`
- `docs/agent_overview.md`

### Deferred / Peripheral Scope

These changed files should not define Agent Core v1 completion unless explicitly pulled into a later task:

- `.gitignore`
- `docs/stress_test_report.md`
- `evals/compare_evals.py`

### Unrelated / User-Owned Scope

These untracked files appear outside the Agent Core v1 implementation boundary and should not be modified or cleaned up without explicit user direction:

- `mytask.py`
- `面试准备.md`

## Future Work

- Refactor duplicated auto-verification/final-verification logic in `app/agent/llm_agent.py` after behavior is locked by tests.
- Keep GitHub repo/issue URL support as an input convenience only unless a later task explicitly asks for GitHub/PR workflow work.
- Do not move into dashboards, bulk benchmarks, SWE-bench Docker integration, token management, or broad multi-language support until the agent core has been exercised on more local/real-repo repair cases.

## Direction

The project must refocus on the coding agent itself.

The final goal is not a benchmark runner, GitHub crawler, or PR automation tool. The goal is a real-repo bug repair coding agent that can receive a software issue, work inside an isolated repository workspace, understand the problem, reproduce it, localize the relevant code, patch it, verify the fix, and output an auditable result.

## Expected Agent Workflow

Upgrade the current loose ReAct-style tool loop into a more disciplined agent workflow:

```text
UNDERSTAND -> REPRODUCE -> LOCALIZE -> PATCH -> VERIFY -> FINAL
```

The agent should use tools inside each phase, but the phase should control what the agent is allowed to do and what evidence it must produce before moving on.

## Core Technical Direction

The recommended architecture is:

```text
Plan-and-Execute state machine
  + phase-local ReAct micro-loops
  + structured reflection / self-correction
```

This keeps the flexibility of tool-use agents while adding engineering discipline:

- explicit phases
- phase-specific tool permissions
- patch entry gates
- verification requirements
- structured failure recovery
- traceable decisions

## P0 Improvements

### 1. Explicit Agent State

Introduce structured run state, such as:

- current phase
- issue summary
- failure signature
- localization candidates
- hypotheses
- modified files
- verification strength

Candidate module:

```text
app/agent/memory.py
```

Suggested structures:

- `AgentState`
- `FailureSignature`
- `LocalizationCandidate`
- `ReflectionDecision`

### 2. Phase-Aware Tool Control

Introduce a tool policy layer so tools are not available freely in every phase.

Candidate module:

```text
app/agent/tool_policy.py
```

Initial policy:

```text
UNDERSTAND: list_files, grep, search_code, read_file
REPRODUCE: run_tests, read_file
LOCALIZE: grep, search_code, read_file, python_repl
PATCH: read_file, edit_file, write_file, show_diff, undo
VERIFY: run_tests, show_diff, read_file, undo
FINAL: show_diff
```

Hard gates:

- no `edit_file` / `write_file` before `PATCH`
- no `PATCH` before reproduction evidence, unless explicitly marked as weak/static
- modified files should be localization candidates, unless an override reason is provided
- every write must be followed by verification
- weak verification must not be reported as normal success

### 3. Better Localization

Improve code localization before patching.

Candidate module:

```text
app/agent/code_locator.py
```

Inputs to use:

- task hints
- issue keywords
- stack trace / failure summary locations
- failed test names
- search/grep hits
- Python AST symbol index
- import relationships between tests and implementation files

Target output:

```text
top candidate files with reason, evidence, and confidence
```

### 4. Stronger Verification

Verification should be explicit and graded.

Candidate module:

```text
app/agent/verification.py
```

Verification levels:

- `none`
- `weak`
- `targeted`
- `full`

Expected behavior:

- run pre-reproduction before patching when possible
- run targeted tests after patching if a failing test can be identified
- run the original full test command before reporting success
- show diff before final verification
- distinguish real success from weak or unverified results

### 5. Reflection And Self-Correction

Add structured reflection when:

- tests fail after a patch
- failure signature does not change
- the agent repeatedly edits the same file
- localization confidence is low
- diff touches too many files
- verification is weak or missing

Candidate module:

```text
app/agent/reflector.py
```

Reflection should decide:

- whether the failure changed
- likely cause
- next phase
- required next actions
- whether to undo the last patch

## Trace And Metrics

Extend trace data so agent behavior can be evaluated directly.

Useful fields:

- `phase`
- `state_snapshot`
- `evidence_ids`
- `reflection_type`
- `verification_strength`

Key metrics:

- `phase_completion_rate`
- `pre_repro_rate`
- `localization_precision@3`
- `write_before_repro_count`
- `unverified_patch_rate`
- `success_full_verify_rate`
- `weak_success_rate`
- `undo_recovery_rate`

## What To Defer

Do not make the next engineering push about these outer features:

- GitHub PR creation
- private repository support
- token management
- dashboard / leaderboard
- full SWE-bench Docker integration
- broad multi-language support
- bulk issue processing

These features may be useful later, but they do not directly improve the agent core.

## Next Engineering Task Package

Implement Agent Core Upgrade v1:

1. Add structured `AgentState` and related memory models.
2. Add phase-aware tool policy.
3. Extend trace steps with phase/state fields while keeping backward compatibility.
4. Update the main LLM system prompt to require the phase workflow.
5. Enforce at least the first hard gate: no writes before reproduction/localization evidence.
6. Add tests proving the agent/tool policy blocks premature writes and records phase information.
