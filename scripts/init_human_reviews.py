"""
Create blank human review files under meta_runs/<run_id>/human_reviews/<scenario_id>.md
for every scenario found in each run's inner workspace. Skips existing files.
"""

from __future__ import annotations

import sys
from pathlib import Path

from human_review_template import render_blank_human_review_md

ROOT = Path(__file__).resolve().parents[1]
META_RUNS = ROOT / "meta_runs"
INNER = Path("round_001") / "inner_workspaces" / "round_001"


def render_md(run_id: str, scenario_id: str) -> str:
    return render_blank_human_review_md(run_id, scenario_id)


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
