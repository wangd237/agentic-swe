# Agent Case Studies

本文档只保留 4 条最适合面试讲述的 LLM agent 案例。每条都对应真实运行产物：`trace.json`、`result.json`、`patch.diff`。

## Case 1: `task_010` Rich ANSI CRLF Parsing

**来源**：`Textualize/rich#4090`  
**run**：`logs/trajectories/task_010/run_20260614T080459321811Z_6319`  
**结果**：`success`，`6` tool calls，修改 `rich_ansi_repo/ansi.py`

### 问题

旧实现把 CRLF 中的 `\r` 当作终端回车覆盖符处理，导致普通 Windows 换行文本被误解析。目标是保留 ANSI parser 对回车覆盖的支持，同时不要破坏普通 `\r\n` 行尾。

### 决策链

- 第 1 轮：agent 先列出文件并读取 `rich_ansi_repo/ansi.py`，确认问题在 ANSI 解码路径，而不是测试夹具。
- 第 2 轮：读取 `tests/test_ansi.py` 后，agent 发现失败输入是普通 CRLF 文本，不是动态终端覆盖场景。
- 第 3 轮：agent 选择在 `AnsiDecoder.decode_text()` 入口归一化 `\r\n`，而不是删除 `decode_line()` 对裸 `\r` 的处理，因为后者仍是终端语义需要的行为。
- 第 4 轮：修改后运行目标测试，再用 diff 留下可审计 patch。

### Patch

```python
terminal_text = terminal_text.replace("\r\n", "\n")
```

证据：

- `logs/trajectories/task_010/run_20260614T080459321811Z_6319/trace.json`
- `logs/trajectories/task_010/run_20260614T080459321811Z_6319/result.json`
- `logs/trajectories/task_010/run_20260614T080459321811Z_6319/patch.diff`

### 为什么值得讲

这是项目从 rule-based solver 转向 LLM tool-use agent 后的第一类核心能力：agent 不是直接猜 patch，而是读实现、读测试、保留原有终端语义，再做最小入口修复。

## Case 2: `task_024` Jinja Static Analysis

**来源**：`pallets/jinja#2069`  
**run**：`logs/trajectories/task_024/run_20260614T113402398598Z_5993`  
**结果**：`success`，`6` tool calls，修改 `jinja_meta_repo/meta.py`

### 问题

模板变量在所有分支里都被 `set` 后，静态分析仍错误地把它报告为 undeclared。旧实现先把分支赋值变量加入 `assigned_variables`，随后又用一个反向循环把这些变量重新塞回 `undeclared`。

### 决策链

- 第 1 轮：agent 读取 `meta.py`，先建立 `used_variables`、`assigned_variables`、`undeclared` 三者关系。
- 第 2 轮：读取测试后，agent 识别到这是控制流语义问题，不是某个变量名的 special case。
- 第 3 轮：agent 没有新增复杂条件，而是删除和前面集合语义冲突的循环，让 `undeclared = used - assigned` 成为唯一规则。
- 第 4 轮：运行测试确认回归通过。

### Patch

```python
undeclared = {name for name in used_variables if name not in assigned_variables}
return undeclared
```

证据：

- `logs/trajectories/task_024/run_20260614T113402398598Z_5993/trace.json`
- `logs/trajectories/task_024/run_20260614T113402398598Z_5993/result.json`
- `logs/trajectories/task_024/run_20260614T113402398598Z_5993/patch.diff`

### 为什么值得讲

这个案例不是边界值 if 修补，而是需要理解静态分析数据流。它证明 agent 能把测试失败映射到算法不变量：声明变量集合不能又被重新标记成未声明。

## Case 3: `task_132` Rich Windows Encoding

**来源**：`Textualize/rich#2411`  
**突破 run**：`logs/trajectories/task_132/run_20260615T053443547474Z_9294`  
**结果**：`success`，`13` tool calls，修改 `rich_windows_rule_repo/console.py`

### 问题

Windows-like legacy encoding stream 无法输出 box drawing rule 字符 `─`。目标行为是：UTF-8 流保留 Unicode，旧编码流稳定降级为 ASCII `-`，而不是泄漏不可编码字符或使用 replacement char。

### 决策链

- 早期 run 多次停在 `incomplete/no_patch`：测试已经绿但没有 patch，系统没有误报 success。这暴露了“测试绿但无实际修复”的边界。
- 压力测试阶段重新运行后，agent 读取 `console.py` 和 `tests/test_console.py`，定位到 `_safe_text_for_encoding()` 的 fallback 分支。
- agent 选择保留“先替换 box drawing 字符为 `-`”的策略，只修正最后一步：如果 fallback 仍需要 `errors="replace"`，也应该 encode/decode fallback text，而不是退回原始 Unicode text。
- 最终 patch 只改一行，并通过目标测试。

### Patch

```python
return fallback_text.encode(encoding, errors="replace").decode(encoding)
```

证据：

- 早期 no-patch run: `logs/trajectories/task_132/run_20260615T053313434663Z_7142/result.json`
- 突破 run: `logs/trajectories/task_132/run_20260615T053443547474Z_9294/result.json`
- patch: `logs/trajectories/task_132/run_20260615T053443547474Z_9294/patch.diff`

### 为什么值得讲

这个案例同时展示了两件面试官会关心的事：agent 能突破历史 hard case；系统也足够保守，不会把“没有 patch 的测试通过”包装成成功。

## Case 4: `task_048` Packaging Version Semantics

**来源**：`pypa/packaging#810`  
**Target 2 run**：`logs/trajectories/task_048/run_20260615T074619354360Z_6882`  
**结果**：`success`，`11` tool calls，修改 `packaging_specifier_repo/specifiers.py`

### 问题

`Specifier.contains()` 处理 `dev+local` 版本时使用 `Version.base_version`。模型之前一直在脑内模拟 `packaging.Version` 行为，误以为 `base_version` 会保留 dev 段，最终 hit `max_iterations`。

### 决策链

- 第 1 轮：agent 读取实现和测试，先给出错误假设：以为 `base_version` 会保留 `a2.dev1235`。
- 第 2 轮：`run_tests` 失败后，agent 没有继续猜，而是调用新工具 `python_repl` 查询真实行为。
- 第 3 轮：`python_repl("str(Version(\"4.1.0a2.dev1235+local\").base_version)")` 返回 `'4.1.0'`，推翻原假设。
- 第 4 轮：agent 继续查询 `.public`，得到 `'4.1.0a2.dev1235'`，确认应该比较去掉 local 但保留 prerelease/dev 的 public version。
- 第 5 轮：agent 用 `Version(prospective_version.public) > self.spec_version` 做最小修复，并通过 4 个测试。

### Patch

```python
if prospective_version.local is not None:
    return Version(prospective_version.public) > self.spec_version
```

证据：

- 失败基线: `logs/trajectories/task_048/run_20260615T064450000602Z_7854/result.json`
- 成功 run: `logs/trajectories/task_048/run_20260615T074619354360Z_6882/result.json`
- trace: `logs/trajectories/task_048/run_20260615T074619354360Z_6882/trace.json`
- patch: `logs/trajectories/task_048/run_20260615T074619354360Z_6882/patch.diff`

### 为什么值得讲

这是 Target 2 最强证据：agent 不再把第三方库语义放在脑内猜，而是通过受控 `python_repl` 查询事实，再把事实转化成 patch。这个能力比单纯提高成功率更接近真实 SWE agent。

## Target 2 Validation Snapshot

| Task | 验证点 | Before | After |
| --- | --- | --- | --- |
| `task_048` | `python_repl` 打破领域库盲区 | `incomplete/max_iterations`, no patch | `success`, 11 calls |
| `task_030` | `context_diff` 帮助修格式精度 | 曾 13 calls hit `max_iterations` | `success`, 12 calls，失败摘要含 `context_diff` |
| `task_089` | 回归基线不退化 | `success`, 7 calls | `success`, 6 calls |

结论：Target 2 的 5 项改进不是“功能清单”，而是在三条代表任务上转化成了真实行为提升。
