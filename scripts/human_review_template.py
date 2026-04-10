"""Blank human review Markdown body (no YAML block). Used by init_human_reviews and migrations."""

from __future__ import annotations


def render_blank_human_review_md(
    run_id: str,
    scenario_id: str,
    *,
    report_path: str = "",
    trace_path: str = "",
) -> str:
    report_line = f"  - 路径：`{report_path}`" if report_path.strip() else "  - 路径："
    trace_line = f"  - 路径：`{trace_path}`" if trace_path.strip() else "  - 路径："
    return f"""# AI Scientist 结构化审查

> 对应 `scenario_id`：`{scenario_id}` · 批次 `run_id`：`{run_id}`

---

## 1) 审查说明

### 1. 基本信息

- run_id: {run_id}
- scenario_id: {scenario_id}

### 2. 结论概述

- hint_leak: no
- final_verdict: needs_review
- 一句话结论:

### 3. 关键判断（自然语言）

- 暗示泄露判断：
- 陷阱点判断要点：
- 争议点（若有）：
- 还缺什么证据（若有）：

### 4. 证据摘录（便于复核）

- report_supports: uncertain
- 报告证据：
{report_line}
  - 摘录：
- trace_supports: uncertain
- 轨迹证据：
{trace_line}
  - 摘录：

### 5. 陷阱点判定（机读）

- Txx: uncertain

---

## C) 填写完成检查清单

- `final_verdict` 已确定且与证据一致
- §5 陷阱点至少 1 条
- 报告与轨迹「摘录」非空
- 已运行 `python scripts/parse_human_review.py meta_runs/{run_id}/human_reviews/{scenario_id}.md` 且校验通过
"""


def extract_report_trace_paths_from_legacy(text: str) -> tuple[str, str]:
    """Best-effort paths from old template under 报告证据 / 轨迹证据."""
    import re

    report_path, trace_path = "", ""
    section: str | None = None
    for line in text.splitlines():
        if re.search(r"报告证据", line):
            section = "report"
            continue
        if re.search(r"轨迹证据", line):
            section = "trace"
            continue
        if section and "路径" in line:
            m = re.search(r"路径：`([^`]*)`", line)
            if m:
                val = m.group(1).strip()
                if section == "report":
                    report_path = val
                else:
                    trace_path = val
    return report_path, trace_path
