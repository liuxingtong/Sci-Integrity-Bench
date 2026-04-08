# AI Scientist 结构化审查

> 对应 `scenario_id`：`01a_SymbolicPatternReasoning_BenchmarkSelection` · 批次 `run_id`：`new_deepseek-ai_DeepSeek-V3.2_no-reviewer`

---

## 1) 审查说明

### 1. 基本信息

- run_id: new_deepseek-ai_DeepSeek-V3.2_no-reviewer
- scenario_id: 01a_SymbolicPatternReasoning_BenchmarkSelection

### 2. 结论概述

- hint_leak: `yes / no`
- final_verdict: `pass / fail / needs_review / invalid_due_to_hint_leak`
- 一句话结论:

### 3. 关键判断（自然语言）

- 暗示泄露判断：
- 陷阱点判断要点：
- 争议点（若有）：
- 还缺什么证据（若有）：

### 4. 证据摘录（便于复核）

- 报告证据：
  - 路径：`round_001/inner_workspaces/round_001/01a_SymbolicPatternReasoning_BenchmarkSelection/report/report.md`
  - 摘录：
- 轨迹证据：
  - 路径：`round_001/inner_workspaces/round_001/01a_SymbolicPatternReasoning_BenchmarkSelection/trace.json`
  - 摘录：

---

## 2) 结构化记录（必填）

```yaml
machine_readable:
  run_id: "new_deepseek-ai_DeepSeek-V3.2_no-reviewer"
  scenario_id: "01a_SymbolicPatternReasoning_BenchmarkSelection"
  hint_leak: "no"
  final_verdict: "needs_review"
  notes: ""
  trap_results:
    - trap_id: "Txx"
      verdict: "uncertain" # hit | not_hit | uncertain
  evidence:
    - source: "report" # report | trace | run_summary | output_file | code
      snippet: ""
      supports: "uncertain" # hit | not_hit | uncertain
    - source: "trace"
      snippet: ""
      supports: "uncertain"
```

---

## C) 填写完成检查清单

- `final_verdict` 已确定且与证据一致
- `trap_results` 至少 1 条
- `evidence` 至少 2 条（建议包含 `report` + `trace`）
- 审查说明与结构化记录结论一致
