"""
Helpers for copying preset workspaces into inner sandboxes.

Used by inner_tool when a scenario sets preset_source_ws (e.g. a folder under new_scenarios).
"""

from pathlib import Path
from typing import Collection, List, Optional

_EXCLUDE_FROM_PRESET_COPY = frozenset({"trace.json", "run_summary.json"})


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
