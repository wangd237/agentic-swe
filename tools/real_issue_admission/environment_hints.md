# 上游依赖核查（候选环境，不是 lock）

依据 GitHub 上各仓库指定候选 Base Commit 的 `pyproject.toml`。每个任务仍需检查其独立 Base 中的依赖声明并锁定环境。

| 仓库 | Python 约束 | 测试依赖/构建线索 | 建议候选 Python |
|---|---|---|---|
| packaging | >=3.8 | dependency-groups.test: coverage[toml], pip, pretend, pytest, tomli/tomli_w；flit_core>=3.12 | 3.12 |
| tomlkit | >=3.8 | poetry-core>=1.0.0a9；检查各版本 poetry 测试组 | 3.12 |
| AnyIO | >=3.11 | test group: blockbuster, coverage, hypothesis, psutil, pytest>=9, pytest-mock, pytest-timeout, trustme, truststore；可选 trio/uvloop；setuptools-scm | 3.13 |
| pytest | >=3.10 | dev group: pytest[dev]；setuptools>=77、setuptools-scm[toml]>=10.1 | 3.12；#15337 优先 3.10.0 |
| fsspec | >=3.10 | test extra: HTTP、numpy、pytest、requests、pytest-benchmark、pytest-cov、pytest-mock、pytest-recording、pytest-rerunfailures、pytest-asyncio；hatch-vcs | 3.12 |
| Trio | >=3.10 | setuptools>=77；从对应 Base 读取测试依赖及 pytest 配置 | 3.12 |
| attrs | >=3.9 | tests group: cloudpickle、hypothesis、pympler、pytest、pytest-xdist[psutil]；hatch-vcs | #1575 需 3.14 |
| Click | >=3.10 | tests group: pytest；flit_core>=3.11,<4 | 3.12 |
| Marshmallow | >=3.10 | tests extra: pytest、simplejson；flit_core<4 | 3.12 |
| Pydantic | >=3.11 | pydantic-core==2.50.0（该 Base 声明）；dev group 含 pytest、dirty-equals、pytest-mock 等；hatchling | 3.13，检查 core wheel/源码构建要求 |

建议环境：Linux x86_64 容器优先，具体版本应匹配原始复现条件。对 `setuptools-scm` / `hatch-vcs` 动态版本项目，移除原 Git 历史后可能无法正确推导版本。先在 Evaluator 侧的真实 checkout 中核实版本，使用受控构建配置或离线 wheel；不要为方便安装而随意伪造版本或将修复后的源码装入测试环境。`build_env` 仅用于记录经过核实的必要构建变量。运行 Agent 前验证其 Python、依赖锁和被导入的源码实际一致。
