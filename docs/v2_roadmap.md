# V2 路线图：从「做出 v1」到「做强、做稳、做亮」

> 一句话定性：v1 已经达成，v2 的重点不再是“证明这个项目能跑”，而是把它收口成一套更稳、更可展示、也更适合持续扩容的 benchmark 基础设施。

## 1. 当前判断

这份路线图不再把“已经落地的能力”继续写成待办，而是把 v2 工作分成三层：

1. **已完成的底座能力**：已经可以依赖，不需要重复立项
2. **正在推进的主线**：当前最值得持续投入的方向
3. **后续扩展项**：等主线稳定后再推进，避免同时开太多口子

当前最合理的执行顺序是：

`性能复核常态化` → `展示层持续校准` → `缺陷覆盖均衡化` → `轻量导入自动化深化`

这和项目现状一致，因为：

- benchmark maturity v1 的硬指标已经达标
- README / architecture / experiment summary / case studies 已经有首版可展示交付物
- 候选搜索、候选状态机、semi_real 脚手架增强已经落地
- 当前真正的主缺口已经从“有没有这些能力”切到“如何持续用好这些能力”

---

## 2. 当前数据快照（2026-06-13 校准）

以下数字以当前仓库中的 manifest、候选池和 maturity 审计输出为基准。

### 2.1 正式任务集

| 维度 | 当前值 |
|------|--------|
| 正式任务总数 | **66** 条 |
| 任务形态 | **全部为 `semi_real`** |
| 来源生态数 | **16** |
| 当前主策略版本 | **`improved_v71`** |
| 冻结集规模 | **`frozen_40` = 40 条** |
| challenge 集规模 | **6** 条 |
| 候选池总数 | **72** 条（其中正式集 `66`、challenge 集 `6`） |

### 2.2 maturity 目标达成度

| 目标 | 当前值 | 目标值 | 状态 |
|------|--------|--------|------|
| 正式任务数 | 66 | 60 | ✓ 已达标 |
| 来源生态数 | 16 | 6 | ✓ 已超标 |
| frozen 集合规模 | 40 | 40 | ✓ 已达标 |
| frozen_40 连续稳定版本数 | 8 | 5 | ✓ 已超标 |

### 2.3 生态分布观察

当前任务主要集中在以下生态：

- `python-poetry/tomlkit`：14
- `pypa/packaging`：9
- `pallets/click`：6
- `pallets/jinja`：6
- `python-jsonschema/jsonschema`：6

偏斜不是错误，但它直接说明了 v2 后续扩容应该优先补：

- 只覆盖了 1 到 2 条任务的边陲生态
- 目前仍然偏薄的缺陷族群
- 还没有代表题的新生态

### 2.4 文档与展示层现状

| 文件 | 当前状态 | 结论 |
|------|----------|------|
| `README.md` | 126 行 | 已进入结果导向首页形态，后续只需同步数据 |
| `GUIDE.md` | 2774 行 | 信息全，但偏长，后续应继续做导航收口 |
| `docs/architecture.md` | 215 行 | 已完成首轮重写，需持续跟随 harness / policy 演进 |
| `docs/experiment_summary.md` | 已存在 | 已承担 results 导读层职责 |
| `docs/case_studies.md` | 5 个精选案例 | 已从流水账切到叙事型案例 |

补充说明：

- 当前 roadmap 关键状态也已开始工具化收口：
  - `scripts/snapshot_roadmap_status.py`
  - 后续续做时，不必只靠人工从多份文档恢复当前阶段

---

## 3. 已完成的 v2 底座能力

这一部分的目的不是复述历史，而是明确后续推进时哪些能力已经可以当作稳定前提使用。

### 3.1 性能复核与成熟度门控

以下能力已经落地：

- `scripts/stability_recheck.py`
- `scripts/snapshot_env_baseline.py`
- `scripts/analyze_duration_regressions.py --env-baseline`
- `scripts/run_real_issue_eval.py` 已接入 stability check
- `scripts/run_real_issue_eval.py` 已接入 benchmark maturity 审计

当前结论：

- “同版复跑 + 稳定性判断 + maturity 摘要”已经不再是规划，而是现有流水线的一部分
- v2 后续不需要再重复建设这条链路，重点应转为持续使用它做门控

### 3.2 展示层首轮收口

以下交付物已经存在且可直接对外使用：

- [README.md](/E:/My_Projects/agentic-software-engineering-roadmap/README.md)
- [docs/architecture.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/architecture.md)
- [docs/experiment_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/experiment_summary.md)
- [docs/case_studies.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/case_studies.md)
- [docs/case_studies_archive_v1.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/case_studies_archive_v1.md)

当前结论：

- D 线不再是“从 0 到 1 的重写任务”
- D 线已经进入“保持与现状同步、补 challenge 叙事、继续压缩 GUIDE 使用成本”的阶段

### 3.3 缺陷覆盖分析与候选导入轻自动化

以下能力也已经具备：

- `scripts/analyze_defect_coverage.py`
- `scripts/search_candidate_issues.py`
- `scripts/import_search_results.py`
- `scripts/screen_candidate.py`
- `scripts/scaffold_semi_real_task.py --from-candidate`
- 候选状态机最小版：`imported -> screened -> accepted -> completed`

当前结论：

- A1、C1、C2、C3 已经完成首版
- 后续重点不是“有没有脚本”，而是“这些脚本能否支撑更高质量扩容”

---

## 4. 当前主线：性能复核常态化

这是当前最优先、也最不容易出错的主线。

### 4.1 当前判断

`improved_v71` 已经完成：

- 正式集 `66 / 66`
- `frozen_20` 功能全绿
- `frozen_40` 功能全绿
- 两条冻结集的 stability recheck 都是 `stable`

但当前同时成立的是：

- `v71` 已经完成扩容闭环并通过三线最小验证，但冻结集平均耗时相对 `v70` 有所回升
- 已新增一个关键校准结论：
  - `improved_v68` 与 `improved_v69` 的 `pytest_additional_flags` 实际相同
  - 二者当前 runtime 配置等价，差异主要来自 patch 规则与环境噪声，而不是 pytest flags 本身
- 因此目前这批策略版 `pytest phases / importtime / matrix / matrix-set` 更适合作为：
  - `runtime-equivalent noise probe`
  - 也就是“同 runtime 配置下的重复测量与噪声探针”
- 热点任务复跑与策略版 pytest compare 仍然没有给出足够强的单一主因证据
- `search_code` 已从主嫌疑降级
- 当前更稳妥的判断是：
  - 如果继续做性能追因，应优先回到 `run_tests` 总链路与环境漂移校准
  - 而不是继续把 `v68 -> v69` 当成“runtime flags 对照实验”

### 4.2 这一主线的目标

目标不是“为了出 `v72` 而出 `v72`”，而是：

1. 继续把 `v68 -> v69` 的性能回升和环境噪声分开看清
2. 把当前这条 pytest compare 线明确用作“runtime 等价噪声探针”
3. 只有在构造出真正 runtime 不同的 policy pair 之后，才重新把这套脚本当作 runtime 对照实验主线

### 4.3 这一主线接下来的动作

优先级从高到低：

1. 保留当前 `pytest phases / importtime` compare 线，但口径统一为 `runtime-equivalent noise probe`
2. 继续围绕热点任务验证“第一次 `run_tests` 更值得优先关注”是否成立
3. 在没有新的 runtime-different policy pair 之前，暂缓基于 `v68 / v69` 证据直接推进新的 runtime 级策略改动
4. 把更多精力切回：
   - A 线真实 issue 扩容
   - 稳定性复跑
   - 环境基线与总链路时延复核

推荐优先补齐的任务：

- `task_097`
- `task_034`
- 如有余力，再把 `task_123 / task_119` 一起补成更完整的 4 任务 compare 集

### 4.4 进入下一轮策略改动前的门槛

只有在满足下面任一条件时，才建议推进下一轮新的 runtime 级策略版本：

- 构造出一组 `pytest_additional_flags` 真实不同的 policy pair，并在多个任务上稳定暴露相同方向
- 或者在更大样本复跑中，稳定复现某条非 runtime-config 层面的执行链回升

如果没有满足，就继续积累诊断证据，而不是过早改 runtime。

---

## 5. 当前主线：展示层持续校准

D 线已经不是重写任务，而是“保持文档始终和当前系统状态一致”。

### 5.1 已完成项

以下目标已经完成首版：

- README 首页结果导向化
- 架构文档首轮重写
- 一页纸实验摘要
- 精选案例替代模板流水账
- ASCII 架构图进入 README 和 architecture

### 5.2 当前剩余工作

这一主线后续主要做三件事：

1. 每次关键扩容或性能结论变化后，及时同步核心数字
2. 在出现新的代表性 hard case 后，补进 `docs/case_studies.md`
3. 持续压缩 `GUIDE.md` 的阅读成本，让它更像“上手指南 + phase 指引”，更少像“全量开发日志”

### 5.3 D 线的执行原则

- 不再做大规模推倒重写
- 只做与真实状态强绑定的增量校准
- 所有展示层叙事都必须能回链到现有 logs、脚本和 summary

---

## 6. 当前主线：Benchmark 均衡化扩容

A 线已经从“先做 gap 分析”进入“按 gap 分析结果定向扩容”阶段。

### 6.1 已完成项

以下能力已具备：

- 缺陷覆盖分析脚本已经存在
- 当前可信 gap report 已经生成
- 当前 A2 找题 brief 已经形成

因此 A 线下一步不是再做一次泛泛分析，而是把分析真正转成任务新增。

### 6.2 当前扩容重点

优先方向保持不变：

1. **并发与协程**
2. **文件路径与 IO**
3. **来自新生态的继承、优先级与控制流问题**

当前理由依然成立：

- 这几类题更能补齐当前 benchmark 的结构性空白
- 已有的 `anyio / fsspec / watchfiles` 线索说明扩容路径是通的
- 它们比继续在 tomlkit / packaging 上加密度，更能提高外部说服力

### 6.3 A 线的近期目标

短期目标建议明确为：

- 再补 `3` 到 `5` 条高质量正式任务
- 尽量来自当前薄弱生态或新生态
- 每次扩容都必须带正式集、冻结集与稳定性复核证据

### 6.4 A3 challenge set 的定位

challenge set 仍然值得做，但不应抢占当前主线优先级。

当前更准确的状态是：

- challenge manifest 已建立
- 已有 `6` 条 challenge 题：
  - `task_126 / samuelcolvin/watchfiles#266`
  - `task_127 / samuelcolvin/watchfiles#110`
  - `task_130 / samuelcolvin/watchfiles#169`
  - `task_131 / samuelcolvin/watchfiles#215`
  - `task_132 / Textualize/rich#2411`
  - `task_133 / Textualize/rich#2457`
- 当前真正缺的不是“有没有 challenge set”，而是继续沉淀更可展示的边界案例和 case study

最稳妥的后续做法是：

- 在不打断 A2 正式扩容主线的前提下
- 继续补第 `7` 条真正能代表系统边界的 hard case
- 并使用单独的 challenge sourcing brief 控制找题口径

理由：

- 这样不会打断当前“继续把正式 benchmark 做厚”的节奏
- 也能避免把已进正式主集的题再次误写成 challenge 候选

---

## 7. 当前主线：候选导入自动化深化

C 线的“从 0 到 1”其实已经做完了，后续应坚持轻量化深化，而不是把它过度工作流化。

### 7.1 已完成项

以下能力已经可用：

- GitHub issue 半自动搜索
- 搜索结果导入候选池
- 最小版人工筛选脚本
- `--from-candidate` semi_real 脚手架增强
- 新候选不再默认 `accepted`

### 7.2 当前剩余工作

这一主线更值得继续做的是：

1. 持续验证现有启发式能否支撑新的仓库来源
2. 控制候选池规模，不让 `imported` 长期堆积
3. 让“找题 -> 判题 -> 脚手架 -> 单任务验证 -> 正式接入”形成稳定节奏

### 7.3 明确不做什么

v2 阶段不建议把 C 线继续做重：

- 不急着做复杂状态机
- 不急着做全自动判题
- 不急着把所有隐式阶段都显式建模

目标是降低人工成本，不是把 issue sourcing 变成另一个系统工程项目。

---

## 8. 重新整理后的优先级

### P0：持续主线

这部分不是“待落地”，而是“已经有底座，当前要持续推进”：

| 编号 | 事项 | 当前状态 |
|------|------|----------|
| B-main | 用现有 stability / maturity 流水线持续做性能复核 | 进行中 |
| D-main | 保持 README / architecture / summary / case studies 与现状同步 | 进行中 |

### P1：接下来最值得做

| 编号 | 事项 | 当前状态 |
|------|------|----------|
| A2-main | 按 gap 分析继续补 `并发与协程`、`文件路径与 IO`、新生态任务 | 进行中 |
| C-main | 用现有候选导入链路维持稳定扩题节奏 | 进行中 |

### P2：条件成熟后推进

| 编号 | 事项 | 当前状态 |
|------|------|----------|
| A3 | 扩 challenge set，到 `7+` 条 hard case，并稳定 sourcing 口径 | 已启动，已有 6 条 |
| D-guide | 继续压缩 `GUIDE.md` 的导航成本 | 待持续优化 |
| B-next | 若证据足够一致，再推进下一轮 runtime 级策略版本 | 待证据触发 |

---

## 9. 执行约束

1. 任何新策略版本都必须配套正式集、冻结集、稳定性复核和 maturity 审计证据。
2. 不为了追求“有新版本”而做证据不足的 runtime 改动。
3. 不改动当前 patcher 规则继承链的既有稳定行为，新增规则必须显式接入正确版本分支。
4. 文档更新必须和代码、脚本、summary 一起同步，避免再出现“文档仍写待做，但能力已落地”的偏差。
5. challenge set 独立管理，不污染当前正式 benchmark 口径。
6. 候选导入链路坚持轻量设计，避免把 C 线做成新的复杂系统。

---

## 10. v2 阶段完成标准

v2 不应再按“是否已经有某个脚本”判断，而应按“是否形成稳定运转方式”判断。

当前建议的完成标准是：

1. **性能复核真正常态化**：每轮重要扩容或策略调整都默认带 stability check 与 maturity audit。
2. **展示层持续可信**：README、architecture、experiment summary、case studies 始终能反映当前真实状态。
3. **benchmark 继续均衡化**：在当前 66 条基础上，持续补入薄弱缺陷族群和新生态任务。
4. **challenge set 独立成立**：至少有 6 到 7 条明确展示系统边界的 hard case。
5. **候选导入链路稳定可复用**：可以低摩擦地支持后续 benchmark 扩容，而不需要重新发明流程。
6. **性能判断更保守更可证伪**：后续是否做新的 runtime 优化，都有跨任务 compare 与复跑证据支撑，而不是凭单次波动决策。

---

## 11. 这份路线图对接下来的直接含义

如果按当前最稳妥的方式继续推进，下一阶段不应再把精力花在“补齐早就有了的能力描述”，而是聚焦三件事：

1. 继续沿 `run_tests / pytest startup / collect` 主线积累更强的性能诊断证据。
2. 继续从 `并发与协程`、`文件路径与 IO`、新生态方向补真实 issue 正式任务。
3. 每轮推进后同步 `README.md`、`GUIDE.md`、`docs/project_memory.md`、`docs/next_actions.md` 和 `docs/optimization_log.md`，保持后续续做时上下文友好。

这才是当前项目最不容易出错、也最符合现状的 v2 推进方式。
