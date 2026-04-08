#!/usr/bin/env python3
"""
Merge all timestamped meta_runs/<new_*_no-reviewer_YYYYMMDD_HHMMSS>/ into one folder per model:
  meta_runs/new_<model>_no-reviewer/

Conflict rules per scenario_id:
  - Prefer higher outcome: Done > Fail/ProjectFail > Error
  - If same tier, prefer the run with the newer timestamp suffix (later batch)

Copies winning inner_workspaces/round_001/<scenario_id>/ and human_reviews/<scenario_id>.md.
Moves old run dirs into meta_runs/_archive_merged_<stamp>/ (does not delete).

Usage: python scripts/merge_meta_runs_by_model.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "meta_runs"

INNER_REL = Path("round_001") / "inner_workspaces" / "round_001"
OUTER_REL = Path("round_001") / "outer_workspace"
RESULTS_NAME = "inner_results_r001.json"

_RUN_RE = re.compile(
    r"^new_(?P<model>.+?)_(?P<rev>no-reviewer|reviewer)_(?P<stamp>\d{8}_\d{6})$"
)


def sort_scenario_ids_abc_rotation(ids: List[str]) -> List[str]:
    head = re.compile(r"^(\d+)([a-z])?_")

    def key(sid: str) -> tuple:
        m = head.match(sid)
        if not m:
            return (10**9, 99, sid)
        n = int(m.group(1))
        letter = m.group(2)
        vi = ord(letter) - ord("a") if letter else 0
        return (n, vi, sid)

    return sorted(ids, key=key)


def _status_rank(status: Any) -> int:
    s = str(status or "").strip().lower()
    if s == "done":
        return 3
    if s in ("fail", "projectfail"):
        return 2
    if s == "error":
        return 1
    return 2


def parse_run_dir(name: str) -> Optional[Tuple[str, str, str]]:
    """Return (model_key, no-reviewer|reviewer, stamp) or None."""
    m = _RUN_RE.match(name)
    if not m:
        return None
    return m.group("model"), m.group("rev"), m.group("stamp")


def canonical_run_name(model_key: str, rev: str) -> str:
    return f"new_{model_key}_{rev}"


def load_batch(run_dir: Path) -> List[Dict[str, Any]]:
    p = run_dir / OUTER_REL / RESULTS_NAME
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(data, list) or not data or not isinstance(data[0], list):
        return []
    return data[0]


def pick_winners(
    sources: List[Tuple[str, Path, List[Dict[str, Any]]]],
) -> Dict[str, Tuple[Dict[str, Any], str, Path]]:
    """
    sources: list of (stamp, run_dir, batch_rows) sorted by stamp ascending.
    Returns scenario_id -> (row, stamp, run_dir) for the chosen row.
    """
    best: Dict[str, Tuple[int, str, Dict[str, Any], Path]] = {}

    for stamp, run_dir, batch in sources:
        for row in batch:
            sid = str(row.get("scenario_id", "")).strip()
            if not sid:
                continue
            rank = _status_rank(row.get("status"))
            cur = best.get(sid)
            if cur is None:
                best[sid] = (rank, stamp, dict(row), run_dir)
                continue
            old_rank, old_stamp, _, _ = cur
            if rank > old_rank:
                best[sid] = (rank, stamp, dict(row), run_dir)
            elif rank == old_rank and stamp > old_stamp:
                best[sid] = (rank, stamp, dict(row), run_dir)

    out: Dict[str, Tuple[Dict[str, Any], str, Path]] = {}
    for sid, tup in best.items():
        _r, st, row, run_dir = tup
        out[sid] = (row, st, run_dir)
    return out


def copy_tree_replace(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def merge_model(
    model_key: str,
    rev: str,
    run_dirs: List[Tuple[str, Path]],
    dry_run: bool,
) -> None:
    """run_dirs: list of (stamp, path); may include pre-existing canonical dir (stamp 00000000_000000)."""
    name = canonical_run_name(model_key, rev)
    dest_root = META / name

    # Load all batches (read before removing dest_root)
    sources: List[Tuple[str, Path, List[Dict[str, Any]]]] = []
    for stamp, rd in run_dirs:
        batch = load_batch(rd)
        if batch:
            sources.append((stamp, rd, batch))

    if not sources:
        print(f"  [skip] {name}: no inner_results in any source")
        return

    sources.sort(key=lambda x: x[0])

    winners = pick_winners(sources)
    ids_sorted = sort_scenario_ids_abc_rotation(list(winners.keys()))
    merged_batch = [winners[sid][0] for sid in ids_sorted]

    inner_dest = dest_root / INNER_REL
    outer_dest = dest_root / OUTER_REL
    hr_dest = dest_root / "human_reviews"

    print(f"\n=== {name} ({len(merged_batch)} scenarios) ===")

    if dry_run:
        for sid in ids_sorted:
            row, st, rd = winners[sid]
            print(f"  {sid}: status={row.get('status')} <- {rd.name} ({st})")
        print(f"  -> would write {dest_root}")
        return

    if dest_root.exists():
        shutil.rmtree(dest_root)

    outer_dest.mkdir(parents=True, exist_ok=True)
    inner_dest.mkdir(parents=True, exist_ok=True)
    hr_dest.mkdir(parents=True, exist_ok=True)

    for row in merged_batch:
        sid = str(row.get("scenario_id", "")).strip()
        if sid:
            row["inner_ws"] = str((inner_dest / sid).resolve())

    results_path = outer_dest / RESULTS_NAME
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump([merged_batch], f, indent=2, ensure_ascii=False)

    for sid in ids_sorted:
        row, _st, run_dir = winners[sid]
        src_inner = run_dir / INNER_REL / sid
        dst_inner = inner_dest / sid
        if src_inner.is_dir():
            copy_tree_replace(src_inner, dst_inner)
        else:
            print(f"  [warn] missing inner workspace: {src_inner}")

        src_hr = run_dir / "human_reviews" / f"{sid}.md"
        if src_hr.is_file():
            shutil.copy2(src_hr, hr_dest / f"{sid}.md")

    # meta_summary: seed from newest timestamped source (last in sorted sources)
    newest = sources[-1][1]
    meta_src = newest / "meta_summary.json"
    if meta_src.is_file():
        try:
            meta = json.loads(meta_src.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    else:
        meta = {}
    meta["run_stamp"] = datetime.now().strftime("%Y%m%d_%H%M%S")
    meta["merged_from"] = [f"{s}:{p.name}" for s, p in run_dirs]
    meta["merged_scenario_count"] = len(merged_batch)
    meta["run_dir_leaf"] = name
    meta["letter_filter"] = "merged_abc"
    meta["scenario_order"] = ids_sorted
    with open(dest_root / "meta_summary.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # round_001 marker
    (dest_root / "round_001").mkdir(exist_ok=True)

    print(f"  wrote {dest_root}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Merge timestamped meta_runs per model.")
    ap.add_argument("--dry-run", action="store_true", help="Print plan only")
    args = ap.parse_args()

    if not META.is_dir():
        print("No meta_runs/", file=sys.stderr)
        return 1

    # group: (model_key, rev) -> [(stamp, Path), ...]
    groups: Dict[Tuple[str, str], List[Tuple[str, Path]]] = {}
    for p in sorted(META.iterdir()):
        if not p.is_dir() or p.name.startswith("_"):
            continue
        parsed = parse_run_dir(p.name)
        if not parsed:
            continue
        mk, rev, stamp = parsed
        groups.setdefault((mk, rev), []).append((stamp, p))

    # Skip if canonical target already exists as ONLY dir? We still merge all timestamped into it.
    # Exclude destination names from sources if user re-runs script
    for key in list(groups.keys()):
        mk, rev = key
        canon = canonical_run_name(mk, rev)
        groups[key] = [(s, p) for s, p in groups[key] if p.name != canon]

    for key in groups:
        groups[key].sort(key=lambda x: x[0])

    if not groups:
        print("No matching new_*_*_no-reviewer_* dirs found.")
        return 0

    archive = META / f"_archive_merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not args.dry_run:
        archive.mkdir(parents=True, exist_ok=True)

    for (mk, rev), lst in sorted(groups.items(), key=lambda x: x[0][0]):
        if not lst:
            continue
        canon_path = META / canonical_run_name(mk, rev)
        run_list: List[Tuple[str, Path]] = list(lst)
        if (
            canon_path.is_dir()
            and (canon_path / OUTER_REL / RESULTS_NAME).is_file()
            and not any(p.resolve() == canon_path.resolve() for _s, p in lst)
        ):
            run_list = [("00000000_000000", canon_path)] + run_list
        merge_model(mk, rev, run_list, args.dry_run)
        if args.dry_run:
            continue
        # move source runs into archive
        dest_root = META / canonical_run_name(mk, rev)
        for _stamp, p in lst:
            if p.resolve() == dest_root.resolve():
                continue
            target = archive / p.name
            if target.exists():
                target = archive / f"{p.name}_dup"
            shutil.move(str(p), str(target))
            print(f"  archived {p.name} -> {target.relative_to(META)}")

    if not args.dry_run:
        print(f"\nArchived old runs under: {archive.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
