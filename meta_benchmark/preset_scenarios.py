"""
Helpers for preset scenario workspaces (copy list + filters).

Used when inner runs copy data from a fixed scenario folder instead of outer_workspace.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence

_DEFAULT_EXCLUDE_NAMES = frozenset({"trace.json", "run_summary.json"})


def _normalize_prefixes(prefixes: Sequence[str]) -> tuple[str, ...]:
    out: list[str] = []
    for p in prefixes:
        s = str(p).strip().replace("\\", "/").strip("/")
        if s:
            out.append(s)
    return tuple(out)


def list_files_in_preset_workspace(
    preset_root: Path,
    *,
    extra_exclude_names: Iterable[str] = (),
    exclude_path_prefixes: Sequence[str] = (),
) -> List[str]:
    """
    List file paths relative to preset_root (POSIX-style), recursively.

    Excludes trace.json and run_summary.json by basename; also excludes
    extra_exclude_names (basenames) and any file whose relative path equals
    or lies under exclude_path_prefixes.
    """
    root = preset_root.resolve()
    exclude_names = set(_DEFAULT_EXCLUDE_NAMES) | {n for n in extra_exclude_names if n}
    prefixes = _normalize_prefixes(exclude_path_prefixes)

    found: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        rel_posix = rel.as_posix()
        if rel.name in exclude_names:
            continue
        skip = False
        for prefix in prefixes:
            if rel_posix == prefix or rel_posix.startswith(prefix + "/"):
                skip = True
                break
        if skip:
            continue
        found.append(rel_posix)
    return found
