# Real Issue admission package (evaluator only)

Not a frozen benchmark. 20 candidate records use GitHub-verified PR base and merge SHAs, plus upstream test paths and behavior summaries. `observed_pr_base` is not guaranteed to be the correct pre-fix commit. Preparation resolves the first parent of the actual merge and records any discrepancy; review that selection and confirm failure. Never expose this package or private directory to the Agent.

## Local execution (Python 3.12+, Git, network)

```powershell
python admission.py --private E:/RealIssueEvaluator --task real_anyio_1466
python admission.py --private E:/RealIssueEvaluator
```

Choose either pilot or full run; existing task folders are deliberately not overwritten. For full run after pilot, use a new private directory or explicitly select remaining IDs. Preparation fetches each pinned merge, exports a clean baseline without `.git`, splits source/tests/docs, and writes review.json. No dependency installation or LLM execution at this stage. A fetch/apply failure is a blocker, not grounds to silently alter the base.

## Review and validation

For each task, check original issue, merge-parent diff, test scope and original user provenance, semantic duplication, dependencies and leakage. Author a separate visible reproducer patch against base; reserve upstream regression tests (or a reviewed subset plus independent cases) for hidden evaluation. Do not expose original issue text if it gives a solution; record all redactions in evaluator records. The catalog's behavior text is only a symptom summary, not a full task prompt. Set review.json issue_text to a reviewed problem statement with reproduction. For multi-purpose PRs, trim unrelated hunks/tests (AnyIO 1391, Trio 3578, Click 3362). Verify original source report for pytest 15370; replace if authenticity cannot be established. For pytest 15337, use exact Python 3.10.0 unless an independently validated equivalent reproduction is justified. For attrs 1575 use Python 3.14. Other versions/dependencies are not locked yet.

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

attrs #1479 is excluded (existing semi-real task_058). Current candidate set has 20 tasks and 10 repositories; full semantic dedup remains outstanding. No paid Agent calls. No remote repository changes.

### Registration gate

`register.py` is a gated integration helper. It checks all 20 validation records, patch/review hashes and evaluator audit flags before writing any task or frozen manifest. It does not perform the audit itself. Add `issue_title`, `public_test_command`, `public_success_criteria`, and optionally `visible_failure_test` to each reviewed `review.json`. Add `audit.json` with `validation_sha256` and true values for the eight named gates only after actual review. Do not set flags mechanically. Task IDs are prefixed `real_full_` to separate the new run history from older tasks. Registration refuses to overwrite the existing real/semi-real task directories.

**Runtime integration blocker:** current `copy_repo_to_workspace` invokes `python -m pip install -e . -q` in the process environment and does not check install failures; `run_tests` runs the task command with `shell=True`. Each task must run in a correctly pinned task-specific environment, not a common Python environment. Provision offline dependencies or adjust the evaluation harness (not Agent decision logic) to validate installs, enforce per-task environment and network isolation. A separate evaluator process/container must apply agent production diff to the clean baseline, then rerun hidden + P2P tests. Existing `run_batch` uses the Agent's own `final_status`; external result integration has not been implemented. Do not start paid evaluations until verified.

**Cross-task leakage:** the baseline of pytest #15337 already contains the fix for #15370; the baseline of marshmallow #2869 contains the fix for #2900. Keep workspaces and all other tasks inaccessible to a running Agent. The catalog itself must remain private.
