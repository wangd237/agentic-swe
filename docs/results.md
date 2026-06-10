# 结果记录

## 当前状态

- 当前阶段：`Phase 6`
- 当前已完成单任务 patch 闭环
- 当前已完成最小 batch run 验证
- 当前已完成最小 baseline eval 验证
- 当前已完成 baseline vs improved 自动 compare 报告
- 当前已完成 `improved_v2` 新一轮 report-set 对比
- 当前已补充真实 issue 接入前的任务校验基础设施
- 当前已补充真实 issue 候选导入脚本
- 当前已成功导入首条真实 issue 候选并生成 `task_005` 草稿
- 当前已补充 `task_006`，并在真实 issue 派生任务上完成 `improved_v2 -> improved_v3` 对比
- 当前已成功导入第 2 条真实 issue 候选并生成 `task_007` 草稿
- 当前已补充 `task_008`，并在真实 issue 派生任务集上完成 `improved_v3 -> improved_v4` 对比
- 当前已成功导入第 3 条真实 issue 候选并生成 `task_009` 草稿
- 当前已补充 `task_010`，并在真实 issue 派生任务集上完成 `improved_v4 -> improved_v5` 对比
- 当前已补充 `task_013`，并在真实 issue 派生任务集上完成 `improved_v5 -> improved_v6` 对比
- 当前已补充 `task_016`，并在真实 issue 派生任务集上完成 `improved_v6 -> improved_v7` 对比
- 当前已补充 `task_017`，并在真实 issue 派生任务集上完成 `improved_v7 -> improved_v8` 对比
- 当前已补充 `task_019`，并在真实 issue 派生任务集上完成 `improved_v8 -> improved_v9` 对比
- 当前已补充 `task_022`，并在真实 issue 派生任务集上完成 `improved_v9 -> improved_v10` 对比
- 当前已补充 `task_024`，并在真实 issue 派生任务集上完成 `improved_v10 -> improved_v11` 对比
- 当前已补充 `task_026`，并在真实 issue 派生任务集上完成 `improved_v11 -> improved_v12` 扩容对比
- 当前已补充 `task_028`，并在真实 issue 派生任务集上完成 `improved_v12 -> improved_v13` 扩容对比
- 当前已补充 `task_030`，并在真实 issue 派生任务集上完成 `improved_v13 -> improved_v14` 扩容对比
- 当前已补充 `task_032`，并在真实 issue 派生任务集上完成 `improved_v14 -> improved_v15` 扩容对比
- 当前已补充 `task_034`，并在真实 issue 派生任务集上完成 `improved_v15 -> improved_v16` 扩容对比
- 当前已补充 `task_036`，并在真实 issue 派生任务集上完成 `improved_v16 -> improved_v17` 扩容对比
- 当前已补充 `task_038`，并在真实 issue 派生任务集上完成 `improved_v17 -> improved_v18` 扩容对比
- 当前已补充冻结 15 条真实任务的同集合评测，对比 `improved_v16 -> improved_v17`

## 当前可展示结果

### 单任务结果

- `task_001` 已可自动修复成功
- 参考运行：
  - `logs/trajectories/task_001/run_007/`

### 批量结果

- 当前批量运行：
  - `logs/summaries/batch_run_001.json`
  - `logs/summaries/batch_run_001.md`
- 当前结果：
  - task_count: `2`
  - success_count: `2`
  - success_rate: `1.0`

### baseline eval 结果

- 当前评测输出：
  - `logs/summaries/batch_eval_001.json`
  - `logs/summaries/batch_eval_001.md`
- 当前指标：
  - success_rate: `1.0`
  - test_pass_rate: `1.0`
  - partial_fix_rate: `0.0`
  - average_steps: `9.0`
  - average_tool_calls: `9.0`
  - average_duration_sec: `0.5406`
  - average_modified_files: `1.0`
  - key_file_read_rate: `1.0`
  - test_execution_rate: `1.0`
  - repeated_search_rate: `0.0`
  - reasonable_finish_rate: `1.0`

### 当前评测结论

- baseline eval 链路已经跑通
- 当前开发任务集全部成功，因此 taxonomy 未命中任何错误标签
- 下一步需要通过更有区分度的任务集和 improved 版本，制造真正有分析价值的对比

### baseline vs improved 对比

第一轮对比：

- baseline：
  - `logs/summaries/batch_eval_baseline_001.json`
- improved：
  - `logs/summaries/batch_eval_improved_001.json`
- compare：
  - `logs/summaries/batch_compare_phase6_002.json`
  - `logs/summaries/batch_compare_phase6_002.md`

第一轮结果：

- `success_rate`
  - baseline: `0.5`
  - improved: `1.0`
- `test_pass_rate`
  - baseline: `0.5`
  - improved: `1.0`

第二轮对比：

- baseline_v1：
  - `logs/summaries/batch_eval_baselinev2_001.json`
- improved_v1：
  - `logs/summaries/batch_eval_improvedv1r2_001.json`
- improved_v2：
  - `logs/summaries/batch_eval_improvedv2_001.json`
- compare：
  - `logs/summaries/batch_compare_phase6v2_step1_001.json`
  - `logs/summaries/batch_compare_phase6v2_step2_001.json`

第二轮结果：

- `success_rate`
  - baseline_v1: `0.3333`
  - improved_v1: `0.6667`
  - improved_v2: `1.0`
- `test_pass_rate`
  - baseline_v1: `0.3333`
  - improved_v1: `0.6667`
  - improved_v2: `1.0`
- `partial_fix_rate`
  - baseline_v1: `0.6667`
  - improved_v1: `0.3333`
  - improved_v2: `0.0`

### 自动对比报告能额外回答什么

当前 compare 报告除了复述核心指标，还会自动给出：

- 每项 metric 的 delta
- 每项 metric 是 `improved / regressed / unchanged`
- taxonomy 的数量变化
- 每个 task 的错误标签是否发生变化

当前关键变化：

- `Patch Incorrect`
  - baseline: `1`
  - improved: `0`
- `task_003`
  - baseline: `Patch Incorrect`
  - improved: `无错误标签`

第二轮关键变化：

- `task_004`
  - improved_v1: `Patch Incorrect`
  - improved_v2: `无错误标签`

### 真实 issue 派生任务对比

- realissuev2：
  - `logs/summaries/batch_eval_realissuev2_001.json`
- realissuev3：
  - `logs/summaries/batch_eval_realissuev3_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step1_001.json`

当前结果：

- `success_rate`
  - improved_v2: `0.0`
  - improved_v3: `1.0`
- `test_pass_rate`
  - improved_v2: `0.0`
  - improved_v3: `1.0`
- taxonomy
  - improved_v2: `Premature Finish = 1`
  - improved_v3: `无错误标签`

扩充到 2 条真实派生任务后的结果：

- realissuev3r2：
  - `logs/summaries/batch_eval_realissuev3r2_001.json`
- realissuev4：
  - `logs/summaries/batch_eval_realissuev4_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step2_001.json`

当前结果：

- `success_rate`
  - improved_v3: `0.5`
  - improved_v4: `1.0`
- `test_pass_rate`
  - improved_v3: `0.5`
  - improved_v4: `1.0`
- taxonomy
  - improved_v3: `Premature Finish = 1`
  - improved_v4: `无错误标签`

扩充到 3 条真实派生任务后的结果：

- realissuev4r2：
  - `logs/summaries/batch_eval_realissuev4r2_001.json`
- realissuev5：
  - `logs/summaries/batch_eval_realissuev5_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step3_001.json`

当前结果：

- `success_rate`
  - improved_v4: `0.6667`
  - improved_v5: `1.0`
- `test_pass_rate`
  - improved_v4: `0.6667`
  - improved_v5: `1.0`
- taxonomy
  - improved_v4: `Premature Finish = 1`
  - improved_v5: `无错误标签`

扩充到 4 条真实派生任务后的结果：

- realissuev5r2：
  - `logs/summaries/batch_eval_realissuev5r2_001.json`
- realissuev6：
  - `logs/summaries/batch_eval_realissuev6_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step4_001.json`

当前结果：

- `success_rate`
  - improved_v5: `0.75`
  - improved_v6: `1.0`
- `test_pass_rate`
  - improved_v5: `0.75`
  - improved_v6: `1.0`
- taxonomy
  - improved_v5: `Premature Finish = 1`
  - improved_v6: `无错误标签`

扩充到 5 条真实派生任务后的结果：

- realissuev6r2：
  - `logs/summaries/batch_eval_realissuev6r2_001.json`
- realissuev7：
  - `logs/summaries/batch_eval_realissuev7_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step5_001.json`

当前结果：

- `success_rate`
  - improved_v6: `0.8`
  - improved_v7: `1.0`
- `test_pass_rate`
  - improved_v6: `0.8`
  - improved_v7: `1.0`
- taxonomy
  - improved_v6: `Premature Finish = 1`
  - improved_v7: `无错误标签`

扩充到 6 条真实派生任务后的结果：

- realissuev7r2：
  - `logs/summaries/batch_eval_realissuev7r2_001.json`
- realissuev8：
  - `logs/summaries/batch_eval_realissuev8_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step6_001.json`

当前结果：

- `success_rate`
  - improved_v7: `0.8333`
  - improved_v8: `1.0`
- `test_pass_rate`
  - improved_v7: `0.8333`
  - improved_v8: `1.0`
- taxonomy
  - improved_v7: `Premature Finish = 1`
  - improved_v8: `无错误标签`
- changed task
  - `task_017`: `Premature Finish -> 无错误标签`

扩充到 7 条真实派生任务后的结果：

- realissuev8r2：
  - `logs/summaries/batch_eval_realissuev8r2_001.json`
- realissuev9：
  - `logs/summaries/batch_eval_realissuev9_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step7_001.json`

当前结果：

- `success_rate`
  - improved_v8: `0.8571`
  - improved_v9: `1.0`
- `test_pass_rate`
  - improved_v8: `0.8571`
  - improved_v9: `1.0`
- taxonomy
  - improved_v8: `Premature Finish = 1`
  - improved_v9: `无错误标签`
- changed task
  - `task_019`: `Premature Finish -> 无错误标签`

扩充到 8 条真实派生任务后的结果：

- realissuev9r2：
  - `logs/summaries/batch_eval_realissuev9r2_001.json`
- realissuev10：
  - `logs/summaries/batch_eval_realissuev10_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step8_001.json`

当前结果：

- `success_rate`
  - improved_v9: `0.875`
  - improved_v10: `1.0`
- `test_pass_rate`
  - improved_v9: `0.875`
  - improved_v10: `1.0`
- taxonomy
  - improved_v9: `Premature Finish = 1`
  - improved_v10: `无错误标签`
- changed task
  - `task_022`: `Premature Finish -> 无错误标签`

扩充到 9 条真实派生任务后的结果：

- realissuev10r2：
  - `logs/summaries/batch_eval_realissuev10r2_001.json`
- realissuev11：
  - `logs/summaries/batch_eval_realissuev11_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step9_001.json`

当前结果：

- `success_rate`
  - improved_v10: `0.8889`
  - improved_v11: `1.0`
- `test_pass_rate`
  - improved_v10: `0.8889`
  - improved_v11: `1.0`
- taxonomy
  - improved_v10: `Premature Finish = 1`
  - improved_v11: `无错误标签`
- changed task
  - `task_024`: `Premature Finish -> 无错误标签`

扩充到 10 条真实派生任务后的结果：

- realissuev11：
  - `logs/summaries/batch_eval_realissuev11_001.json`
- realissuev12：
  - `logs/summaries/batch_eval_realissuev12_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step10_001.json`

当前结果：

- `success_rate`
  - improved_v11: `1.0`
  - improved_v12: `1.0`
- `test_pass_rate`
  - improved_v11: `1.0`
  - improved_v12: `1.0`
- `average_duration_sec`
  - improved_v11: `0.5872`
  - improved_v12: `0.5526`
- `average_steps`
  - improved_v11: `9.5556`
  - improved_v12: `9.5`
- changed task
  - `task_026`: 新增任务，在 `improved_v12` 下完全通过

扩充到 11 条真实派生任务后的结果：

- realissuev12：
  - `logs/summaries/batch_eval_realissuev12_001.json`
- realissuev13：
  - `logs/summaries/batch_eval_realissuev13_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step11_001.json`

当前结果：

- `success_rate`
  - improved_v12: `1.0`
  - improved_v13: `1.0`
- `test_pass_rate`
  - improved_v12: `1.0`
  - improved_v13: `1.0`
- `average_duration_sec`
  - improved_v12: `0.5526`
  - improved_v13: `0.5512`
- `average_steps`
  - improved_v12: `9.5`
  - improved_v13: `9.3636`
- changed task
  - `task_028`: 新增任务，在 `improved_v13` 下完全通过

扩充到 12 条真实派生任务后的结果：

- realissuev13：
  - `logs/summaries/batch_eval_realissuev13_001.json`
- realissuev14：
  - `logs/summaries/batch_eval_realissuev14_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step12_001.json`

当前结果：

- `success_rate`
  - improved_v13: `1.0`
  - improved_v14: `1.0`
- `test_pass_rate`
  - improved_v13: `1.0`
  - improved_v14: `1.0`
- `average_steps`
  - improved_v13: `9.3636`
  - improved_v14: `9.25`
- `average_duration_sec`
  - improved_v13: `0.5512`
  - improved_v14: `0.5811`
- changed task
  - `task_030`: 新增任务，在 `improved_v14` 下完全通过

扩充到 13 条真实派生任务后的结果：

- realissuev14：
  - `logs/summaries/batch_eval_realissuev14_001.json`
- realissuev15：
  - `logs/summaries/batch_eval_realissuev15_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step13_001.json`

当前结果：

- `success_rate`
  - improved_v14: `1.0`
  - improved_v15: `1.0`
- `test_pass_rate`
  - improved_v14: `1.0`
  - improved_v15: `1.0`
- `average_steps`
  - improved_v14: `9.25`
  - improved_v15: `9.2308`
- `average_duration_sec`
  - improved_v14: `0.5811`
  - improved_v15: `0.552`
- changed task
  - `task_032`: 新增任务，在 `improved_v15` 下完全通过

扩充到 14 条真实派生任务后的结果：

- realissuev15：
  - `logs/summaries/batch_eval_realissuev15_001.json`
- realissuev16：
  - `logs/summaries/batch_eval_realissuev16_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step14_001.json`

当前结果：

- `success_rate`
  - improved_v15: `1.0`
  - improved_v16: `1.0`
- `test_pass_rate`
  - improved_v15: `1.0`
  - improved_v16: `1.0`
- `average_steps`
  - improved_v15: `9.2308`
  - improved_v16: `9.3571`
- `average_duration_sec`
  - improved_v15: `0.552`
  - improved_v16: `0.5792`
- changed task
  - `task_034`: 新增任务，在 `improved_v16` 下完全通过
- 备注
  - 这一轮 compare 属于任务集扩容对比，不是冻结同集合对比
  - 成功率保持 `100%`，但平均步骤数和平均耗时小幅回升

扩充到 15 条真实派生任务后的结果：

- realissuev16：
  - `logs/summaries/batch_eval_realissuev16_001.json`
- realissuev17：
  - `logs/summaries/batch_eval_realissuev17_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step15_001.json`

当前结果：

- `success_rate`
  - improved_v16: `1.0`
  - improved_v17: `1.0`
- `test_pass_rate`
  - improved_v16: `1.0`
  - improved_v17: `1.0`
- `average_steps`
  - improved_v16: `9.3571`
  - improved_v17: `9.2667`
- `average_duration_sec`
  - improved_v16: `0.5792`
  - improved_v17: `0.5887`
- changed task
  - `task_036`: 新增任务，在 `improved_v17` 下完全通过
- 备注
  - 这一轮 compare 仍属于任务集扩容对比
  - 平均步数略有改善，但平均耗时小幅回升

冻结 15 条真实任务后的同集合结果：

- baseline：
  - `logs/summaries/batch_eval_frozen15v16_001.json`
- improved：
  - `logs/summaries/batch_eval_frozen15v17_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen15_step1_001.json`

当前结果：

- `success_rate`
  - improved_v16: `0.9333`
  - improved_v17: `1.0`
- `test_pass_rate`
  - improved_v16: `0.9333`
  - improved_v17: `1.0`
- `average_steps`
  - improved_v16: `9.2667`
  - improved_v17: `9.2667`
- `average_duration_sec`
  - improved_v16: `0.5926`
  - improved_v17: `0.5906`
- taxonomy
  - improved_v16: `Premature Finish = 1`
  - improved_v17: `无错误标签`
- changed task
  - `task_036`: `Premature Finish -> 无错误标签`

扩充到 16 条真实派生任务后的结果：

- realissuev17：
  - `logs/summaries/batch_eval_realissuev17_001.json`
- realissuev18：
  - `logs/summaries/batch_eval_realissuev18_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step16_001.json`

当前结果：

- `task_count`
  - improved_v17: `15`
  - improved_v18: `16`
- `success_count`
  - improved_v17: `15`
  - improved_v18: `16`
- `success_rate`
  - improved_v17: `1.0`
  - improved_v18: `1.0`
- `test_pass_rate`
  - improved_v17: `1.0`
  - improved_v18: `1.0`
- `average_steps`
  - improved_v17: `9.2667`
  - improved_v18: `9.1875`
- `average_duration_sec`
  - improved_v17: `0.5887`
  - improved_v18: `0.5649`
- changed task
  - `task_038`: 新增任务，在 `improved_v18` 下完全通过
- 备注
  - 这一轮 compare 仍属于任务集扩容对比
  - 在正式任务集扩充到 16 条后，成功率继续保持 `100%`

### 当前优化结论

- improved policy 在不增加额外步骤成本的前提下，提升了成功率
- 关键改动是让 patch 逻辑除了空输入保护，还能处理 `None` 元素过滤
- `improved_v2` 进一步把“只处理部分 None”升级为“归一化前全量过滤 None”
- `improved_v3` 进一步覆盖了真实 issue 派生出来的依赖约束修复场景
- `improved_v4` 进一步覆盖了真实 issue 派生出来的 header charset 解析场景
- `improved_v5` 进一步覆盖了真实 issue 派生出来的 ANSI 文本 CRLF 行尾拆分场景
- `improved_v6` 进一步覆盖了真实 issue 派生出来的 RichHandler 时区偏移场景
- `improved_v7` 进一步覆盖了真实 issue 派生出来的负向 boolean flag 默认值场景
- `improved_v8` 进一步覆盖了真实 issue 派生出来的最近 marker 覆盖优先场景
- `improved_v9` 进一步覆盖了真实 issue 派生出来的 UTC/GMT 无 offset 时区解析场景
- `improved_v10` 进一步覆盖了真实 issue 派生出来的 9 位时间串解析场景
- `improved_v11` 进一步覆盖了真实 issue 派生出来的模板变量控制流分析场景
- `improved_v12` 进一步覆盖了真实 issue 派生出来的 Jinja slice filter 填充值边界场景
- `improved_v13` 进一步覆盖了真实 issue 派生出来的数组序列化重复逗号场景
- `improved_v14` 进一步覆盖了真实 issue 派生出来的 dotted inline table 分隔损坏场景
- `improved_v15` 进一步覆盖了真实 issue 派生出来的 wheel 版本号 normalization 校验场景
- `improved_v16` 进一步覆盖了真实 issue 派生出来的 mixed-type extras 错误消息渲染场景
- `improved_v17` 进一步覆盖了真实 issue 派生出来的 hostname 格式检查异常回落场景
- `improved_v18` 进一步覆盖了真实 issue 派生出来的 integer-valued `multipleOf` 浮点数数值语义场景
- compare 报告已经可以作为后续每轮优化的标准化对比产物
- 冻结 manifest 让我们第一次拿到了同集合上的真实提升证据
- 任务 schema 已经支持从 synthetic 过渡到 real_issue
- 详细过程与文件级改动见：
  - `docs/optimization_log.md`

## 后续将记录

- baseline 结果
- improved 结果
- compare 结果
- 核心指标对比
- 代表性成功案例
- 代表性失败案例
- 未来引入 GitHub 真实仓库 issue 后的外部评测结果
