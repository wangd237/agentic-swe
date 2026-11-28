# 其余 17 个候选的 Issue 审核队列

2026-11-27 基于固定 GitHub Issue、候选补丁和实际矩阵。此表记录来源风险，**不代表完整准入**。20 个候选的补丁哈希、`git apply --check` 和 gitlink 完整性预检均通过。

| 候选 | 原报告与风险 | 下一步 |
|---|---|---|
| [Requests #6711](https://github.com/psf/requests/issues/6711) | 真实 S3 用户报告，URL 双斜杠影响签名；替换 packaging #938。旧 [#6643](https://github.com/psf/requests/issues/6643) 普通 HTTP 用例存在语义重叠。 | 两轮矩阵及独立评分通过；另设回环 HTTP P2P 验证旧用例仍能实际请求成功。 |
| [tomlkit #381](https://github.com/python-poetry/tomlkit/issues/381) | 真实 Pipfile 损坏报告。 | 首轮矩阵已通过；复跑、评分和隔离检查。 |
| [tomlkit #411](https://github.com/python-poetry/tomlkit/issues/411) | 真实嵌套 dotted key 复现。 | 复用 tomlkit 镜像；配置已完成，待六格实测。 |
| [AnyIO #1466](https://github.com/agronholm/anyio/issues/1466) | 明确的 asyncio socket 关闭后缓存读取症状；报告说明内部队列。 | 公开描述去内部实现，独立可见测试和隐藏上游回归。 |
| [AnyIO #1479](https://github.com/agronholm/anyio/issues/1479) | 报告含异常处理源码诊断，原复现 Python 3.14.7。 | 已用 Python 3.14.7 与固定插件完成两轮矩阵及独立评分。 |
| [pytest #15436](https://github.com/pytest-dev/pytest/issues/15436) | 真实 fixture 生命周期回归复现。 | 两轮矩阵与独立评分通过；独立可见 fixture 图、隐藏上游两个参数，固定 Python 3.12.16。 |
| [pytest #15370](https://github.com/pytest-dev/pytest/issues/15370) | 报告明确由 AI coding agent 生成；真实用户使用来源未确证。 | 暂列高风险，先查独立用户证据；否则用储备候选替换。储备 [Requests #6711](https://github.com/psf/requests/issues/6711) 有真实 S3 用户报告和 [PR #7315](https://github.com/psf/requests/pull/7315)，但 PR 反转了此前 `//` 路径测试，须审核 #6643 行为重叠后才能替换。 |
| [pytest #15337](https://github.com/pytest-dev/pytest/issues/15337) | 报告披露 Python slotted dataclass 根因。 | 已用精确 Python **3.10.0** 复现 pytest 启动崩溃；标准库 unittest 完成两轮矩阵与评分。 |
| [fsspec #2311](https://github.com/fsspec/filesystem_spec/issues/2311) | 真实 ZIP/simplecache 发布延迟，原报告含环境与导入路径证据。 | 锁定缓存/ZIP 依赖，验证关闭前后目标可见性。 |
| [fsspec #2456](https://github.com/fsspec/filesystem_spec/issues/2456) | 原报告点名失败上传后的状态复位实现。 | 去根因化描述，测试一次失败后新写入能立即上传。 |
| [fsspec #2266](https://github.com/fsspec/filesystem_spec/issues/2266) | 内存文件系统 `makedirs(exist_ok=True)` 接受已有文件。 | 独立文件/目录复现并保留相关 P2P。 |
| [Trio #3261](https://github.com/python-trio/trio/issues/3261) | 原报告链接精确源码行和建议实现。 | 已删减公开描述；两轮矩阵与独立评分通过，分别验证 cause 与 cause/context。 |
| [Trio #3578](https://github.com/python-trio/trio/issues/3578) | MockClock NaN 复现；修复 PR 还包含其他 NaN 改动。 | 已裁成仅 MockClock.jump 的 NaN 检查；两轮矩阵与独立评分通过。 |
| [attrs #1575](https://github.com/python-attrs/attrs/issues/1575) | Python 3.14 下未导入 `ClassVar` 的真实复现。 | 已用 Python 3.14.7 完成两轮矩阵及独立评分。 |
| [marshmallow #2869](https://github.com/marshmallow-code/marshmallow/issues/2869) | 作者称由学术自动测试工具发现并人工核实，正文给出实现细节。 | 两轮矩阵及独立评分通过；冻结前仍须判断自动发现来源是否符合门槛，不符则替换。 |
| [marshmallow #2900](https://github.com/marshmallow-code/marshmallow/issues/2900) | 真实 OpenAPI `Constant(required=True)` 用例，但报告直接建议修复。 | 隐去建议并单独验证公开症状与隐藏测试。 |
| [Pydantic #14310](https://github.com/pydantic/pydantic/issues/14310) | 真实 2.14 泛型别名回归，traceback 暴露内部调用。 | 锁定 Python 与 `pydantic-core` 精确版本，公开描述去内部栈。 |

20 项行为矩阵已通过；来源风险不能通过脚本自动置位，运行时隔离和最终 Evaluator 判定仍待验收。

**淘汰记录**：[packaging #938](https://github.com/pypa/packaging/issues/938) 的自写可见/隐藏测试与上游新增的全部 6 个回归参数，在固定修复前基线均通过；F2P 门槛失败。已从 20 候选目录移除，保留私有失败日志，不把其上游测试伪称为缺陷复现。
