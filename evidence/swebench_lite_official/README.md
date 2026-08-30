# SWE-bench Lite 官方 Harness 评测证据

本目录存放 2026-08-30 官方 SWE-bench Docker harness 评测的完整产物。

## 结果

**resolved 3 / 8 submitted**（10 条任务中 2 条 agent 未产出 patch，未提交）

| Instance | 结果 | 备注 |
|---|---|---|
| marshmallow-code__marshmallow-1343 | ✅ RESOLVED | |
| marshmallow-code__marshmallow-1359 | ✅ RESOLVED | |
| pydicom__pydicom-1694 | ✅ RESOLVED | |
| pydicom__pydicom-1139 | ❌ | 修复引入 pass_to_pass 回归（`test_next` 挂） |
| pvlib__pvlib-python-1072 | ❌ | 修复不完整 |
| pylint-dev__astroid-1196 | ❌ | 修复不完整 |
| pylint-dev__astroid-1268 | ❌ | 修复不完整 |
| pylint-dev__astroid-1866 | ⚠️ error | 官方环境镜像构建失败（repo 自身 setup 问题） |
| pyvista__pyvista-4315 | — 未提交 | agent 未产出 patch（3 次修改均被 reflection 判 wrong_file 回滚） |
| sqlfluff__sqlfluff-1625 | — 未提交 | agent 未产出 patch（16 轮全部用于读代码） |

## 运行环境

- 模型：`deepseek-v4-flash`（DeepSeek 官方 API）
- agent：本项目 LLMCodeAgent，policy `llm_deepseek_minimal`
- harness：swebench 2.1.8 + Docker（Windows 主机，需应用 `patches/swebench/apply_windows_patches.sh`）
- 数据集：本地 `benchmarks/swebench_lite_instances.json`（10 条 instance，绕过 HF 在线下载）

## 复现步骤

```bash
# 1. 应用 Windows 补丁（Linux/macOS 跳过）
bash patches/swebench/apply_windows_patches.sh <python>

# 2. 跑 agent 生成 patch（10 条任务）
python scripts/run_issue_agent.py \
  --task benchmarks/tasks/swebench_lite/<task>.json \
  --policy optimization/policy_versions/llm_deepseek_minimal.json

# 3. 导出 prediction JSONL（有 patch 的任务）
#    见 logs/swebench_predictions.jsonl 的生成逻辑

# 4. 官方 harness 评测
python -m swebench.harness.run_evaluation \
  --predictions logs/swebench_predictions.jsonl \
  --dataset benchmarks/swebench_lite_instances.json \
  --run_id <run_id> --max_workers 2
```

## 目录结构

- `summary.json`：官方总报告（resolved/unresolved/error 统计）
- `<instance_id>/report.json`：单实例官方判定（patch 是否应用成功、是否 resolved）
- `<instance_id>/patch.diff`：提交给官方 harness 的 patch
- `<instance_id>/test_output.txt`：容器内完整测试输出

## 说明

- resolved 判定 = 官方容器内 `FAIL_TO_PASS` 全部转通过 **且** `PASS_TO_PASS` 无回归
- 本地 smoke 成功 ≠ 官方 resolved（见 pydicom-1139：本地通过但官方判回归）
- 这正是项目 Verification Quality Layer 区分 `local_smoke_success` 与 `official_resolved` 的原因
