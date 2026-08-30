# ADR-0002: 上下文预算从字符数切换为 token 数

**日期**: 2026-08-30
**状态**: 提议中（分两步实施）

## Problem

当前 `_compress_messages_if_needed` 用 `json.dumps(ensure_ascii=False)` 字符数估算上下文大小，阈值 `max_context_chars=80000`。存在问题：

1. **估算偏差**：中文/代码混合的 JSON 内容，字符→token 映射在 1:1.5 到 1:4 之间波动，固定 80K 字符阈值在不同内容下对应 ~27K~55K token，误差难以控制。
2. **触发时机不可控**：3 个真实 compression run 的 `before_chars` 均为 80K~82K（步骤 64/78），在 16 轮迭代下实际触发偏晚且一次性大幅压缩，导致上下文质量骤降。
3. **无法设置精确 reserve**：DeepSeek 64K 窗口下，需要为最终输出和验证轮预留空间，字符数估算做不到。

## Decision

分两步落地：

**Step 1（观测增强）**: 不改判定逻辑，先把观测管道建好：
- `_normalize_usage` 保留 `prompt_tokens`（当前只保留 `total_tokens` 并丢弃 prompt），以及 DeepSeek 的 `prompt_cache_hit_tokens / prompt_cache_miss_tokens`
- `compress_context_if_needed` 的 `tool_metrics` 增加 `estimated_tokens` 与 API 返回的 `usage.prompt_tokens` 对照
- 跑 3~5 个 benchmark 任务，统计估算偏差率

**Step 2（替换判定）**: 偏差数据到手后：
- `LLMConfig` 新增 `context_window_tokens` 和 `reserve_tokens` 字段（从 `.env` / policy 读取，符合"模型配置集中在 .env"的既有决策）
- 触发条件改为 `estimated_tokens > context_window_tokens - reserve_tokens`
- 保留字符数估算作为 usage 缺失时的降级（`chars / 2.5` 保守插值）
- 熔断：LLM 摘要连续失败 3 次后降级为字符截断

## Alternatives Considered

1. **一步到位直接替换**: 没有实测偏差数据就换公式，risk/unreward 不对称。3 个真实 run 的 usage 数据缺失（见"Risks"），先观测再行动。
2. **保持字符数预算但增加动态系数**: 不如直接切 token——锚点（API usage）已经存在，加系数只是把问题往前提一层。
3. **用 tiktoken 离线估算**: 增加依赖，精度未必优于 API 返回的 prompt_tokens 校准。拒绝。

## Risks

- 历史 run 的 `result.json` 中 `llm_usage` 均为 null/空（该字段刚在 commit `2a30e94` 加入），需重新跑任务才能拿到对照数据。
- DeepSeek 的 `usage.prompt_tokens` 是否包含 cache hit 部分需实测确认（影响 P1-2 缓存观测）。
- 不同 provider（Kimi/GLM）的 usage 返回格式不一，需容错。

## Files Changed

- `app/agent/llm_agent.py`: `_normalize_usage`, `_compress_messages_if_needed`, `compress_context_if_needed`
- `app/agent/llm_config.py`: 新增 `context_window_tokens`, `reserve_tokens`
- `app/agent/policy.py`: 新增可选的 policy 字段