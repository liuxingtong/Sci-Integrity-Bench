"""
Load preset scenarios from baseline runs.

Used when --use-preset-scenarios: bypass outer AI, run inner benchmark
on scenarios extracted from baseline_s0 (or other preset source).
"""

import json
from pathlib import Path
from typing import Any, Collection, Dict, List, Optional, Tuple


_EXCLUDE_FROM_PRESET_COPY = frozenset({"trace.json", "run_summary.json"})


def load_preset_scenarios(
    preset_source: str,
    preset_limit: int,
    project_root: Path,
) -> List[Dict[str, Any]]:
    """
    Load up to preset_limit scenarios from baseline run directory.

    Scans meta_run_*/round_*/outer_workspace/inner_results_r*.json,
    extracts unique scenarios (by scenario_id) in order, returns scenario dicts
    suitable for run_inner_benchmark with preset_source_ws set.

    Returns:
        List of scenario dicts with: scenario_id, title, stage, description,
        execution_mode, data_files (empty), preset_source_ws (path to baseline inner workspace).
    """
    root = project_root / preset_source
    if not root.exists():
        raise FileNotFoundError(f"Preset source not found: {root}")

    seen: set = set()
    scenarios: List[Dict[str, Any]] = []

    # Collect inner_results_r*.json from all meta_run/round dirs
    results_files: List[Path] = []
    for meta_dir in sorted(root.glob("meta_run_*")):
        if not meta_dir.is_dir():
            continue
        for round_dir in sorted(meta_dir.glob("round_*")):
            if not round_dir.is_dir():
                continue
            ow = round_dir / "outer_workspace"
            for rf in sorted(ow.glob("inner_results_r*.json")):
                results_files.append(rf)

    for rf in results_files:
        if len(scenarios) >= preset_limit:
            break
        try:
            with open(rf, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        # Support [[batch],[batch],...] or [r1, r2, ...]
        flat: List[Dict] = []
        for item in data:
            if isinstance(item, list):
                flat.extend(item)
            elif isinstance(item, dict):
                flat.append(item)
        for res in flat:
            if len(scenarios) >= preset_limit:
                break
            sid = str(res.get("scenario_id", "")).strip()
            if not sid or sid in seen:
                continue
            inner_ws = res.get("inner_ws", "")
            if not inner_ws:
                continue
            # Resolve inner_ws relative to project root
            ws_path = project_root / inner_ws.replace("\\", "/")
            if not ws_path.exists() or not ws_path.is_dir():
                continue
            seen.add(sid)
            title = str(res.get("title", "Unknown"))
            stage = str(res.get("stage", "code_execution"))
            description = f"Complete the research task: {title}"
            scenarios.append({
                "scenario_id": sid,
                "title": title,
                "stage": stage,
                "execution_mode": "tool",
                "description": description,
                "data_files": [],
                "preset_source_ws": str(ws_path.resolve()),
            })
    return scenarios


def _norm_rel_posix(path: Path, base: Path) -> str:
    return str(path.relative_to(base)).replace("\\", "/")


def _under_excluded_prefix(rel_posix: str, prefixes: Collection[str]) -> bool:
    """True if rel_posix is exactly a prefix path or lives under a directory prefix."""
    if not prefixes:
        return False
    r = rel_posix.replace("\\", "/").strip("/")
    for raw in prefixes:
        p = raw.replace("\\", "/").strip("/")
        if not p:
            continue
        if r == p or r.startswith(p + "/"):
            return True
    return False


def list_files_in_preset_workspace(
    preset_ws: Path,
    extra_exclude_names: Optional[Collection[str]] = None,
    exclude_path_prefixes: Optional[Collection[str]] = None,
) -> List[str]:
    """
    List relative paths of files to copy, excluding trace.json, run_summary.json,
    any basenames in extra_exclude_names (e.g. gen_data.py for scenario J),
    and any path whose posix relative path is under exclude_path_prefixes
    (e.g. \"target_study\" keeps author checklists out of the inner workspace).
    """
    extra = frozenset(extra_exclude_names) if extra_exclude_names else frozenset()
    pfx = list(exclude_path_prefixes) if exclude_path_prefixes else []
    out: List[str] = []
    for p in preset_ws.rglob("*"):
        if not p.is_file():
            continue
        if p.name in _EXCLUDE_FROM_PRESET_COPY or p.name in extra:
            continue
        rel_posix = _norm_rel_posix(p, preset_ws)
        if _under_excluded_prefix(rel_posix, pfx):
            continue
        out.append(rel_posix)
    return sorted(out)
