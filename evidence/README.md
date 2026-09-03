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

## 真实 GitHub Issue 运行（2026-09-02）

- 模型：`kimi-k3`（#411）/ `glm-5.2`（#377、#938）（OpenAI-compatible，阿里云 MaaS）
- policy：`optimization/policy_versions/llm_real_issue_32steps.json`（32 步）
- 任务来源：真实 GitHub issue + 官方 fix commit 已知，agent 仅拿到 issue 文本与失败测试

| Task | 来源 Issue | 状态 | LLM 调用 | Token | 修改文件 |
|---|---|---|---:|---:|---|
| real_tomlkit_411 | python-poetry/tomlkit#411 | success / accepted_success | 25 | 388,925 | `tomlkit/api.py` |
| real_tomlkit_377 | python-poetry/tomlkit#377 | success / accepted_success | 32 | 496,715 | `tomlkit/items.py` |
| real_tomlkit_381_failed | python-poetry/tomlkit#381 | incomplete（max_iterations ×2，32/48 步） | 80 | 760,720 | —（定位失败，非预算不足） |
| real_packaging_938 | pypa/packaging#938 | success / accepted_success | 9 | 73,381 | `src/packaging/markers.py` |

3/4 success。修复语义均与官方 fix commit 一致（diff 形状不同，评分看行为不看形状）：

- **#411**：`dumps()` 的 isinstance 判断从 `Container` 扩为 `(Container, _Item)`（官方为 `(Table, InlineTable, Container)`，`_Item` 基类覆盖更广）
- **#377**：`is_super_table` 从“单 child 判断”改为“所有 child 均为 Table/AoT”（与官方重构方向一致）
- **#938**：`_eval_op` 对 `extra` marker 按纯字符串比较，跳过版本解析
- **#381**（失败）：agent 两次均在 parser 侧探索，官方修复在渲染侧 `container.py`（4 处渲染点补换行）。后段重复 grep 同一符号——定位策略缺陷，加步数无用。详见 `real_tomlkit_381_failed/`

回归验证：tomlkit 858 passed（其余两个独立任务的测试失败符合预期）；packaging 全量 26,952 passed, 1 skipped，零回归。

## 说明

- 这些任务是 semi-real benchmark（从真实 GitHub issue 提炼的最小复现场景），
  验证的是 agent 闭环能力，不等价于 SWE-bench 官方 resolved。
- SWE-bench Lite 任务的官方 harness 验证状态见 README 量化结果表。
