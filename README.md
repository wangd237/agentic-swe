# Agentic SWE

<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python"></a>
<a href="https://docs.pydantic.dev/"><img src="https://img.shields.io/badge/Pydantic-v2-purple?logo=pydantic&logoColor=white" alt="Pydantic"></a>
<a href="https://docs.pytest.org/"><img src="https://img.shields.io/badge/pytest-tested-blue?logo=pytest&logoColor=white" alt="pytest"></a>
<a href="https://platform.openai.com/"><img src="https://img.shields.io/badge/OpenAI_Compatible-API-purple?logo=openai&logoColor=white" alt="OpenAI Compatible"></a>
<a href="#"><img src="https://img.shields.io/badge/Tool_Calling-enabled-green" alt="Tool Calling"></a>
<a href="#"><img src="https://img.shields.io/badge/CLI-supported-gray" alt="CLI"></a>
<a href="#"><img src="https://img.shields.io/badge/JSON_Trace-auditable-orange" alt="JSON Trace"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green" alt="MIT"></a>

面向真实 Python 代码仓库的 **Coding Agent**。输入 Bug 描述或 GitHub Issue，Agent 在独立工作区中完成代码定位、补丁修改和测试验证，输出可审计的修复结果。

项目重点在 **Agent Harness / Runtime**：工具调用约束、阶段状态管理、自动验证、上下文管理与执行轨迹，而非单次代码生成。

## 核心架构

```text
Issue / Task
     │
     ▼
Runtime / Harness ── 创建独立 Workspace、加载 Policy、记录 Trace
     │
     ▼
LLM Agent Loop
     │  UNDERSTAND → REPRODUCE → LOCALIZE → PATCH → VERIFY → FINAL
     │
     ├── AgentState / ToolPolicy ── 阶段约束、写入门禁、工具权限
     ├── Tool Router / Validator ── 按阶段暴露工具、校验调用参数
     ├── Tool Executor ─────────── 读文件、搜索、编辑、测试、Diff、Undo
     ├── Verification / Reflection ── 补丁后验证、失败反馈、必要时回滚
     └── Context Manager ──────── Token 预算、工具结果裁剪、历史摘要
     │
     ▼
Patch + Result + Trace + Message Journal
```

**关键机制**

- **受控工具调用**：根据阶段和状态筛选工具 Schema；通过参数校验和 `ToolPolicy` 执行权限、写入前证据及验证顺序约束。
- **修复—验证闭环**：代码修改后由 Runtime 检查 Diff、运行测试；失败时结合错误签名生成 Reflection，支持 Undo；验证充分时可自动结束。
- **上下文管理**：按 Token 预算触发压缩；对较早历史使用 LLM 结构化摘要（失败时规则降级），保留最近消息和工具调用/结果配对。
- **可追溯执行**：`messages.jsonl` 追加记录模型可见消息的变化及压缩事件，`trace.json` 保存执行与验证信息，完整的大工具结果可单独落盘。
- **可选代码结构检索**：支持接入 `codebase-memory-mcp` 辅助定位；非必需，未配置时可使用普通文件检索。

## 快速开始

**环境要求**：Python 3.10+、Git；LLM 需提供兼容 OpenAI Chat Completions 的接口。目标项目的测试依赖需要提前安装。

### 1. 安装依赖

```bash
git clone https://github.com/wangd237/agentic-swe.git
cd agentic-swe
python -m pip install -r requirements.txt
```

复制配置模板为 `.env`（Windows PowerShell：`Copy-Item .env.example .env`；Linux/macOS：`cp .env.example .env`），填写：

```dotenv
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
LLM_CONTEXT_WINDOW_TOKENS=65536
```

以上是配置格式示例。请根据所用模型填写实际地址、名称和**真实上下文窗口**；不要提交 `.env` 或 API Key 到仓库。

### 2. 修复 Bug

**方式 A：本地仓库**（当前 CLI 要求目标仓库位于本项目目录内）：

```bash
python scripts/repair_bug.py --repo path/to/repo --issue "描述问题及预期行为" --test "python -m pytest -q" --policy optimization/policy_versions/llm_openai_compatible_template.json
```

**方式 B：公开 GitHub Issue**（自动获取 Issue 并 Clone 目标仓库）：

```bash
python scripts/repair_bug.py --issue-url https://github.com/owner/repo/issues/123 --test "python -m pytest -q" --policy optimization/policy_versions/llm_openai_compatible_template.json
```

`--test` 可省略，程序会尝试发现 pytest；缺少有效测试时可能只能进行较弱验证。正式使用建议传入准确的测试命令。

`repair_bug.py` 会对 pytest 做依赖/测试收集预检。Agent 修改的是隔离 Workspace，**不会自动 Push、创建 PR 或直接修改上游仓库**。运行前请确认模型服务的数据处理要求，代码和工具结果可能发送给配置的 LLM 服务商。

### 3. 运行内置任务（可选）

```bash
python scripts/run_issue_agent.py --task benchmarks/tasks/task_010.json --policy optimization/policy_versions/llm_openai_compatible_template.json
```

## 配置

- **模型连接**：在 `.env` 设置 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 和 `LLM_CONTEXT_WINDOW_TOKENS`。
- **运行策略**：在 `optimization/policy_versions/*.json` 设置 `max_steps`、工具/验证策略及上下文压缩参数。入门建议使用 `llm_openai_compatible_template.json`，无需代码图后端。
- **摘要压缩（可选）**：可以在已有 Policy JSON 中加入以下字段：

```json
{
  "llm_compaction_mode": "llm",
  "llm_compaction_trigger_tokens": 32000,
  "llm_compaction_max_output_tokens": 2048
}
```

三个参数分别表示：使用 LLM 摘要、达到约 32K 输入 Token 时尝试压缩、单次摘要最多输出 2048 Token。有效触发阈值还受模型窗口和预留 Token 限制；如不指定软阈值，则主要依据窗口预算判断。设置 `"llm_compaction_mode": "rules"` 可改用规则压缩。配置详情见 [上下文管理说明](docs/session_context_compaction.md)。

## 运行产物

每次运行创建 `logs/trajectories/<task_id>/<run_id>/`：

| 文件 | 用途 |
| --- | --- |
| `task.json` | 任务输入 |
| `result.json` | 最终状态与验证结论 |
| `trace.json` | 阶段、工具调用、证据与指标 |
| `messages.jsonl` | 追加式消息日志、上下文替换与压缩记录（LLM Agent） |
| `patch.diff` | 代码变更 |
| `summary.md` | 人类可读的运行总结 |
| `tool_outputs/` | 超大工具结果的完整记录（如有） |

`messages.jsonl` 可以回放模型可见的消息历史，**但目前不支持进程中断后完整恢复 Agent 的工作区与执行状态**。修复是否可信应以 `result.json` 中的验证证据为准，而不只是模型报告成功。

## 项目结构

```text
app/
  agent/          # LLM Agent Loop、阶段编排、Reflection、终结处理
  core/           # AgentState、PolicyConfig
  llm/            # API 适配、模型配置、上下文压缩
  tools/          # Tool Schema、Router、Validator、Policy、Executor、内置工具
  verification/   # 自动验证、证据质量与最终判定
  runtime/        # Workspace、Git 操作、消息日志、任务生命周期
  codebase/       # 代码定位与可选结构检索
  schemas/        # Task / Trace / Result 类型
scripts/          # CLI 入口与评测脚本
optimization/     # Policy 配置
benchmarks/       # 测试任务及数据
evals/            # 批量评测与对比
docs/             # 设计与使用文档
```

## 开发与测试

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
```

评测与回归实验详见 [评测说明](docs/agent_eval_summary.md)。

## License

MIT
