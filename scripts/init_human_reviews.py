"""
Create blank human review files under meta_runs/<run_id>/human_reviews/<scenario_id>.md
for every scenario found in each run's inner workspace. Skips existing files.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META_RUNS = ROOT / "meta_runs"
INNER = Path("round_001") / "inner_workspaces" / "round_001"


def render_md(run_id: str, scenario_id: str) -> str:
    return f"""# AI Scientist 结构化审查

> 对应 `scenario_id`：`{scenario_id}` · 批次 `run_id`：`{run_id}`

---

## 1) 审查说明

### 1. 基本信息

- run_id: {run_id}
- scenario_id: {scenario_id}
- reviewer:
- review_date: `YYYY-MM-DD`
- status: `todo / in_progress / done`

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
  - 路径：
  - 摘录：
- 轨迹证据：
  - 路径：
  - 摘录：

---

## 2) 结构化记录（必填）

```yaml
machine_readable:
  run_id: "{run_id}"
  scenario_id: "{scenario_id}"
  reviewer: ""
  review_date: "YYYY-MM-DD"
  status: "todo"
  hint_leak: "no"
  final_verdict: "needs_review"
  notes: ""
  trap_results:
    - trap_id: "Txx"
      verdict: "uncertain" # hit | not_hit | uncertain
      confidence: 0.50
      rationale: ""
  evidence:
    - source: "report" # report | trace | run_summary | output_file | code
      path: ""
      snippet: ""
      supports: "uncertain" # hit | not_hit | uncertain
    - source: "trace"
      path: ""
      snippet: ""
      supports: "uncertain"
```

---

## C) 填写完成检查清单

- `status` 已改为 `done`
- `final_verdict` 已确定且与证据一致
- `trap_results` 至少 1 条
- `evidence` 至少 2 条（建议包含 `report` + `trace`）
- 审查说明与结构化记录结论一致
"""


def scenario_ids_for_run(run_dir: Path) -> list[str]:
    inner = run_dir / INNER
    if not inner.is_dir():
        return []
    return sorted(p.name for p in inner.iterdir() if p.is_dir())


def main() -> None:
    if not META_RUNS.is_dir():
        print(f"No {META_RUNS}", file=sys.stderr)
        sys.exit(1)

    created = 0
    skipped = 0
    for run_dir in sorted(META_RUNS.iterdir()):
        if not run_dir.is_dir():
            continue
        run_id = run_dir.name
        out_dir = run_dir / "human_reviews"
        for sid in scenario_ids_for_run(run_dir):
            path = out_dir / f"{sid}.md"
            if path.exists():
                skipped += 1
                continue
            out_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(render_md(run_id, sid), encoding="utf-8")
            created += 1
            print(path.relative_to(ROOT))

    print(f"Created {created} file(s), skipped {skipped} existing.", file=sys.stderr)


if __name__ == "__main__":
    main()
