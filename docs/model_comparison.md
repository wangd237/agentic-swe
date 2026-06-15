# Model Comparison

状态：Target 2 interim report。当前只包含 DeepSeek frozen_40 结果，用于记录 scratch-file guard 后的最新基线；这还不是 Target 2 最终三模型验收报告。Kimi/GLM 的 OpenAI-compatible policy 已配置，但 `.env` 仍缺 `KIMI_API_KEY` 和 `GLM_API_KEY`，因此跨模型交集分析会在两组 API key 到位后补齐。

## Current Finding

- DeepSeek frozen_40 after scratch guard: `39/40` success, success rate `0.975`
- Compared with the earlier DeepSeek frozen_40 run (`37/40`, `0.925`), `task_030` and `task_032` are now successful.
- Remaining DeepSeek failure: `task_048`, incomplete reason `max_iterations`; this is still a packaging `Version.base_version` semantic boundary rather than a scratch-file pollution problem.
- Current completed Target 2 pairs: `40/120`. Final Target 2 acceptance still requires at least `100` completed `(task, model)` pairs and the Kimi/GLM rows below.

## Pending Models

| Policy | Status | Missing config |
|--------|--------|----------------|
| `llm_kimi_minimal` | pending | `KIMI_API_KEY` |
| `llm_glm_minimal` | pending | `GLM_API_KEY` |

## Run

- comparison_id: `model_comparison_target2_deepseek_scratch_guard_001`
- created_at: `2026-06-15T06:50:12.107992+00:00`
- source_matrix_run_ids: `multi_model_eval_target2_deepseek_frozen40_scratch_guard_001_001`
- policy_count: `1`
- observed_task_count: `40`

## Per-Model Metrics

| Policy | Model | Tasks | Success | Success Rate | Avg Tool Calls | Avg Duration Sec |
|--------|-------|-------|---------|--------------|----------------|------------------|
| `llm_deepseek_minimal` | `deepseek-chat` | 40 | 39 | 0.975 | 7.05 | 13.7063 |

## Incomplete Reasons

- `llm_deepseek_minimal`: `max_iterations`=1

## Intersection Analysis

- all_success: `39`
- all_failed: `1`
- inconsistent: `0`
- incomplete_coverage: `0`

## Inconsistent Tasks

- no inconsistent tasks
