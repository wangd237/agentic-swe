# Real Issue 准入进度（2026-11-27）

当前状态：**20/20 任务通过两轮 F2P/P2P/隐藏矩阵、参考补丁独立评分、运行时准入和最终审计；tomlkit #377 通过一次真实 LLM 端到端验收；20 个任务已注册冻结**。冻结清单为 `benchmarks/manifests/real_issue_full_frozen_20_v1.json`，包含 20 份 Task JSON 与 20 个独立仓库快照。packaging #938 因修复前测试全通过已淘汰，由 Requests #6711 替换。未修改 Agent 核心求解逻辑或旧 Manifest，未开展批量付费 LLM 实验。

## 共性工程修复

- `admission.py` 现在按基线 gitlink SHA 导出测试子模块。原 `git archive` 遗漏 `tomlkit` 固定的 `tests/toml-test`，导致 pytest 收集失败。已补齐三个 tomlkit 候选的该子模块；其余 17 个基线无 gitlink。
- `validate.py` 的补丁应用现在阻止 Git 向上发现项目父仓库。原实现对 `.tools/` 下副本返回成功却没有修改目标文件。新增容器矩阵模式，检查固定镜像 ID、完整 `pip freeze` 锁文件、源码导入路径；每格使用新副本、禁网只读容器和独立 JUnit 日志。
- `score.py` 在 Evaluator 私有目录对候选生产补丁重建干净基线，拒绝测试/配置路径变更，单独运行隐藏与 P2P。它不依赖 Agent 自报 `final_status`。
- `preflight.py` 使用正确的 Git 边界检查全部 20 个固定补丁哈希、可应用性和 gitlink 内容，**20/20 通过结构预检**。该预检不执行行为测试。

## 任务有效性验证

| 任务 | Python | F2P 修复前→后 | P2P 前/后 | 隐藏修复前→后 | 全矩阵复跑 | 参考补丁评分 |
|---|---|---|---|---|---|---|
| tomlkit #377 | 3.10.20 | 1 失败→1 通过 | 1/1 通过 | 1 失败→1 通过 | 结果一致 | 接受 |
| AnyIO #1391 | 3.13.18 | 4 失败→4 通过 | 4/4 通过 | 4 失败→4 通过 | 结果一致 | 接受 |
| Click #3362 | 3.12.16 | 1 失败→1 通过 | 5/5 通过 | 1 失败→1 通过 | 结果一致 | 接受 |
| tomlkit #381 | 3.10.20 | 1 失败→1 通过 | 1/1 通过 | 1 失败→1 通过 | 结果一致 | 接受 |
| tomlkit #411 | 3.10.20 | 1 失败→1 通过 | 1/1 通过 | 1 失败→1 通过 | 结果一致 | 接受 |
| AnyIO #1466 | 3.13.18 | 6 失败/2 通过→8 通过 | 8/8 通过 | 12 失败/4 通过→16 通过 | 结果一致 | 接受 |
| fsspec #2266 | 3.12.16 | 修复前失败→修复后通过 | 通过 | 修复前失败→修复后通过 | 结果一致 | 接受 |
| fsspec #2311 | 3.12.16 | 修复前失败→修复后通过 | 通过 | 修复前失败→修复后通过 | 结果一致 | 接受 |
| fsspec #2456 | 3.12.16 | 修复前失败→修复后通过 | 通过 | 修复前失败→修复后通过 | 结果一致 | 接受 |
| Requests #6711 | 3.12.16 | 修复前失败→修复后通过 | 回环 HTTP 前/后通过 | 修复前失败→修复后通过 | 结果一致 | 接受 |
| marshmallow #2900 | 3.12.16 | 修复前失败→修复后通过 | 2/2 通过 | 修复前失败→修复后通过 | 结果一致 | 接受 |
| pytest #15436 | 3.12.16 | 1 失败→1 通过 | 1/1 通过 | 2 失败→2 通过 | 结果一致 | 接受 |
| Trio #3578 | 3.13.18 | 1 失败→1 通过 | 1/1 通过 | 1 失败→1 通过 | 结果一致 | 接受 |
| Trio #3261 | 3.13.18 | 1 失败→1 通过 | 1/1 通过 | 1 失败→1 通过 | 结果一致 | 接受 |
| AnyIO #1479 | 3.14.7 | 1 失败→1 通过 | 1/1 通过 | 1 失败→1 通过 | 结果一致 | 接受 |
| pytest #15370 | 3.12.16 | 1 失败→1 通过 | 1/1 通过 | 1 失败→1 通过 | 结果一致 | 接受，来源已注明 |
| pytest #15337 | 3.10.0 | 1 失败→1 通过 | 1/1 通过 | 1 失败→1 通过 | 结果一致 | 接受 |
| attrs #1575 | 3.14.7 | 1 失败→1 通过 | 4/4 通过 | 2 失败→2 通过 | 结果一致 | 接受 |
| marshmallow #2869 | 3.12.16 | 1 失败→1 通过 | 1/1 通过 | 1 失败→1 通过 | 结果一致 | 接受，来源已注明 |
| Pydantic #14310 | 3.12.16 | 1 失败→1 通过 | 1/1 通过 | 1 失败→1 通过 | 结果一致 | 接受 |

每个已实测任务的 `review.json`、`dependencies.lock.txt`、补丁、`validation.json`、两轮日志均在本地私有 Evaluator 暂存区 `.tools/real_issue_evaluator/<task_id>/`，没有进入 Agent 导出。镜像按 ID 锁定，测试容器 `--network none`，源码挂载只读；JUnit 记录及导入路径检查均通过。Click 首版可见测试在基线也通过，已保留失败的初版验证记录并更换为真正触发边界的用例。packaging #938 的可见、隐藏及上游 6 个新增参数在修复前全部通过，故已淘汰。现行目录由 `build_catalog.py` 生成，20 个任务均通过结构预检。

第二轮矩阵记录此前有 9 项尚未单独保存；本次对这 9 项重新执行完整六格容器矩阵并逐项与原 `validation.json` 比较，均一致，现行 20/20 均有 `validation_repeat1.json`。

- pytest #15436 的源码快照缺少上游构建时生成的 _pytest/_version.py；已在三个 pytest 私有基线补入固定版本模块，并用独立容器实际复现与验收 #15436。此生成物不属于参考修复补丁。
- Trio #3578 的上游 PR 同时修改多个 NaN 行为；已裁成仅对 MockClock.jump 增加 NaN 检查，另写独立可见和隐藏用例。Trio #3261 的公开任务描述删去原报告披露的源码行与实现建议。两项均复跑稳定且独立评分接受。

- pytest #15337 在真实 Python 3.10.0 上，未修复 pytest 的会话启动即抛出 NodeId 属性错误、无法收集自身测试；失败日志已保留。为避免把收集失败当作 F2P，采用标准库 unittest 在同一锁定镜像中运行独立可见、隐藏和 P2P 三组用例，并验证参考补丁。
- AnyIO #1479 与 attrs #1575 使用 Python 3.14.7 镜像；Pydantic #14310 锁定 pydantic-core 2.50.0。缺失的 pytest 插件、jsonschema 与构建生成版本模块均按环境问题补齐，不计作缺陷复现。
- 评分器已将隐藏和 P2P 分别从干净基线重建，避免隐藏补丁改变 P2P 参数数目。attrs #1575 修正后 P2P 从旧评分记录的 5 项回到矩阵的 4 项，仍被接受；修正后已重跑 20 项参考补丁，20/20 接受，评分的隐藏与 P2P 用例数均与准入矩阵一致。

- 20 个单任务 Agent 导出已按各自基线加可见补丁生成；逐文件 SHA-256 对比全部导出与重建副本，20/20 一致，无私有补丁、隐藏测试或其他任务目录。

## Issue 与补丁审查

- [tomlkit #377](https://github.com/python-poetry/tomlkit/issues/377)：原报告给出两个子表的复现，没有源码级修复方案。参考源码补丁仅改超表判定；独立可见测试与上游隐藏回归测试分开。
- [AnyIO #1391](https://github.com/agronholm/anyio/issues/1391)：原报告包含具体源码诊断以及后续发送端问题，公开描述已去除诊断并限定接收端。参考补丁裁去 PR 的发送端代码；可见同流关闭和隐藏克隆关闭分别验证 asyncio、uvloop、eager、Trio。
- [Click #3362](https://github.com/pallets/click/issues/3362)：原报告指出底层换行参数，公开描述已去除该诊断。原 PR 还改动其他换行实现和旧测试；参考补丁仅保留达到此行为所需的两个换行参数。可见与隐藏使用不同的边界输入。

## 运行时隔离与独立评分验证

- **单次付费 LLM 验收（tomlkit #377，2026-11-27）已通过**：现有 `run_agent` 使用 `deepseek-flash` 完成 8 次模型调用、14 次工具调用，共 52,310 token；修复前公开测试失败，修复后通过。Agent 镜像 ID 为 `sha256:bc2f02466a80c68f1fb314c0074877a9c2e869c2d4dfdb3b6509d4802667e1ac`，完整 `pip freeze` 与私有锁文件一致。只挂载该任务公开源码、`app/`、公开 task/policy JSON 和本次日志；参考补丁、隐藏测试及其他任务未挂载。Agent 在 Docker 内部网络中仅可访问固定 `/chat/completions` 模型代理，直接连外网得到网络不可达；评分容器另用 `--network none`。
- Agent 生成的生产补丁 SHA-256 为 `318f8b3d70dcd36f611502427e19267d9ec7a7d045cec5dd77dd50444a6b7db4`。容器退出后才从工作区提取补丁，私有 Evaluator 在干净基线上分别运行隐藏 1 项和 P2P 1 项，均通过；`scoring/result.json` 判 `accepted=true`，`runtime_agent_probe/llm_acceptance_1/pipeline_result.json` 的 `final_success=true` 来自该判定。此次 Agent 恰好修复成功，但工程验收依据为完整执行与外部评分链路，不依赖 Agent 自报成功。
- 轨迹中的 `policy_violation_count=2` 均是达到探索预算后继续请求 `grep` / `read_file`，原有工具策略按预期阻止；Agent 随后完成补丁和验证。这两次阻止不涉及参考补丁或隐藏测试访问。
- pytest #15337 的首次 Agent 运行时探针在初始化 Git 工作区前失败：精确 Python 3.10.0 的 Evaluator 基础镜像未含 `git`。保留 `runtime_admission_1` 失败日志；只在该任务 Agent 覆盖镜像安装 Git，重新锁定镜像 ID / `pip freeze`，`runtime_admission_2` 已通过。原 Evaluator 镜像与有效性矩阵未变。
- Pydantic #14310 首次通用 Agent 镜像将任务锁定的 `pydantic-core 2.50.0` 降到 2.41.4，公开测试在收集阶段退出码 4；第二次恢复 core 导致 Harness 启动不兼容；第三次独立 Harness 虚拟环境误用其 Python 执行测试；第四次显式使用系统 Python 后仍受上游 benchmark `addopts` 干扰。失败日志均保留。第五次探针将 Harness 置于 `/harness`，测试使用原锁定系统 Python 并沿用矩阵的 `-o addopts=`，公开测试退出码 1 且定位到预期 Issue 用例。最终审计还确认系统侧完整依赖锁与原验证记录一致。

- 三个已知修复生产补丁在独立评分器上被接受。Click 的仅改注释补丁被隐藏测试拒绝；修改测试文件的候选补丁在执行前被路径门槛拒绝。
- 已从各基线加可见补丁生成单独 Agent 导出。20 个导出均无 `.git`、隐藏测试、参考补丁；运行时仅挂载单个任务导出，Agent 容器无法看到 Evaluator 路径。20 个任务的现有 Agent 入口均在隔离容器中实跑。
- 三个原试点还经 runtime_agent_probe.py 运行了现有 run_agent 规则 Agent 入口：分别使用独立 Agent 镜像、完整依赖锁、禁网只读容器和单任务公开挂载。三项可见测试在基线失败，规则 Agent 均未生成补丁，Evaluator 最终均判失败；不以 Agent 自报状态替代评分。Click 首次取 diff 遇 Windows 长路径，改为容器内短路径后复跑成功。与前述预设正确补丁接受记录合起来覆盖了正负两条无 LLM 路径。
- 旧 batch_runner 对新 real_full_ 任务现会拒绝走宿主机旧入口，避免误用 Agent 自报结果；原有任务入口保持原行为。回归测试 4/4 通过。
- 三个原试点已用 `runtime_smoke.py` 实跑无 LLM 端到端：容器只挂载单任务公开导出、`app/` 和本任务工作区，使用现有 Harness 工作区复制与可见测试工具；容器退出后才注入预设补丁，提交生产 diff 给独立 Evaluator。三个已知修复最终均被接受，Click 无效补丁最终被拒绝。Agent 阶段不可访问参考补丁、隐藏测试和其他任务；这一证明限于预设 Patch 烟测路径。

## 冻结与运行边界

- `copy_repo_to_workspace` 增加默认行为不变的 `install_editable=False` 入口，供锁定容器路径避免宿主进程级安装。真实 LLM 试点的模型通信、工具调用、单任务容器与外部评分已实跑验收；其余 19 项已完成禁网单任务 Agent 入口探针。各任务 Agent 镜像 ID 与完整依赖锁已保存在私有目录。
- 原 Issue 风险见 [candidate_triage.md](candidate_triage.md)。pytest #15370 的报告明确由 AI coding agent 起草，但人类帐号提交；pytest 维护者 RonnyPfannschmidt 发起并审核 AI 辅助 PR，另一维护者批准并合入。marshmallow #2869 由学术自动测试工具发现，报告者人工核实，维护者确认诊断并批准合入另一作者的 PR。两项均为真实上游接受且可独立复现的缺陷；来源情况已人工审查并保留，不因报告文字的撰写方式直接淘汰。
- 旧批量入口对历史任务仍使用进程 Python 的 editable 安装和 Agent 自报结果；新 `real_full_` 任务已封锁该入口，运行时需走单任务容器与私有 Evaluator。20 个 `audit.json` 均在最终证据核对后生成，八项准入门槛全为真；`register.py` 已写出冻结 Manifest。首次注册受 Windows MAX_PATH 影响失败并自动清理，采用长路径复制后完成。
