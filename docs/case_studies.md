# 精选案例

这份文档不再按“每个版本过了哪一题”平铺罗列，而是只保留最能说明系统能力、优化方法和当前边界的 5 个案例。

如果你需要查看早期完整流水账，请看归档版本：

- [docs/case_studies_archive_v1.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/case_studies_archive_v1.md)

## 案例 1：模板控制流分析不是简单字符串替换

**来源**：`pallets/jinja#2069`  
**任务**：`task_024`  
**缺陷类型**：模板变量控制流分析  
**难度**：`medium`

### 背景

这个问题的关键不在于“某个 if 条件写错了”，而在于模板分析器对控制流的理解退化了。对于一个变量，如果它在 `if / elif / else` 的所有分支里都已经被 `set`，那么后续再读取它时，不应该再被判成 undeclared。这个场景很适合检验 agent 是否具备最小但真实的语义理解能力，因为它需要看到“每个分支都赋值”这一事实，而不是只做局部文本替换。

### Agent 的执行过程

任务定义里已经把目标文件收敛到 `jinja_meta_repo/meta.py`。旧实现先把所有分支里出现过的变量做并集，再错误地把所有被使用过且在并集中出现的变量重新加入 `undeclared` 集合，导致 `output` 即使在所有分支都已赋值，也会被误报。对应的 `improved_v11` 在 [app/agent/patcher.py](/E:/My_Projects/agentic-software-engineering-roadmap/app/agent/patcher.py) 中引入了 `_handle_branch_assigned_undeclared` 规则，把逻辑改成先求所有分支赋值集合的交集 `all_branch_assigned`，再跳过这些变量。

### 结果

修复后，`MetaTests.test_branch_assigned_variable_is_not_undeclared` 不再失败，`task_024` 成为 `improved_v11` 的代表性通过案例之一。它说明当前系统已经不仅能处理“边界值 if 判断”，也能覆盖一部分轻量控制流语义问题。

### 启示

这个案例说明，semi-real benchmark 的价值不只是让 agent 改一行代码，而是能在可控范围内逼近真实框架语义。对后续扩容来说，这类“需要一点程序语义理解、但不至于变成完整编译器问题”的任务非常有代表性。

## 案例 2：继承链上的 validator 合并体现了框架机制理解

**来源**：`pydantic/pydantic#9582`  
**任务**：`task_057`  
**缺陷类型**：继承链上的 model validator 合并  
**难度**：`medium`

### 背景

这个问题比普通的函数 bug 更接近框架内部行为：父类和子类都定义了 `model_validator(mode="after")`，但旧实现里子类一旦声明自己的 validator，就会把父类整个校验链覆盖掉。这样的缺陷不是简单的空值判断，也不是局部渲染错误，而是框架元编程和继承行为上的语义回归。

### Agent 的执行过程

最小复现代码位于 `pydantic_inheritance_repo/models.py`。`BaseModel.__init_subclass__` 会收集本类 `after` validator 名称，同时读取继承来的 `__model_validator_names__`。旧逻辑使用 `merged_after = own_after or inherited_after`，这意味着只要子类有自己的 validator，就完全忽略父类链路。`improved_v28` 在 [app/agent/patcher.py](/E:/My_Projects/agentic-software-engineering-roadmap/app/agent/patcher.py) 中引入 `_handle_pydantic_inherited_model_validators`，把合并逻辑改成“父类在前，子类追加在后”，保证 `ParentModel` 和 `ChildModel` 的 after-validator 都继续执行。

### 结果

修复后，`ModelValidatorInheritanceTests.test_child_model_runs_parent_and_child_validators` 通过，父类独立校验路径也没有回归。它是当前任务集里比较能体现“理解框架机制”的案例，因为修复点并不是业务函数，而是类构建阶段的 validator 注册逻辑。

### 启示

这个案例说明系统已经开始触及“类定义期行为”而不只是“运行时边界值”。如果后续要继续增强 benchmark 的代表性，继承、注册表、descriptor、hook 链这类轻量框架机制问题是很值得继续补的方向。

## 案例 3：一行 patch 也能体现恰到好处的理解

**来源**：`psf/requests#6432`  
**任务**：`task_006`  
**缺陷类型**：依赖约束上界放宽  
**难度**：`medium`

### 背景

这道题表面上非常“小”：只是把 `urllib3` 的上界从 `<1.27` 放宽到 `<3`。但它之所以适合作为 benchmark，不在于改动行数，而在于 agent 是否能理解这是依赖管理语义问题，而不是去误改测试、误删约束或顺手把其它依赖也一并改掉。

### Agent 的执行过程

任务目标集中在 `setup.py`。旧实现保留了 `\"urllib3>=1.21.1,<1.27\"`，因此 `urllib3 2.x` 在 Python 3.7+ 环境下无法被接受。`improved_v3` 在 [app/agent/patcher.py](/E:/My_Projects/agentic-software-engineering-roadmap/app/agent/patcher.py) 中通过 `_relax_urllib3_upper_bound` 精准替换这一行，避免把问题扩大成“重写整个依赖列表”的粗暴修复。这个案例也很能说明当前 patch strategy 的工程取向：优先做最小、可证伪、可回归验证的改动。

### 结果

修复后，`DependencyConstraintTests.test_urllib3_v2_is_allowed_for_python37_plus` 通过，`task_006` 成为项目正式接入真实 issue 方向后的第一个代表性成功案例之一。

### 启示

好的 benchmark 不一定需要“大改代码”。像这种一行 patch 的任务，恰好可以验证 agent 有没有“只改必要部分”的克制能力。对于求职或展示来说，这类案例也很有说服力，因为它体现的是判断力，而不是堆 patch。

## 案例 4：失败到成功的优化故事比单次通过更能说明方法论

**来源**：`python-jsonschema/jsonschema#1121`  
**任务**：`task_036`  
**缺陷类型**：异常回落与普通校验失败语义分离  
**难度**：`medium`

### 背景

这个问题是早期优化路径里很典型的一类。对于空字符串 hostname，旧实现会在 `_split_hostname_labels` 阶段直接抛出 `ValueError`，导致格式检查函数中断执行；但真实期望不是抛异常，而是像普通非法 hostname 一样返回 `False`。这类问题非常适合做“失败到成功”的优化案例，因为它往往不是 patch 写错，而是系统还没有覆盖某一类错误语义。

### Agent 的执行过程

最小代码在 `jsonschema_hostname_repo/hostname.py`。旧实现先调用 `_split_hostname_labels(value)`，而这个辅助函数在 `value == ""` 时直接抛出异常。`improved_v17` 在 [app/agent/patcher.py](/E:/My_Projects/agentic-software-engineering-roadmap/app/agent/patcher.py) 中引入 `_handle_jsonschema_hostname_value_error`，把格式检查改成在这类输入上回落到普通失败，避免异常穿透到调用方。这个优化不是只解决一条任务，而是形成了“把底层异常映射回用户态失败语义”的一类方法。

### 结果

`task_036` 在 `improved_v17` 后进入稳定通过状态，并且后续在冻结集验证里一直保住了成功。它也因此成为项目里最适合讲述“我们不是乱加规则，而是在形成缺陷类型方法论”的案例之一。

### 启示

这个案例说明，优化系统真正有价值的地方不在于“又多过了一题”，而在于它把失败原因抽象成了一个更稳定的修复模式。后续如果继续做 challenge 集或更难生态，这种“异常回落语义”的能力仍然会复用。

## 案例 5：当前系统边界不只是失败题，也包括成熟度治理

**来源**：`python-poetry/tomlkit#412`  
**任务**：`task_121`  
**缺陷类型**：容器接口 key 规范化与解析路径语义一致性  
**难度**：`easy`

### 背景

这条任务本身不算最难，但它很适合放在“系统边界”位置，因为它刚好是第 `60` 条正式任务，代表项目从“继续扩容”进入了“规模目标已达成，开始强调成熟度”的阶段。问题本身是：解析路径已经接受整数 key，例如 `4 = 5`，但 `add(4, 5)` 和 `setdefault(4, 5)` 仍把 `int` 当成可迭代对象处理，导致 `TypeError`。

### Agent 的执行过程

最小实现位于 `tomlkit_int_key_repo/container.py`。问题集中在 `SingleKey.__init__`：旧逻辑默认 `key` 可逐字符遍历，因此在遇到 `int` 时会直接在 `for character in key` 处崩溃。对应的 `improved_v63` 在 [app/agent/patcher.py](/E:/My_Projects/agentic-software-engineering-roadmap/app/agent/patcher.py) 中补上了这一类 key 规范化规则，让 `add`、`setdefault` 与解析路径保持一致。更重要的是，这一轮还暴露了另一个系统级风险：patcher 版本继承链遗漏会导致旧规则段回归，因此后续又补了 `v63r2 / v63r3` 验证。

### 结果

从任务角度看，`task_121` 通过后，正式集来到 `60 / 60`；从 benchmark 成熟度角度看，后续同版复跑把 `frozen_40 average_duration_sec` 从 `0.5594` 拉回 `0.5454`，补齐了性能门控证据。这说明项目当前的边界已经不只是“能不能修这条题”，而是“能不能在扩容后继续稳住功能、性能和回归体系”。

### 启示

这个案例提醒我们：系统边界不一定表现为一条明确失败题，也可能表现为规模扩大后基础设施是否还稳。下一阶段如果继续推进 roadmap，重点会更多落在稳定性门控、生态均衡扩容和 challenge manifest，而不是单纯继续追通过数。

## 补充说明

如果你想看更完整的时序实验记录，请继续阅读：

- [docs/experiment_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/experiment_summary.md)
- [docs/results.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/results.md)
- [docs/optimization_log.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/optimization_log.md)
