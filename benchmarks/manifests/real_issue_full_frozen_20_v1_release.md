# Real Issue frozen 20 v1

Frozen manifest: `benchmarks/manifests/real_issue_full_frozen_20_v1.json`.

| Item | Count |
| --- | ---: |
| Tasks / repositories | 20 / 10 |
| F2P / P2P / hidden test cases | 30 / 38 / 60 |
| Repeated six-cell matrices | 20 / 20 |
| Accepted reference patches | 20 / 20 |
| Locked Agent runtime admissions | 20 / 20 |
| Real paid LLM end-to-end acceptance | 1 (tomlkit #377) |

Python versions: 3.10.0 (1 task), 3.10.20 (3), 3.12.16 (10), 3.13.18 (4), 3.14.7 (2).

The Agent receives one public task export and the reviewed task statement. Reference patches, hidden tests, Evaluator records, credentials, and other tasks stay outside its mounts. The independent Evaluator owns the final score. The legacy batch runner rejects `real_full_` tasks.

## Formal single-task execution

Run from the project root after provisioning the private Evaluator directory, its locked Docker images, a per-task public export, an environment file containing `LLM_API_KEY` and `LLM_MODEL`, and the restricted Docker network with the `model-proxy` alias. The proxy must forward only `/chat/completions` to the configured model endpoint. Use a fresh label for each run.

```powershell
$taskId = 'real_tomlkit_377'
$privateRoot = '<PRIVATE_EVALUATOR_ROOT>'
$exportRoot = '<PUBLIC_SINGLE_TASK_EXPORT_ROOT>'
$envFile = '<PRIVATE_LLM_ENV_FILE>'
$image = (Get-Content "$privateRoot/$taskId/agent_runtime.json" -Raw | ConvertFrom-Json).image
python tools/real_issue_admission/runtime_agent_probe.py "$privateRoot/$taskId" "$exportRoot/$taskId" app $image --label formal_001 --llm-env $envFile --network real_issue_acceptance_internal
```

The command executes the existing Agent in the task-specific locked container, extracts its production diff after exit, and writes the independent hidden/P2P verdict to the private `runtime_agent_probe/formal_001/pipeline_result.json` and `scoring/result.json`. Do not use `app.runtime.batch_runner` for this manifest. No batch LLM run is part of this release.
