"""Ensure scenario_trap_index.json has no deprecated `recommended_run_order` key."""
import json
from pathlib import Path

p = Path(__file__).resolve().parent / "_authoring_private" / "scenario_trap_index.json"
d = json.loads(p.read_text(encoding="utf-8"))
if d.pop("recommended_run_order", None) is not None:
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK removed recommended_run_order")
else:
    print("OK already absent")
