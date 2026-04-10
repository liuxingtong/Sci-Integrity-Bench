"""
Rewrite human_reviews/*.md with the latest blank body from human_review_template.py.

Targets files that look like AI Scientist blank reviews but lack the current hint lines.
Preserves report/trace path backticks.

Usage:
  python scripts/sync_human_review_blank_template.py
  python scripts/sync_human_review_blank_template.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META_RUNS = ROOT / "meta_runs"

from human_review_template import extract_report_trace_paths_from_legacy, render_blank_human_review_md


def needs_resync(text: str) -> bool:
    if "# AI Scientist 结构化审查" not in text:
        return False
    if "```yaml" in text or "## 2) 结构化记录" in text:
        return False
    return "（`hint_leak` 仅允许" not in text


def main() -> None:
    ap = argparse.ArgumentParser(description="Resync blank human review MD to latest template hints.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not META_RUNS.is_dir():
        print(f"No {META_RUNS}", file=sys.stderr)
        sys.exit(1)

    n = 0
    for path in sorted(META_RUNS.glob("*/human_reviews/*.md")):
        text = path.read_text(encoding="utf-8")
        if not needs_resync(text):
            continue
        run_id = path.parent.parent.name
        scenario_id = path.stem
        rp, tp = extract_report_trace_paths_from_legacy(text)
        body = render_blank_human_review_md(run_id, scenario_id, report_path=rp, trace_path=tp)
        print(path.relative_to(ROOT).as_posix())
        n += 1
        if not args.dry_run:
            path.write_text(body, encoding="utf-8", newline="\n")

    print(f"{'Would update' if args.dry_run else 'Updated'} {n} file(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
