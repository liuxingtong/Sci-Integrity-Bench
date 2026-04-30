#!/usr/bin/env python3
"""Convert docs/TASK_INFO_REGISTER_en.md to a LaTeX appendix fragment.

This version avoids `listings` so the appendix remains stable across templates.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "docs" / "TASK_INFO_REGISTER_en.md"
OUT = ROOT / "docs" / "TASK_INFO_REGISTER_appendix_en.tex"


def latex_escape_text(s: str) -> str:
    """Escape LaTeX-sensitive characters in normal text mode."""
    return (
        s.replace("\\", "\\textbackslash{}")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("#", "\\#")
        .replace("&", "\\&")
        .replace("$", "\\$")
    )


def json_block_label(body: str) -> str:
    t = body.strip()
    if not t:
        return "JSON"
    if t.startswith("["):
        return r"\texttt{checklist} (array)"
    if t.startswith("{"):
        if '"task"' in t and '"data"' in t:
            return r"\texttt{task\_info.json}"
        head = t[:2000]
        if '"scenario"' in head and '"checks"' in head:
            return r"\texttt{checklist} (object)"
        if '"trap"' in head:
            return r"\texttt{checklist} (object)"
    return "JSON"


def markdown_inline_to_latex_text(s: str) -> str:
    """Best-effort conversion for simple markdown inline markers."""
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = s.replace(r"\%", "%")
    s = s.replace(r"\_", "_")
    s = s.replace(r"\\ ", " ")
    s = s.replace("\\ ", " ")
    return s.strip()


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def extract_task_brief(task_text: str) -> str:
    m = re.search(r"Task Description\s*(.+?)(?:\n\n|$)", task_text, flags=re.DOTALL)
    if m:
        return normalize_ws(m.group(1))
    return normalize_ws(task_text)[:600]


def extract_deliverable(task_text: str) -> str:
    m = re.search(r"Deliverable:\s*(.+?)(?:\n|$)", task_text)
    return normalize_ws(m.group(1)) if m else ""


def render_task_info(obj: dict, lines: list[str]) -> None:
    lines.append(r"\paragraph{\texttt{task\_info.json} (structured).}")
    task_text = str(obj.get("task", ""))
    brief = extract_task_brief(task_text)
    deliverable = extract_deliverable(task_text)
    if brief:
        lines.append(r"\textbf{Task brief:} " + latex_escape_text(brief))
    if deliverable:
        lines.append(r"\textbf{Deliverable:} " + latex_escape_text(deliverable))

    data_items = obj.get("data", [])
    if isinstance(data_items, list) and data_items:
        lines.append(r"\textbf{Available data files:}")
        lines.append(r"\begin{itemize}")
        for item in data_items:
            if not isinstance(item, dict):
                continue
            name = latex_escape_text(str(item.get("name", "")))
            typ = latex_escape_text(str(item.get("type", "")))
            path = latex_escape_text(str(item.get("path", "")))
            desc = latex_escape_text(str(item.get("description", "")))
            lines.append(
                rf"\item \texttt{{{name}}} ({typ}) --- \texttt{{{path}}}. {desc}"
            )
        lines.append(r"\end{itemize}")
    lines.append("")


def render_checklist(obj: object, label: str, lines: list[str]) -> None:
    lines.append(rf"\paragraph{{{label} (structured).}}")
    items: list[dict] = []
    if isinstance(obj, list):
        items = [x for x in obj if isinstance(x, dict)]
    elif isinstance(obj, dict):
        trap = obj.get("trap")
        checks = obj.get("checks")
        if isinstance(trap, dict):
            items.append(trap)
        if isinstance(checks, list):
            items.extend([x for x in checks if isinstance(x, dict)])

    # Trap metadata first
    for it in items:
        if "trap_code" in it or "trap_name" in it or "trap_summary" in it:
            code = latex_escape_text(str(it.get("trap_code", "")))
            name = latex_escape_text(str(it.get("trap_name", "")))
            summary = latex_escape_text(str(it.get("trap_summary", "")))
            lines.append(r"\textbf{Trap metadata:}")
            lines.append(r"\begin{itemize}")
            if code:
                lines.append(rf"\item Code: \texttt{{{code}}}")
            if name:
                lines.append(rf"\item Name: {name}")
            if summary:
                lines.append(rf"\item Summary: {summary}")
            lines.append(r"\end{itemize}")
            break

    checks = [x for x in items if "content" in x]
    if checks:
        lines.append(r"\textbf{Evaluation checks:}")
        lines.append(r"\begin{itemize}")
        for ch in checks:
            content = latex_escape_text(normalize_ws(str(ch.get("content", ""))))
            keywords = ch.get("keywords")
            if isinstance(keywords, list) and keywords:
                kw = ", ".join(latex_escape_text(str(k)) for k in keywords[:6])
                lines.append(rf"\item {content} \emph{{Keywords:}} {kw}.")
            else:
                lines.append(rf"\item {content}")
        lines.append(r"\end{itemize}")
    lines.append("")


def emit_pre_block(lines: list[str], content: str) -> None:
    """Emit a raw preformatted block (stable across templates)."""
    lines.append(r"\begin{small}")
    lines.append(r"\begin{verbatim}")
    lines.append(content)
    lines.append(r"\end{verbatim}")
    lines.append(r"\end{small}")


def section_to_tex(subsection_title: str, body: str) -> str:
    lines: list[str] = []
    st = latex_escape_text(subsection_title)
    lines.append(f"\\subsection{{{st}}}")
    lines.append("")

    parts = body.split("```json")
    intro = parts[0].strip()
    intro = re.sub(r"\n*\*\*checklist\*\*\s*:\s*", "\n", intro, flags=re.DOTALL).strip()
    scenario_id = ""
    m_sid = re.search(r"\*\*Scenario ID:\*\*\s*`([^`]+)`", intro)
    if m_sid:
        scenario_id = m_sid.group(1).strip()
    intro = re.sub(r"\*\*Scenario ID:\*\*\s*`[^`]+`\s*", "", intro, count=1).strip()
    intro = re.sub(r"^\*\*Summary:\*\*\s*", "", intro, count=1).strip()
    summary_text = markdown_inline_to_latex_text(intro)

    if scenario_id:
        lines.append(r"\paragraph{Scenario ID.}")
        lines.append(rf"\texttt{{{latex_escape_text(scenario_id)}}}")
        lines.append("")
    if summary_text:
        lines.append(r"\paragraph{Summary.}")
        lines.append(latex_escape_text(summary_text))
        lines.append("")

    for chunk in parts[1:]:
        if "```" not in chunk:
            continue
        json_body, _, _tail = chunk.partition("```")
        json_body = json_body.strip("\n")
        label = json_block_label(json_body)
        parsed = None
        try:
            parsed = json.loads(json_body)
        except Exception:
            parsed = None

        if parsed is not None and label == r"\texttt{task\_info.json}" and isinstance(parsed, dict):
            render_task_info(parsed, lines)
        elif parsed is not None and "checklist" in label:
            render_checklist(parsed, label, lines)
        else:
            lines.append(rf"\paragraph{{{label}.}}")
            emit_pre_block(lines, json_body)
            lines.append("")

    return "\n".join(lines).rstrip() + "\n\n"


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    chunks = re.split(r"(?=^## )", md, flags=re.MULTILINE)
    header_chunk = chunks[0]
    # Strip main title and preamble horizontal rule for appendix intro paragraph
    header_lines = []
    for ln in header_chunk.splitlines():
        if ln.startswith("# "):
            title = ln[2:].strip()
            header_lines.append(title)
            continue
        if ln.strip() == "---":
            continue
        if ln.strip():
            header_lines.append(ln)

    intro_para = "\n".join(header_lines[1:]).strip() if len(header_lines) > 1 else ""

    blocks = [
        "% =============================================================================",
        "% English task information register — LaTeX appendix fragment",
        "% =============================================================================",
        "% Include from your main document (adjust path).",
        "% No extra LaTeX package required by this fragment.",
        "% =============================================================================",
        "% Source markdown: docs/TASK_INFO_REGISTER_en.md",
        "% Regenerate English MD: python tools/generate_task_info_register_en.py",
        "% Regenerate this .tex file: python tools/task_register_md_to_latex.py",
        "% =============================================================================",
    ]
    out: list[str] = list(blocks) + [""]

    out.append(r"\section{Task information register (English)}")
    out.append(r"\label{sec:appendix-task-info-register-en}")
    out.append("")
    out.append(
        r"\noindent\emph{This appendix mirrors \texttt{docs/TASK\_INFO\_REGISTER\_en.md}: "
        r"one subsection per scenario directory under \texttt{meta\_benchmark/new\_scenarios/}, "
        r"with an English summary and embedded JSON copies of \texttt{task\_info.json} and "
        r"\texttt{checklist}.}"
    )
    out.append("")
    if intro_para:
        out.append(latex_escape_text(markdown_inline_to_latex_text(intro_para)))
        out.append("")

    for ch in chunks[1:]:
        if not ch.strip():
            continue
        lines = ch.split("\n", 1)
        title = lines[0].strip()
        if not title.startswith("## "):
            continue
        subsection_title = title[3:].strip()
        body = lines[1] if len(lines) > 1 else ""
        out.append(section_to_tex(subsection_title, body))

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
