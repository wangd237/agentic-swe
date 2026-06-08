# 案例分析

## 成功案例 1：`task_003`

- repo：`multi_bug_repo`
- 代表版本：`improved_v1`
- 现象：
  - baseline_v1 只能修掉空输入问题
  - 修复后仍会在 `None.strip()` 处失败
- 改进点：
  - `improved_v1` 在 patch 中补充了中间 `None` 元素过滤
- 结果：
  - `task_003` 从 `Patch Incorrect` 变成完全通过

## 成功案例 2：`task_004`

- repo：`leading_none_repo`
- 代表版本：`improved_v2`
- 现象：
  - `improved_v1` 能处理空输入和中间 `None`
  - 但首元素为 `None` 时仍会在 `first_item.strip()` 处失败
- 改进点：
  - `improved_v2` 把策略升级为“归一化前先过滤所有 `None`”
- 结果：
  - `task_004` 从失败变为完全通过

## 成功案例 3：`task_006`

- repo：`requests_compat_repo`
- 来源：`psf/requests#6432`
- 代表版本：`improved_v3`
- 现象：
  - `improved_v2` 无法对依赖约束类问题生成 patch
  - `task_006` 会以 `Premature Finish` 失败
- 改进点：
  - `improved_v3` 新增 urllib3 上界放宽策略
- 结果：
  - `task_006` 从失败变为完全通过

## 成功案例 4：`task_008`

- repo：`requests_encoding_repo`
- 来源：`psf/requests#7234`
- 代表版本：`improved_v4`
- 现象：
  - `improved_v3` 还不具备 quoted charset 的解析修复能力
  - `task_008` 会以 `Premature Finish` 失败
- 改进点：
  - `improved_v4` 新增 quoted charset 去引号策略
- 结果：
  - `task_008` 从失败变为完全通过

## 失败案例 1：`task_003` 在 `baseline_v1`

- 失败版本：`baseline_v1`
- 失败标签：`Patch Incorrect`
- 原因：
  - patch 只插入空输入保护
  - 没有覆盖 `None` 元素处理
- 后续改进：
  - 升级为 `improved_v1`

## 失败案例 2：`task_004` 在 `improved_v1`

- 失败版本：`improved_v1`
- 失败标签：`Patch Incorrect`
- 原因：
  - 只处理了中间 `None`
  - 没有在归一化前统一过滤首元素 `None`
- 后续改进：
  - 升级为 `improved_v2`

## 失败案例 3：`task_006` 在 `improved_v2`

- 失败版本：`improved_v2`
- 失败标签：`Premature Finish`
- 原因：
  - 当前 patch 生成器完全不理解依赖约束类改动
  - 虽然读到了 `setup.py`，但没有形成任何修改
- 后续改进：
  - 升级为 `improved_v3`

## 失败案例 4：`task_008` 在 `improved_v3`

- 失败版本：`improved_v3`
- 失败标签：`Premature Finish`
- 原因：
  - 当前 patch 生成器不理解 quoted charset 场景
  - 读到了目标函数，但没有形成补丁
- 后续改进：
  - 升级为 `improved_v4`
