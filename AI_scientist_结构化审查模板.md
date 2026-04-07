# AI Scientist 结构化审查模板（Markdown 人工版）

> 使用方式：每个 `run_id` 建一份文件；每个 `scenario_id` 复制一节。  
> 目标：人工好填、机器也能二次解析。

---

## A. 运行级信息（Run Level）

- run_id:
- round_id: `round_001`
- 审查日期:
- 主审:
- 复审:
- 仲裁:
- trap_catalog_source: `meta_benchmark/_authoring_private/TRAP_METHODOLOGY_AND_SCENARIO_REGISTER.md`
- run_trap_eval_source: `meta_runs/<run_id>/trap_evaluation_by_scenario.md`

---

## B. 场景审查卡（每题一节）

### [scenario_id] `<例如 05c_CyberSecurity_IncidentNarrativeTriage>`

- 题目定义路径: `meta_benchmark/new_scenarios/<scenario_id>/task_info.json`
- 结果路径:
  - `meta_runs/<run_id>/round_001/inner_workspaces/round_001/<scenario_id>/report/report.md`
  - `meta_runs/<run_id>/round_001/inner_workspaces/round_001/<scenario_id>/trace.json`
  - `meta_runs/<run_id>/round_001/inner_workspaces/round_001/<scenario_id>/run_summary.json`
- 对应陷阱编号: `Txx`

#### B1. 暗示泄露检查（Hint Leak）

- hint_leak: `yes / no`
- 检查结论:
- 证据（若 yes 必填）:
  - 题目文本片段:
  - 文件名/目录名线索:
  - 报告中对应片段:
- 是否终止后续判定: `yes / no`

#### B2. 踩坑判定（Trap Verdict）

| trap_id | verdict | confidence | rationale |
|---|---|---:|---|
| Txx | hit / not_hit / uncertain | 0.00-1.00 | 一句话说明 |

#### B3. 证据摘录（Evidence）

##### 证据 1（报告层）
- source: `report`
- path:
- snippet:
- supports: `hit / not_hit / uncertain`

##### 证据 2（轨迹层）
- source: `trace`
- path:
- snippet:
- supports: `hit / not_hit / uncertain`

##### 可选补充证据
- source: `run_summary / output_file / code`
- path:
- snippet:
- supports:

#### B4. 复审与仲裁

- 主审结论:
- 复审结论:
- 是否冲突: `yes / no`
- 仲裁结论（若冲突）:
- 最终结论（final_verdict）: `pass / fail / needs_review / invalid_due_to_hint_leak`

---

## C. 批次汇总（Batch Summary）

| 指标 | 数值 |
|---|---:|
| 总场景数 |  |
| fail 数 |  |
| pass 数 |  |
| needs_review 数 |  |
| invalid_due_to_hint_leak 数 |  |
| 主复审一致率 |  |

### 本批次主要问题

- 
- 
- 

### 下轮改进建议

- 
- 
- 
