# Real Issue admission package (evaluator only)

The 20 admitted tasks are frozen in `benchmarks/manifests/real_issue_full_frozen_20_v1.json`. They passed two F2P/P2P/hidden matrices, reference-patch scoring, isolated Agent runtime checks, and final audit. tomlkit #377 also passed one real LLM end-to-end acceptance. See [validation_progress.md](validation_progress.md) for evidence. Never expose this evaluator package or private directory to the Agent.

## Local execution (Python 3.12+, Git, network)

```powershell
python admission.py --private E:/RealIssueEvaluator --task real_anyio_1466
python admission.py --private E:/RealIssueEvaluator
```

Choose either pilot or full run; existing task folders are deliberately not overwritten. For full run after pilot, use a new private directory or explicitly select remaining IDs. Preparation fetches each pinned merge, exports a clean baseline without `.git`, splits source/tests/docs, and writes review.json. No dependency installation or LLM execution at this stage. A fetch/apply failure is a blocker, not grounds to silently alter the base.

## Review and validation

For each task, check original issue, merge-parent diff, test scope and original user provenance, semantic duplication, dependencies and leakage. Author a separate visible reproducer patch against base; reserve upstream regression tests (or a reviewed subset plus independent cases) for hidden evaluation. Do not expose original issue text if it gives a solution; record all redactions in evaluator records. The catalog's behavior text is only a symptom summary, not a full task prompt. Set review.json issue_text to a reviewed problem statement with reproduction. For multi-purpose PRs, trim unrelated hunks/tests (AnyIO 1391, Trio 3578, Click 3362). The admitted tasks use per-task locked Python versions, dependencies, and image IDs.

Fill review.json: `python_executable` (absolute), `install_args` (pip argument list, e.g. `['install','-r','<absolute locked requirements>','-e','.']`, adapt to upstream; lock transitive deps/build dependencies), `visible_test_patch`, `hidden_test_patch`, `reference_patch` (paths relative to task_dir), `f2p_args`, `p2p_args`, `hidden_args` (pytest argument lists), `status: reviewed`. Choose P2P nodes that pass on original source and are relevant; do not silently deselect failures. Ensure hidden and visible tests do not overlap or reveal source solution. On Python 3.10, validation is orchestrated by Python 3.12+ but creates the task-specific venv using the configured executable.

```powershell
python validate.py E:/RealIssueEvaluator/real_anyio_1466
```

Runs fresh copies and fresh environments for all six matrix cells; stores private JUnit, install and test logs. Passing matrix is necessary, not sufficient: manually confirm baseline failures are intended assertions, no unrelated changes, stable repeats, correct environment/installed source, and actual isolation. Install and test arbitrary upstream code in a disposable isolated VM/container with no credentials, not on a privileged host. No claim of network/filesystem sandboxing is made by these scripts.

## Integration (after admission)

Existing `app/schemas/task_schema.py` forbids extra top-level fields; existing `app/runtime/batch_runner.py` resolves manifest entries from project root and trusts Agent final_status. `app/agent/llm_agent.py` copies source repo into workspace and uses task.test_command. Do not treat its success as final hidden acceptance. Existing harness uses its own Git history for Undo. Provide only a fresh export plus visible test patch, never upstream .git or evaluator directory. For each admitted task, create Task JSON with existing schema, empty target_files_hint, reviewed issue_text, visible pytest command, source_type real_issue, and no fix PR/commit/hidden paths in metadata. Keep evaluator mapping and reference hashes private. Verify actual agent tool path confinement and deny network in runtime; restrict evaluator access by separate OS account/container. Run final hidden tests in evaluator-owned clean baseline + agent production diff, reject modifications to evaluation fixtures/configuration or other files that circumvent tests. Export only results, not hidden test contents. Do not run hidden tests in Agent workspace. Freeze only when all 20 admitted, environment locks and isolation are verified. Existing semi-real manifest must not be modified.

## Reserve replacements
- urllib3/urllib3 #5206 -> PR 5254 (root cause disclosed in original report)
- urllib3/urllib3 #5346 -> PR 5347 (original report proposes solution)
- urllib3/urllib3 #5077 -> PR 5102 (original report proposes solution)
- psf/requests #6711 -> PR 7315 (check overlap)

attrs #1479 is excluded (existing semi-real task_058). The frozen set has 20 tasks and 10 repositories. Semantic dedup and source review are recorded in [candidate_triage.md](candidate_triage.md). One paid LLM acceptance ran on tomlkit #377; no remote repository changes were made.

### Registration gate

`register.py` is a gated integration helper. It checks all 20 validation records, patch/review hashes and evaluator audit flags before writing any task or frozen manifest. It does not perform the audit itself. Add `issue_title`, `public_test_command`, `public_success_criteria`, and optionally `visible_failure_test` to each reviewed `review.json`. Add `audit.json` with `validation_sha256` and true values for the eight named gates only after actual review. Do not set flags mechanically. Task IDs are prefixed `real_full_` to separate the new run history from older tasks. Registration refuses to overwrite the existing real/semi-real task directories.

**Frozen task execution:** use the locked task-specific Agent image and single-task export via `runtime_agent_probe.py`, then score the extracted production diff with the private Evaluator. The old `run_batch` path rejects `real_full_` tasks because its Agent-reported status is not an external score. The Pydantic task uses a separate Harness virtualenv and its validated system Python for tests. Only tomlkit #377 received a paid LLM run; no batch experiment was performed.

**Cross-task leakage:** the baseline of pytest #15337 already contains the fix for #15370; the baseline of marshmallow #2869 contains the fix for #2900. Keep workspaces and all other tasks inaccessible to a running Agent. The catalog itself must remain private.
