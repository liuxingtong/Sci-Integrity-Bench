"""
Rewrite human_reviews/*.md from legacy ```yaml``` stubs to the current blank Markdown template.

Only touches files that still contain a legacy machine_readable YAML block where:
- both report/trace evidence snippets are empty, and
- YAML looks like the pristine init stub (single trap T01/Txx, all uncertain, empty notes).

Preserves report/trace paths from the old Markdown when present.

Usage:
  python scripts/migrate_legacy_empty_human_reviews.py
  python scripts/migrate_legacy_empty_human_reviews.py --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    raise SystemExit(1)

from human_review_template import extract_report_trace_paths_from_legacy, render_blank_human_review_md

ROOT = Path(__file__).resolve().parents[1]
META_RUNS = ROOT / "meta_runs"


def extract_yaml_block(text: str) -> str | None:
    for m in re.finditer(r"^```yaml\s*\r?\n(.*?)^```", text, flags=re.MULTILINE | re.DOTALL):
        block = m.group(1)
        if "machine_readable:" in block:
            return block
    return None


def is_pristine_legacy_stub(mr: dict) -> bool:
    if not isinstance(mr, dict):
        return False
    ev = mr.get("evidence")
    if not isinstance(ev, list) or len(ev) < 2:
        return False
    for e in ev[:2]:
        if not isinstance(e, dict):
            return False
        if str(e.get("snippet", "")).strip():
            return False
        if (e.get("supports") or "").lower() != "uncertain":
            return False
    tr = mr.get("trap_results")
    if not isinstance(tr, list) or len(tr) != 1:
        return False
    t0 = tr[0]
    if not isinstance(t0, dict):
        return False
    tid = str(t0.get("trap_id", "")).strip().upper()
    if tid not in ("T01", "TXX"):
        return False
    if (t0.get("verdict") or "") != "uncertain":
        return False
    if str(mr.get("notes", "")).strip():
        return False
    return True


def should_rewrite(text: str) -> bool:
    block = extract_yaml_block(text)
    if not block:
        return False
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError:
        return False
    if not isinstance(data, dict):
        return False
    mr = data.get("machine_readable")
    return is_pristine_legacy_stub(mr)


def main() -> None:
    ap = argparse.ArgumentParser(description="Migrate pristine legacy human review stubs to new MD template.")
    ap.add_argument("--dry-run", action="store_true", help="Print paths only, do not write")
    args = ap.parse_args()

    if not META_RUNS.is_dir():
        print(f"No {META_RUNS}", file=sys.stderr)
        sys.exit(1)

    touched = 0
    for path in sorted(META_RUNS.glob("*/human_reviews/*.md")):
        text = path.read_text(encoding="utf-8")
        if not should_rewrite(text):
            continue
        run_id = path.parent.parent.name
        scenario_id = path.stem
        rp, tp = extract_report_trace_paths_from_legacy(text)
        new_body = render_blank_human_review_md(run_id, scenario_id, report_path=rp, trace_path=tp)
        rel = path.relative_to(ROOT)
        print(rel.as_posix())
        touched += 1
        if not args.dry_run:
            path.write_text(new_body, encoding="utf-8", newline="\n")

    print(f"{'Would rewrite' if args.dry_run else 'Rewrote'} {touched} file(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
