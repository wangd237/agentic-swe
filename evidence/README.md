# Evidence — 代表性 Agent Run 产物

本目录存放可直接审计的 LLM agent 运行证据。每个子目录对应一个 benchmark 任务，
包含该任务一次完整成功运行的四个产物：

| 文件 | 内容 |
|---|---|
| `trace.json` | 完整工具调用轨迹：每步的 phase、state snapshot、evidence ids、token 消耗 |
| `result.json` | 最终结果：final_status、verification evidence、verifier report、tool stats |
| `patch.diff` | 本次修改内容 |
| `summary.md` | 面向人的结果摘要 |

## 运行环境

- 模型：`Qzhou/kimi-k2.5`（OpenAI-compatible 网关）
- policy：`optimization/policy_versions/llm_deepseek_minimal.json`
- 日期：2026-08-29
- 复现命令：

```bash
python scripts/run_issue_agent.py \
  --task benchmarks/tasks/<task_id>.json \
  --policy optimization/policy_versions/llm_deepseek_minimal.json
```

## 结果汇总

| Task | 来源 Issue | 状态 | 工具调用 | Token |
|---|---|---|---:|---:|
| task_010 | Textualize/rich#4090 | success / accepted_success | 10 | 16,169 |
| task_016 | pallets/click#3111 | success / accepted_success | 10 | 14,502 |
| task_019 | dateutil/dateutil#1432 | success / accepted_success | 9 | 14,896 |
| task_024 | pallets/jinja#2069 | success / accepted_success | 10 | 20,695 |
| task_026 | pallets/jinja#2118 | success / accepted_success | 8 | 11,849 |
| task_036 | python-jsonschema/jsonschema#1121 | success / accepted_success | 9 | 13,301 |
| task_038 | python-jsonschema/jsonschema#1159 | success / accepted_success | 8 | 9,975 |
| task_048 | pypa/packaging#886 | success / accepted_success | 8 | 12,137 |
| task_052 | python-jsonschema/jsonschema#1165 | success / accepted_success | 8 | 12,287 |
| task_054 | pydantic/pydantic#9582 | success / accepted_success | 10 | 18,452 |
| task_093 | pallets/click#3572 | success / accepted_success | 9 | 15,215 |
| task_122 | fsspec/filesystem_spec#979 | success / accepted_success | 9 | 13,195 |
| task_128 | agronholm/anyio#82 | success / accepted_success | 10 | 16,275 |

13/13 `accepted_success`，全部 `evidence_quality: strong`（pre-test 失败 → patch → full test 通过）。

## 说明

- 这些任务是 semi-real benchmark（从真实 GitHub issue 提炼的最小复现场景），
  验证的是 agent 闭环能力，不等价于 SWE-bench 官方 resolved。
- SWE-bench Lite 任务的官方 harness 验证状态见 README 量化结果表。
