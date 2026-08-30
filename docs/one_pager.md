# Agentic SWE One-Pager

## What This Is

一个 OpenAI-compatible coding agent：读取真实 issue 派生任务，在隔离 workspace 中读代码、搜索、编辑、运行测试，并把完整 trace/result/patch 落盘供审计。

## Architecture

```text
GitHub issue / semi-real task
        |
        v
Task JSON + policy
        |
        v
isolated git workspace
        |
        v
LLM tool loop
  list/search/read -> edit/write -> run_tests -> show_diff
        |
        v
Result artifacts
  trace.json + result.json + patch.diff + summary.md
```

## Core Numbers

| Signal | Current Evidence |
| --- | --- |
| **SWE-bench Lite official harness** | **resolved 3/8 submitted**（官方 Docker harness 判定，[证据](../evidence/swebench_lite_official/)）|
| Tool surface | 11 tools, including safe `python_repl` |
| Semi-real benchmark | 132 tasks; 13 representative runs all `accepted_success` with `evidence_quality: strong`（[证据](../evidence/)）|
| Regression suite | 374 pytest passes |
| Frozen-set discipline | `frozen_40` stable across 72+ policy versions |
| Token optimization | `task_010`: 30,510 → 18,553 tokens, 7 → 5 LLM calls |
| Provider design | OpenAI-compatible, not tied to any vendor |

## Best Case In One Minute

`task_048` was a packaging version bug. The model previously guessed `Version.base_version` semantics and hit `max_iterations`. After Target 2, the agent used safe `python_repl` to query reality:

```python
str(Version("4.1.0a2.dev1235+local").base_version)
# '4.1.0'

Version("4.1.0a2.dev1235+local").public
# '4.1.0a2.dev1235'
```

That changed the patch from guessing to evidence-based:

```python
if prospective_version.local is not None:
    return Version(prospective_version.public) > self.spec_version
```

Result: `task_048` success, 11 tool calls, target tests passed.

## Why It Matters

- The agent does not self-report success; success requires patch + tests + verified workspace generation.
- The trace shows decision quality, not just final diff.
- Harness improvements are measured on hard tasks, then turned into case studies.
- The project is auditable by design: anyone can open README, this one-pager, a case study, and a raw trace.

## Clone To Run

```bash
python -m pip install -r requirements.txt
cp .env.example .env
python scripts/run_issue_agent.py --task benchmarks/tasks/task_048.json --policy optimization/policy_versions/llm_deepseek_minimal.json
```

Fill `.env` with any OpenAI-compatible provider. DeepSeek, Kimi, GLM, and a generic template policy are included.
