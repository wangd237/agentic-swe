# Ollama Minimal Smoke v16.5.34 Local 7B Sample 002

- run_count: `5`
- unique_task_count: `4`
- accepted_count: `2`
- accepted_rate: `0.40`
- unique_task_accepted_count: `2`
- avg_duration_sec: `20.9354`
- avg_llm_duration_sec: `19.1248`
- avg_tokens: `828.8`

| Task | Smoke ID | Accepted | Duration | LLM Sec | Calls | Tokens | Pre | Apply | Post | Diff | Failure |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| `task_006` | `ollama_minimal_smoke_20260629T065513201250Z` | `True` | 23.4389 | 21.1214 | 1 | 590 | 1 | True | 0 | 211 | `none` |
| `task_008` | `ollama_minimal_smoke_20260629T065551465467Z` | `False` | 16.3891 | 15.1251 | 1 | 546 | 1 | False | None | 0 | `invalid_patch_schema` |
| `task_008` | `ollama_minimal_smoke_20260629T070049389282Z` | `False` | 23.2116 | 22.1934 | 2 | 1328 | 1 | False | None | 0 | `invalid_patch_schema` |
| `task_010` | `ollama_minimal_smoke_20260629T065847057379Z` | `False` | 19.7184 | 17.6326 | 1 | 809 | 1 | True | 1 | 417 | `post_test_failed` |
| `task_013` | `ollama_minimal_smoke_20260629T065931431720Z` | `True` | 21.9188 | 19.5513 | 1 | 871 | 1 | True | 0 | 378 | `none` |
