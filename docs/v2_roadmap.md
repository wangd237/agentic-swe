# V2 路线图：把 Agent 做成可投递作品

> 当前目标不是继续把项目做成 benchmark infra，而是把它收口成一个能服务 AI Agent 实习投递的 coding agent 项目。

## 1. 当前判断

v1 已经证明了两件事：

- 有一套可复现的验证底座：任务、workspace 隔离、trace / result / patch 落盘、规则版 baseline、冻结集和稳定性复跑。
- 有一个真实 LLM coding agent：通过 OpenAI-compatible tool calling 读 issue、搜代码、写 patch、跑测试，并已有 5 条可审计成功案例。

所以 v2 的主线不再是“继续扩 benchmark 规模”，而是：

```text
更强 agent 能力证据
        |
        v
更清晰 case study
        |
        v
更适合简历和面试的项目叙事
```

benchmark / frozen / maturity 继续保留，但它们是验证层，不是项目主角。

## 2. V2 成功标准

### Agent 能力

- LLM agent 至少覆盖 `8-10` 条真实 issue 派生任务。
- 样本中包含：
  - 简单单文件修复；
  - 至少 1 条跨文件或长上下文任务；
  - 至少 1 条失败或边界案例，并带清晰 `incomplete_reason`。
- 每条代表任务都能回链到 `trace.json / result.json / patch.diff`。

### 展示材料

- README 首屏能在 1 分钟内说明：
  - 这是一个什么 agent；
  - agent 会怎么做；
  - 怎么证明它不是 demo。
- `docs/agent_case_studies.md` 至少有 3 个可讲述案例：
  - 成功案例；
  - 复杂案例；
  - 边界或失败案例。
- `docs/agent_eval_summary.md` 持续维护小样本评测表，不把它夸大成完整 benchmark 成功率。

### 工程可信度

- 保留规则版 baseline 作为稳定参照。
- 保留 frozen / stability 作为回归保护。
- LLM provider 保持 OpenAI-compatible 抽象，不能把代码写死到 DeepSeek。

## 3. 当前数据快照

| 维度 | 当前状态 |
| --- | --- |
| LLM agent 主样本 | `5 / 5` success |
| 扩展样本 | `2` success + `1` incomplete boundary |
| 平均工具调用数 | `6.0` |
| 当前 LLM policy | `llm_deepseek_minimal` |
| Provider 抽象 | OpenAI-compatible，可切换 Kimi / GLM 等 |
| 验证底座 | `66` 正式任务 + `6` challenge 任务 |
| 规则版 baseline | `improved_v71` 正式集稳定通过 |

## 4. 当前最高优先级

### P0：补 1 条更复杂的 LLM Agent 案例

目标不是再刷数量，而是补作品集里最缺的一类证据：agent 能处理更长上下文或跨文件修复。

完成标准：

- 真实运行 `scripts/run_issue_agent.py`；
- 产物包含 `trace.json / result.json / patch.diff`；
- README 和 case study 能说明 agent 的关键决策点；
- 如果失败，也必须保留为带 `incomplete_reason` 的边界案例。

### P1：把失败分类变成展示资产

当前代码已经写入 `incomplete_reason`。下一步要把它用起来：

- `no_patch`：测试已绿但没有实际修复；
- `failed_tests`：生成了 patch 但验证失败；
- `max_iterations`：达到轮次上限仍未收束；
- `no_tests_run`：未完成验证；
- `unverified_patch`：有改动但不是当前 generation 的测试结果。

这些分类能说明 agent 项目不是“只报成功”，而是有真实边界和可审计失败。

### P2：精简 README 首屏

README 现在已经切回 agent 主线，但仍然保留了较多验证底座细节。后续应继续压缩：

- 首屏优先放 agent 能力；
- benchmark 数字放到“验证底座”折叠叙事里；
- 代表案例优先链接 agent case study。

## 5. 暂缓事项

以下内容不是废弃，而是暂时不作为主线：

- 继续扩正式 benchmark 数量；
- 继续围绕 `improved_v*` 做规则 patcher 迭代；
- 深挖 pytest 性能复核；
- 新增 maturity / tracking 自动化；
- 提前做 UI、多 agent 或训练增强。

判断标准很简单：如果它不能直接增强“我做了一个可信 coding agent”的求职叙事，就先不要让它占主线。

## 6. 推荐执行顺序

1. 选择 1 条更复杂但可控的真实 issue 派生任务。
2. 用 LLM agent 真实跑一遍。
3. 根据结果补 `agent_eval_summary`。
4. 把最有代表性的成功或失败写进 `agent_case_studies`。
5. 再回头精简 README 首屏。

## 7. 一句话总结

V2 的核心不是“更大的 benchmark”，而是“更像一个可以拿去面试的 agent 项目”：有真实能力、有可审计轨迹、有失败边界，也有工程底座证明它不是一次性 demo。
