"""
Deterministic extraction of machine_readable fields from the narrative section of a human review .md.

Stops before ``## 2) 结构化记录`` (legacy) if present, else before ``## C)`` checklist, so the checklist is not parsed.
"""

from __future__ import annotations

import re
from typing import Any


def _narrative_only(text: str) -> str:
    m2 = text.find("## 2) 结构化记录")
    if m2 >= 0:
        return text[:m2]
    m = re.search(r"(?m)^## C\)", text)
    if m:
        return text[: m.start()]
    return text


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _is_fullwidth_paren_hint_line(text: str) -> bool:
    """Template-only lines under 摘录, e.g. （多行正文：…） or （同上）."""
    s = text.strip()
    return len(s) >= 2 and s.startswith("（") and s.endswith("）")


def _strip_template_value(raw: str) -> str:
    s = raw.strip()
    if s.startswith("`") and s.endswith("`"):
        s = s[1:-1].strip()
    return s


def _is_placeholder_hint_leak(s: str) -> bool:
    t = _strip_template_value(s).lower()
    return "/" in t or ("yes" in t and "no" in t and len(t) < 20)


def _is_placeholder_final_verdict(s: str) -> bool:
    t = _strip_template_value(s).lower()
    return "/" in t or ("pass" in t and "fail" in t and "needs_review" in t)


def _parse_kv_list_item(pattern: re.Pattern[str], lines: list[str]) -> str | None:
    for line in lines:
        m = pattern.match(line)
        if m:
            return m.group(1).strip()
    return None


def _parse_traps(lines: list[str]) -> list[dict[str, str]]:
    """After heading ### 5. 陷阱点… collect `- T01: hit` style lines until next ### or ##."""
    start = -1
    for i, line in enumerate(lines):
        if re.match(r"^#{1,3}\s+5\.\s*陷阱点", line):
            start = i + 1
            break
    if start < 0:
        return []

    traps: list[dict[str, str]] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if re.match(r"^#{1,3}\s", line) or re.match(r"^##\s", line):
            break
        m = re.match(r"^\s*-\s*([A-Za-z0-9_.-]+)\s*[:：]\s*(hit|not_hit|uncertain)\b", line)
        if m:
            traps.append({"trap_id": m.group(1), "verdict": m.group(2)})
            i += 1
            continue
        m2 = re.match(
            r"^\s*-\s*trap_id\s*[:：]\s*(\S+)\s+verdict\s*[:：]\s*(hit|not_hit|uncertain)\b",
            line,
            re.I,
        )
        if m2:
            traps.append({"trap_id": m2.group(1), "verdict": m2.group(2)})
        i += 1
    return traps


_EXCERPT_START = re.compile(r"^(\s*-\s*摘录\s*[:：]\s*)(.*)$")


def _excerpt_under_line(lines: list[str], idx: int) -> str:
    line = lines[idx]
    m = _EXCERPT_START.match(line)
    if not m:
        return ""
    first = m.group(2).strip()
    base = _line_indent(line)
    chunks: list[str] = []
    if first and not _is_fullwidth_paren_hint_line(first):
        chunks.append(first)
    j = idx + 1
    while j < len(lines):
        L = lines[j]
        if not L.strip():
            chunks.append("")
            j += 1
            continue
        ind = _line_indent(L)
        if ind <= base:
            break
        if _is_fullwidth_paren_hint_line(L):
            j += 1
            continue
        chunks.append(L.strip())
        j += 1
    return "\n".join(chunks).strip()


def _slice_between_headings(lines: list[str], start_pat: str, stop_pat: str | None) -> list[str]:
    start_i = stop_i = -1
    for i, line in enumerate(lines):
        if start_i < 0 and re.match(start_pat, line):
            start_i = i
            continue
        if start_i >= 0 and stop_pat and re.match(stop_pat, line):
            stop_i = i
            break
    if start_i < 0:
        return []
    if stop_i < 0:
        return lines[start_i + 1 :]
    return lines[start_i + 1 : stop_i]


def _parse_supports(sub_lines: list[str], key: str) -> str | None:
    pat = re.compile(rf"^\s*-\s*{re.escape(key)}\s*[:：]\s*(hit|not_hit|uncertain)\b", re.I)
    for line in sub_lines:
        m = pat.match(line)
        if m:
            return m.group(1)
    return None


def _find_excerpt_in_block(block_lines: list[str]) -> str:
    for i, line in enumerate(block_lines):
        if _EXCERPT_START.match(line):
            return _excerpt_under_line(block_lines, i)
    return ""


def parse_narrative_to_machine_readable(text: str) -> tuple[dict[str, Any] | None, list[str]]:
    """
    Returns (machine_readable dict, parse_errors). On success errors is empty.
    """
    errs: list[str] = []
    body = _narrative_only(text)
    lines = body.splitlines()

    run_id = _parse_kv_list_item(re.compile(r"^\s*-\s*run_id\s*[:：]\s*(.+?)\s*$"), lines)
    scenario_id = _parse_kv_list_item(re.compile(r"^\s*-\s*scenario_id\s*[:：]\s*(.+?)\s*$"), lines)
    if not run_id:
        errs.append("narrative: missing `- run_id: ...` under 基本信息")
    if not scenario_id:
        errs.append("narrative: missing `- scenario_id: ...` under 基本信息")

    hint_leak: str | None = None
    final_verdict: str | None = None
    notes = ""
    for line in lines:
        hm = re.match(r"^\s*-\s*hint_leak\s*[:：]\s*(.+?)\s*$", line)
        if hm:
            cand = _strip_template_value(hm.group(1))
            if cand in ("yes", "no") and not _is_placeholder_hint_leak(hm.group(1)):
                hint_leak = cand
            continue
        fm = re.match(r"^\s*-\s*final_verdict\s*[:：]\s*(.+?)\s*$", line)
        if fm:
            cand = _strip_template_value(fm.group(1))
            if cand in ("pass", "fail", "needs_review", "invalid_due_to_hint_leak") and not _is_placeholder_final_verdict(
                fm.group(1)
            ):
                final_verdict = cand
            continue
        nm = re.match(r"^\s*-\s*一句话结论\s*[:：]\s*(.*)$", line)
        if nm:
            notes = nm.group(1).strip()

    if hint_leak is None:
        errs.append(
            "narrative: set `- hint_leak: yes` or `- hint_leak: no` (replace template placeholder in 结论概述)"
        )
    if final_verdict is None:
        errs.append(
            "narrative: set `- final_verdict: pass|fail|needs_review|invalid_due_to_hint_leak` "
            "(replace template placeholder)"
        )

    trap_results = _parse_traps(lines)
    if not trap_results:
        errs.append(
            "narrative: add `### 5. 陷阱点判定（机读）` with lines like `- T01: hit` "
            "(verdict: hit | not_hit | uncertain)"
        )

    sec4 = _slice_between_headings(lines, r"^#{1,3}\s+4\.\s*证据摘录", r"^#{1,3}\s+5\.\s*陷阱点|^##\s")
    if not sec4:
        sec4 = _slice_between_headings(lines, r"^#{1,3}\s+4\.\s*证据", r"^#{1,3}\s+5\.|^##\s")

    report_block = _slice_between_headings(sec4, r"^\s*-\s*报告证据", r"^\s*-\s*轨迹证据")
    trace_block = _slice_between_headings(sec4, r"^\s*-\s*轨迹证据", None)

    report_snip = _find_excerpt_in_block(report_block)
    trace_snip = _find_excerpt_in_block(trace_block)

    report_sup = _parse_supports(sec4, "report_supports") or "uncertain"
    trace_sup = _parse_supports(sec4, "trace_supports") or "uncertain"

    if not report_snip:
        errs.append("narrative: under 报告证据, fill `- 摘录：` with non-empty text (multi-line indent under 摘录)")
    if not trace_snip:
        errs.append("narrative: under 轨迹证据, fill `- 摘录：` with non-empty text")

    if errs:
        return None, errs

    assert hint_leak is not None and final_verdict is not None

    mr: dict[str, Any] = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "hint_leak": hint_leak,
        "final_verdict": final_verdict,
        "notes": notes,
        "trap_results": trap_results,
        "evidence": [
            {"source": "report", "snippet": report_snip, "supports": report_sup},
            {"source": "trace", "snippet": trace_snip, "supports": trace_sup},
        ],
    }
    return mr, []
