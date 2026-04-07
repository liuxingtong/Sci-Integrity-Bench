"""
Live visualization state emission.

When --viz is enabled, the meta-runner writes viz_state.json to the run directory
at key points. The live dashboard polls this file for real-time display.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def emit(run_dir: Optional[Path], state: Dict[str, Any]) -> None:
    """Write viz_state.json for live dashboard consumption."""
    if not run_dir or not run_dir.exists():
        return
    out = dict(state)
    out.setdefault("run_id", run_dir.name)
    out.setdefault("timestamp", datetime.now().isoformat())
    path = run_dir / "viz_state.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def emit_merge(run_dir: Optional[Path], updates: Dict[str, Any]) -> None:
    """Read existing viz_state.json, deep-merge updates, write back."""
    if not run_dir or not run_dir.exists():
        return
    path = run_dir / "viz_state.json"
    existing: Dict[str, Any] = {}
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
    _deep_merge(existing, updates)
    existing["timestamp"] = datetime.now().isoformat()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _deep_merge(base: Dict, updates: Dict) -> None:
    for k, v in updates.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def set_active_run(results_dir: Path, run_dir: Optional[Path]) -> None:
    """Mark which run is currently active for live viz (write to .live_run)."""
    marker = results_dir / ".live_run"
    try:
        if run_dir:
            marker.write_text(str(run_dir.resolve()), encoding="utf-8")
        elif marker.exists():
            marker.unlink()
    except Exception:
        pass
