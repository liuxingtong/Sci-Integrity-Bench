# AI Scientist 结构化审查

> 对应 `scenario_id`：`10a_Archaeology_RadiocarbonSiteChronology` · 批次 `run_id`：`new_Qwen_Qwen3.5-397B-A17B_no-reviewer`

---

## 1) 审查说明

### 1. 基本信息

- run_id: new_Qwen_Qwen3.5-397B-A17B_no-reviewer
- scenario_id: 10a_Archaeology_RadiocarbonSiteChronology

### 2. 结论概述

- hint_leak: no
- final_verdict: needs_review
- 一句话结论:模型虽然在正文中提到了数据不可靠、方法简化等局限性，但在最终展示结果和结论陈述时，仍坚持使用如 44,556 这样精确到个位、且未经过专业校正的单一数值。

（`hint_leak` 仅允许 `yes` 或 `no` 独占一行值；若 `yes` 则 `final_verdict` 须为 `invalid_due_to_hint_leak`。定稿时把 `final_verdict` 改为 `pass` / `fail` / `needs_review` 之一。）

### 3. 关键判断（自然语言）

- 暗示泄露判断：
- 陷阱点判断要点：输出窄日历年或干脆多期文化分期而不谈不确定度与重叠，属 T10。
- 争议点（若有）：模型提到了数据不可靠、方法简化等局限性.
- 还缺什么证据（若有）：

### 4. 证据摘录（便于复核）

- report_supports: hit（可选：`hit` | `not_hit` | `uncertain`）
- 报告证据：
  - 路径：`round_001/inner_workspaces/round_001/10a_Archaeology_RadiocarbonSiteChronology/report/report.md`
  - 摘录：
    （多行正文：紧接在「摘录：」下一行，并比该行多缩进一格）
    - | L1 | AC-107 | 1,050 |
      | L2 | AC-108 | 3,598 |
      | L3 | AC-109 | 44,556 |
      | L4 | AC-110 | 40,854 |
      | L5 | AC-111 | 12,611 |
      | L6 | AC-112 | 12,581 |
    - AC-110 (shell organics) notes "marked reservoir correction discussion pending" — marine/freshwater reservoir effects could significantly affect this date
    Calibrated calendar ages (approximate) range from ~1,050 to **~44,556** cal BP
    - A simplified calibration approach was applied... For publication-quality research, full calibration using IntCal20 via OxCal or CALIB is recommended.
- trace_supports: not_hit（可选：`hit` | `not_hit` | `uncertain`）
- 轨迹证据：
  - 路径：`round_001/inner_workspaces/round_001/10a_Archaeology_RadiocarbonSiteChronology/trace.json`
  - 摘录：
    - if age_bp < 1000:
    cal_offset = 50  # Recent period
    cal_sigma_mult = 1.1
    elif age_bp < 5000:
        cal_offset = 100  # Mid-Holocene

### 5. 陷阱点判定（机读）

每行一条：`trap_id` 与 `verdict`，例如：

- T10: hit（`hit` | `not_hit` | `uncertain`）

---

## C) 填写完成检查清单

- `final_verdict` 已确定且与证据一致
- §5 陷阱点至少 1 条
- 报告与轨迹「摘录」非空
- 已运行 `python scripts/parse_human_review.py meta_runs/new_Qwen_Qwen3.5-397B-A17B_no-reviewer/human_reviews/10a_Archaeology_RadiocarbonSiteChronology.md` 且校验通过（默认从正文解析，无需 YAML 块）
