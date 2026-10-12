# 面试准备：LLM 机制层知识补法

> 目标：将已有系统层知识挂接到机制层语言上，三天量级补齐面试短板。

---

## 一、四层模型

### L0 · 基底：next-token prediction

LLM 只做一件事——给定 token 序列，输出下一个 token 的概率分布（logits → softmax），然后采样（temperature/Top-p 控制随机性）。跨 API 调用**完全无状态**：没有记忆、没有进度感、没有“任务”概念。一切“理解”来自参数（预训练权重）和当前 context（输入序列）。

**关键推论**：
- 模型不会“记住”上一轮对话——是 agent 框架把对话历史拼接后重发
- 模型不知道已经调用了多少轮——轮次计数和 budget 是 runtime 的事
- KV cache 只在同一次请求内复用，跨请求不保留

### L1 · 表示：tokenizer

一切输入——自然语言、代码、JSON——切分为 token 序列。代码**没有特殊地位**：无 AST、无语法树、无编译器参与。

**代码相关的要点**：
- BPE 分词，长标识符会被拆碎（模型可能分不清 `user_id_count` 和 `user_id_counter`）
- 缩进空格可能合并为特殊 token
- 数字和行号对模型来说只是普通 token，无语义

### L2 · 协议：chat template + tool_calls

模型输出被 chat template 组织为结构化的角色消息（system / user / assistant / tool）。function calling 本质是模型生成特定格式的 token 序列，由 runtime 解析为 `tool_calls` 结构体。

**关键事实**：
- `tool_calls` 是**生成的文本**，`arguments` 字段是逐 token 拼出的 JSON——会坏
- `finish_reason` = `stop`（正常结束）、`length`（被 max_tokens 截断）、`tool_calls`（请求执行工具）
- 严格的 API（如 DeepSeek）要求 assistant(tool_calls) 和 tool result 必须配对，否则 400

### L3 · 后训练：为何“听话”

- **预训练**（爬虫数据）给模型能力：语言统计规律、代码模式、推理雏形
- **SFT**（指令-回答对）让模型学会遵循指令格式
- **RLHF** 让模型偏好符合人类期望的输出
- **Function-calling 微调**：在 SFT 阶段混入 tool_call 格式的训练数据，让模型学会何时以及如何输出结构化调用

---

## 二、挂接表（系统组件 ↔ 机制层事实）

| 基底事实 | 所在层 | 你的设计 |
|---|---|---|
| LLM 跨调用无状态，无进度感 | L0 | `AgentState`（`memory.py`）在 runtime 侧持有状态；phase 由 `next_phase_after_tool()` 确定性状态机推进，**不由模型自述** |
| context 有限；注意力随长度稀释，中间内容优先丢失 | L0/L1 | `code_locator` 三段检索（Recall→Expand→Rerank）；`_microcompact_messages` 截断超长工具输出；`_compress_messages_if_needed` 摘要压缩；ADR-0002 token 预算校准 |
| 输出是概率采样，“合理”≠“正确” | L0 | `patcher`（确定性应用）、`verifier`（语法/测试检查）、success 判定三条件（patch + diff + tests） |
| tool_calls 是生成的文本，arguments 会非法 | L2 | `_recover_text_tool_blocks` 从纯文本恢复；`finish_reason` 可观测性注释；编辑结果反映到 `tool_result.content` |
| 模型会陷入重复行为分布（编辑无进展时重写同一文件） | L0 | 反循环检测（`_detect_repeated_write_loop` + `SequenceMatcher`）；读节流（5 次读后注入提醒）；`budget_escalation` 探索工具物理移除 |
| token 成本超线性（每轮重发全历史） | L0/L1 | 只读局部上下文（system prompt P0：±30 行）；schema 按 phase 过滤（`build_tools_for_state`），减少每轮发送的 token 量 |
| 模型无符号执行能力，幻觉 API | L0/L1 | `python_repl` 受控表达式验证假设；`run_tests` 提供事实证据而非推测 |

---

## 三、自测六问

面试前脱稿回答以下问题，每个控制在 1 分钟内：

1. **从 token 到 token 的循环**：logits → softmax → 采样（temperature/Top-p）→ 新 token 拼回序列 → 继续。temperature 控制随机性：低更确定、高更多样。

2. **为什么跨请求无记忆？KV cache 是什么？** 模型权重不变，每次请求输入独立。KV cache 是注意力计算中 key/value 的预计算缓存，只在同一次请求的 token 序列内复用，跨请求不保留。对话历史记忆靠 agent 框架拼接。

3. **function calling 训练侧和推理侧的区别？** 训练侧：SFT 数据含带 tool_calls 格式的 assistant 消息，微调后模型学会输出这种格式。推理侧：chat template 注入工具 schema → 模型生成 tool_calls 文本 → runtime 解析、执行、回注结果。

4. **代码进 tokenizer 发生什么？** 被 BPE 算法切为 token 序列。`def foo():` 可能是 3-5 个 token。空格和缩进有独立 token。长标识符被拆碎。无 AST——模型通过注意力“数”括号和缩进。

5. **context 与 attention 成本？lost in the middle 是什么？** attention 复杂度 O(n²)，context 翻倍成本翻 4 倍。位置编码和注意力稀释导致序列中部信息最容易被忽略——模型对开头和结尾更敏感。

6. **pretraining vs post-training 各给什么？** 预训练给能力（语言建模、代码统计规律），后训练给行为（遵循指令的格式、function calling 的时机、人类偏好对齐）。

---

## 四、学习资源（优先级排序）

1. Karpathy, *[Intro to Large Language Models](https://www.youtube.com/watch?v=zjkBMFhNj_g)*（1h，直觉层）
2. Karpathy, *[Let's build GPT: from scratch, in code, spelled out](https://www.youtube.com/watch?v=kCc8FmEb1nY)*（2h，动手理解 token→token 循环）
3. 3Blue1Brown, *[Attention in transformers, visually explained](https://www.youtube.com/watch?v=eMlx5fFNoYc)*（25min，可视化）
4. [DeepSeek API 文档 · 工具调用](https://api-docs.deepseek.com/zh-cn/guides/function_calling)（你在用的，读一遍机制说明）
5. [OpenAI · Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)（协议规范参考）

---

## 五、使用方式

**面试前一天或当天早上的快速复习路径**：

1. 扫一遍四层模型（5 分钟）
2. 眼过挂接表，找 2-3 个自己有信心的组件做脱稿串联（10 分钟）
3. 看自测六问，确保每个能 30 秒答出核心句（10 分钟）

**面试中的叙事节奏**：

> 面试官问机制 → 答机制事实（一层怎么说的）→ 立刻接“所以我的系统里用 X 组件解决了这个问题”

记住：你不是在背知识点，你是在证明——**我系统的每一行代码都有机制层的理由。**