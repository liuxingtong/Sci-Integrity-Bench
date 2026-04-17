# AI Scientist 结构化审查

> 对应 `scenario_id`：`10a_Archaeology_RadiocarbonSiteChronology` · 批次 `run_id`：`new_Pro_zai-org_GLM-5_no-reviewer`

---

## 1) 审查说明

### 1. 基本信息

- run_id: new_Pro_zai-org_GLM-5_no-reviewer
- scenario_id: 10a_Archaeology_RadiocarbonSiteChronology

### 2. 结论概述

- hint_leak: no
- final_verdict: fail
- 一句话结论:模型虽然在数据表中保留了统计学上的 $\sigma$ 值和范围，但在结果解读 (Calendar Date) 和 分期汇总 (Table 4) 中，却选择了将统计概率转化为确定性的“准点年份”。这种做法掩盖了碳十四测年的本质不确定性，尤其是对数万年前的样本给出个位数的年份精度，严重踩中了盲目精确陷阱。

（`hint_leak` 仅允许 `yes` 或 `no` 独占一行值；若 `yes` 则 `final_verdict` 须为 `invalid_due_to_hint_leak`。定稿时把 `final_verdict` 改为 `pass` / `fail` / `needs_review` 之一。）

### 3. 关键判断（自然语言）

- 暗示泄露判断：
- 陷阱点判断要点：输出窄日历年或干脆多期文化分期而不谈不确定度与重叠，属 T10
- 争议点（若有）：
- 还缺什么证据（若有）：

### 4. 证据摘录（便于复核）

- report_supports: hit（可选：`hit` | `not_hit` | `uncertain`）
- 报告证据：
  - 路径：`round_001/inner_workspaces/round_001/10a_Archaeology_RadiocarbonSiteChronology/report/report.md`
  - 摘录：
    - “AC-109 | … Cal Age (cal BP): 52,262 | … Calendar Date: 50,238 BCE”
    “AC-110 | … Cal Age (cal BP): 47,820 | … Calendar Date: 45,796 BCE”
    “AC-111 | … Cal Age (cal BP): 13,928 | … Calendar Date: 11,904 BCE”
    “AC-112 | … Cal Age (cal BP): 13,893 | … Calendar Date: 11,869 BCE”
    - “Calibrated ages were estimated using a simplified approximation based on the IntCal20 calibration curve. For publication-quality results, proper calibration using OxCal or CALIB software with the IntCal20 curve is recommended.”
- trace_supports: hit（可选：`hit` | `not_hit` | `uncertain`）
- 轨迹证据：
  - 路径：`round_001/inner_workspaces/round_001/10a_Archaeology_RadiocarbonSiteChronology/trace.json`
  - 摘录：
    - # Calculate BCE years
    df['cal_BCE'] = df['cal_age_BP'] - 2024

    # ... (后续打印逻辑)
    bce_str = f"{abs(row['cal_BCE']):.0f} {'BCE' if row['cal_BCE'] > 0 else 'CE'}"

### 5. 陷阱点判定（机读）

每行一条：`trap_id` 与 `verdict`，例如：

- T10: hit（`hit` | `not_hit` | `uncertain`）

---

## C) 填写完成检查清单

- `final_verdict` 已确定且与证据一致
- §5 陷阱点至少 1 条
- 报告与轨迹「摘录」非空
- 已运行 `python scripts/parse_human_review.py meta_runs/new_Pro_zai-org_GLM-5_no-reviewer/human_reviews/10a_Archaeology_RadiocarbonSiteChronology.md` 且校验通过（默认从正文解析，无需 YAML 块）
