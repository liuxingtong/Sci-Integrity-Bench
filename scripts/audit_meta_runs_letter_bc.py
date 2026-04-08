#!/usr/bin/env python3
"""Audit meta_runs: per model, letter b and c should each have 11 scenarios with results."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "meta_runs"
INNER = Path("round_001/inner_workspaces/round_001")
RES = Path("round_001/outer_workspace/inner_results_r001.json")

_LETTER = re.compile(r"^(\d{2})([a-z])_")


def letter_from_sid(sid: str) -> str | None:
    m = _LETTER.match(sid)
    return m.group(2) if m else None


def audit_run(run_dir: Path) -> dict | None:
    inner = run_dir / INNER
    if not inner.is_dir():
        return None
    res_path = run_dir / RES
    ids = sorted([p.name for p in inner.iterdir() if p.is_dir()])
    letters: dict[str, list[str]] = defaultdict(list)
    for sid in ids:
        L = letter_from_sid(sid)
        if L:
            letters[L].append(sid)

    batch: list | str = []
    if res_path.is_file():
        try:
            batch = json.loads(res_path.read_text(encoding="utf-8"))[0]
        except Exception as e:
            batch = f"READ_ERR: {e}"
    else:
        batch = []

    def summarize(letter: str) -> dict:
        sids = sorted(letters.get(letter, []))
        n = len(sids)
        if not isinstance(batch, list):
            return {
                "n_dirs": n,
                "n_json": None,
                "done": None,
                "fail": None,
                "error": None,
                "sids": sids,
            }
        idset = set(sids)
        rows = [r for r in batch if str(r.get("scenario_id", "")) in idset]
        st: dict[str, int] = defaultdict(int)
        for r in rows:
            st[str(r.get("status", "?"))] += 1
        return {
            "n_dirs": n,
            "n_json": len(rows),
            "done": st.get("Done", 0),
            "fail": st.get("Fail", 0),
            "error": st.get("Error", 0),
            "sids": sids,
        }

    return {
        "letters": {L: summarize(L) for L in sorted(letters.keys())},
        "has_results_file": res_path.is_file(),
    }


def model_key_from_run_id(name: str) -> str:
    m = re.match(r"^new_(.+?)_(?:no-)?reviewer_\d{8}_\d{6}$", name)
    return m.group(1) if m else name


def main() -> int:
    runs: list[dict] = []
    for d in sorted(META.iterdir()):
        if not d.is_dir():
            continue
        info = audit_run(d)
        if info is None:
            continue
        info["run_id"] = d.name
        info["model_key"] = model_key_from_run_id(d.name)
        runs.append(info)

    by_model: dict[str, list[dict]] = defaultdict(list)
    for r in runs:
        by_model[r["model_key"]].append(r)

    print("# meta_runs letter b / c audit (expect 11 dirs per letter, all Done for 'full pass')\n")

    issues: list[str] = []

    for mk in sorted(by_model.keys()):
        grp = by_model[mk]
        print(f"## Model: `{mk}`\n")
        for letter in ("b", "c"):
            full = []
            partial = []
            for r in grp:
                L = r["letters"].get(letter)
                if not L:
                    continue
                n = L["n_dirs"]
                if n == 11:
                    full.append((r["run_id"], L, r.get("has_results_file")))
                elif n > 0:
                    partial.append((r["run_id"], L))

            print(f"### Letter **{letter}** (need 11 scenarios)\n")
            if not full and not partial:
                print("- No inner workspace folders for this letter in any batch.\n")
                issues.append(f"{mk} letter {letter}: MISSING entire letter batch (0/11 dirs).")
                continue

            if full:
                # pick canonical: prefer all Done; else list all full-11 runs
                for rid, L, has_res in sorted(full, key=lambda x: (-(x[1].get("done") or -1), x[0])):
                    d_, f_, e_ = L.get("done"), L.get("fail"), L.get("error")
                    status_note = f"Done={d_} Fail={f_} Err={e_}"
                    if d_ == 11:
                        print(f"- OK (11/11 Done): `{rid}` -- {status_note}, has inner_results={has_res}")
                    elif d_ == 0 and f_ == 11:
                        print(f"- NEED RE-RUN (11 dirs but all Fail): `{rid}` -- {status_note}")
                        issues.append(f"{mk} {letter}: {rid} -- 11 Fail, re-run with higher steps or fix tool format.")
                    elif e_ == 11:
                        print(f"- NEED RE-RUN (11 dirs but all Error): `{rid}` -- {status_note}")
                        issues.append(f"{mk} {letter}: {rid} -- 11 Error, re-run.")
                    else:
                        print(f"- NEED RE-RUN (incomplete Done): `{rid}` -- {status_note}")
                        issues.append(f"{mk} {letter}: {rid} -- only {d_}/11 Done, re-run failed/error IDs.")

            if not full:
                print("- No batch has **11** scenario directories for this letter.")
                issues.append(f"{mk} letter {letter}: no full batch of 11 dirs.")

            for rid, L in partial:
                print(
                    f"- ORPHAN / INCOMPLETE ({L['n_dirs']}/11 dirs): `{rid}` -- "
                    f"{L['sids'][:3]}{'...' if len(L['sids']) > 3 else ''}"
                )
                issues.append(f"{mk} {letter}: orphan `{rid}` ({L['n_dirs']} dirs) -- re-run full `--letter {letter}` or merge.")
            print()

    if issues:
        print("---\n## Action list (must re-run or merge)\n")
        for line in issues:
            print(f"- {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
