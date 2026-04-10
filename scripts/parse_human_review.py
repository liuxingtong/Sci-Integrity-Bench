"""
Parse and validate machine_readable data from a human review .md.

Primary source: Markdown narrative (## 1) 审查说明 …), see scripts/human_review_narrative.py
and docs/AI_scientist_机器解析规则.yaml → narrative_parse.

Legacy: optional ```yaml``` machine_readable block is still accepted when --source auto
and narrative does not validate (unmigrated files).

Usage:
  python scripts/parse_human_review.py <path-to-review.md>
  python scripts/parse_human_review.py <path.md> --source narrative
  python scripts/parse_human_review.py <path.md> --source legacy-yaml
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Missing dependency: PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    raise SystemExit(1)

from human_review_narrative import parse_narrative_to_machine_readable

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "docs" / "AI_scientist_机器解析规则.yaml"

ENUMS = {
    "hint_leak": {"yes", "no"},
    "final_verdict": {"pass", "fail", "needs_review", "invalid_due_to_hint_leak"},
    "trap_verdict": {"hit", "not_hit", "uncertain"},
    "evidence_source": {"report", "trace", "run_summary", "output_file", "code"},
    "supports": {"hit", "not_hit", "uncertain"},
}


def extract_yaml_block(text: str) -> str | None:
    for m in re.finditer(r"^```yaml\s*\r?\n(.*?)^```", text, flags=re.MULTILINE | re.DOTALL):
        block = m.group(1)
        if "machine_readable:" in block:
            return block
    return None


def try_parse_legacy_yaml_machine_readable(text: str) -> tuple[dict[str, Any] | None, list[str]]:
    block = extract_yaml_block(text)
    if not block:
        return None, []
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as e:
        return None, [f"YAML parse error: {e}"]
    if not isinstance(data, dict) or not isinstance(data.get("machine_readable"), dict):
        return None, ["YAML: root must be a mapping with key machine_readable."]
    mr = data["machine_readable"]
    if not isinstance(mr, dict):
        return None, ["machine_readable must be a mapping."]
    return mr, []


def validate(mr: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    req = ["run_id", "scenario_id", "hint_leak", "final_verdict", "trap_results", "evidence"]
    for k in req:
        if k not in mr:
            errs.append(f"missing required key: {k}")

    if errs:
        return errs

    for k in ("run_id", "scenario_id"):
        v = mr.get(k)
        if not isinstance(v, str) or len(v.strip()) < 1:
            errs.append(f"{k} must be a non-empty string")

    hl = mr.get("hint_leak")
    if hl not in ENUMS["hint_leak"]:
        errs.append(f"hint_leak must be one of {sorted(ENUMS['hint_leak'])}, got {hl!r}")

    fv = mr.get("final_verdict")
    if fv not in ENUMS["final_verdict"]:
        errs.append(f"final_verdict must be one of {sorted(ENUMS['final_verdict'])}, got {fv!r}")

    if hl == "yes" and fv != "invalid_due_to_hint_leak":
        errs.append("cross_field: hint_leak=yes requires final_verdict=invalid_due_to_hint_leak")

    tr = mr.get("trap_results")
    if not isinstance(tr, list) or len(tr) < 1:
        errs.append("trap_results must be a non-empty list")
    else:
        for i, item in enumerate(tr):
            if not isinstance(item, dict):
                errs.append(f"trap_results[{i}] must be a mapping")
                continue
            for k in ("trap_id", "verdict"):
                if k not in item:
                    errs.append(f"trap_results[{i}] missing {k}")
            tid = item.get("trap_id")
            if isinstance(tid, str) and len(tid.strip()) < 1:
                errs.append(f"trap_results[{i}].trap_id must be non-empty")
            ver = item.get("verdict")
            if ver is not None and ver not in ENUMS["trap_verdict"]:
                errs.append(f"trap_results[{i}].verdict invalid: {ver!r}")

    ev = mr.get("evidence")
    if not isinstance(ev, list) or len(ev) < 2:
        errs.append("evidence must be a list with at least 2 items")
    else:
        for i, item in enumerate(ev):
            if not isinstance(item, dict):
                errs.append(f"evidence[{i}] must be a mapping")
                continue
            for k in ("source", "snippet", "supports"):
                if k not in item:
                    errs.append(f"evidence[{i}] missing {k}")
            src = item.get("source")
            if src is not None and src not in ENUMS["evidence_source"]:
                errs.append(f"evidence[{i}].source invalid: {src!r}")
            snip = item.get("snippet")
            if not isinstance(snip, str) or len(snip.strip()) < 1:
                errs.append(f"evidence[{i}].snippet must be a non-empty string")
            sup = item.get("supports")
            if sup is not None and sup not in ENUMS["supports"]:
                errs.append(f"evidence[{i}].supports invalid: {sup!r}")

    if "notes" in mr and mr["notes"] is not None and not isinstance(mr["notes"], str):
        errs.append("notes must be a string if present")

    return errs


def load_machine_readable(text: str, *, source: str) -> tuple[dict[str, Any] | None, list[str]]:
    if source == "narrative":
        mr, perr = parse_narrative_to_machine_readable(text)
        if mr is None:
            return None, perr
        verr = validate(mr)
        if verr:
            return None, [f"narrative: {x}" for x in verr]
        return mr, []

    if source == "legacy-yaml":
        ymr, yperr = try_parse_legacy_yaml_machine_readable(text)
        if ymr is None:
            return None, yperr if yperr else ["No ```yaml``` code block containing machine_readable."]
        verr = validate(ymr)
        if verr:
            return None, [f"legacy-yaml: {x}" for x in verr]
        return ymr, []

    # auto — Markdown 正文优先；仅当正文无法通过校验时再尝试旧版 YAML 块
    mr, perr = parse_narrative_to_machine_readable(text)
    if mr is not None:
        verr = validate(mr)
        if not verr:
            return mr, []

    ymr, yperr = try_parse_legacy_yaml_machine_readable(text)
    if ymr is not None:
        yverr = validate(ymr)
        if not yverr:
            return ymr, []

    errs: list[str] = []
    if mr is not None:
        errs.extend(f"narrative invalid: {x}" for x in validate(mr))
    else:
        errs.extend(perr)
    if ymr is not None:
        errs.extend(f"legacy yaml invalid: {x}" for x in validate(ymr))
    else:
        errs.extend(yperr)
    if not errs:
        errs.append("Could not obtain valid machine_readable from narrative or legacy YAML.")
    return None, errs


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Parse and validate human review machine_readable from Markdown (and optionally legacy YAML)."
    )
    ap.add_argument("path", type=Path, help="Path to human_reviews/<scenario_id>.md")
    ap.add_argument(
        "--source",
        choices=("narrative", "legacy-yaml", "auto"),
        default="auto",
        help="narrative=§1 only; legacy-yaml=```yaml``` only; auto=narrative first, else legacy yaml (default)",
    )
    args = ap.parse_args()
    path: Path = args.path
    if not path.is_file():
        print(f"Not a file: {path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    mr, load_errs = load_machine_readable(text, source=args.source)
    if mr is None:
        for e in load_errs:
            print(e, file=sys.stderr)
        print(json.dumps({"ok": False, "errors": load_errs}, ensure_ascii=False, indent=2))
        sys.exit(3)

    errs = validate(mr)
    rules_rel = str(RULES_PATH.relative_to(ROOT)).replace("\\", "/")
    out = {"ok": len(errs) == 0, "rules_file": rules_rel, "machine_readable": mr}
    if errs:
        out["errors"] = errs

    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if not errs else 5)


if __name__ == "__main__":
    main()
