#!/usr/bin/env python3
"""Convert docs/TASK_INFO_REGISTER_en.md to a LaTeX appendix fragment."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "docs" / "TASK_INFO_REGISTER_en.md"
OUT = ROOT / "docs" / "TASK_INFO_REGISTER_appendix_en.tex"


def latex_escape_comment(s: str) -> str:
    """Escape % # & _ for use in optional short titles (not used if we use lstlisting)."""
    return (
        s.replace("\\", "\\textbackslash{}")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("#", "\\#")
        .replace("&", "\\&")
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


def section_to_tex(subsection_title: str, body: str) -> str:
    lines: list[str] = []
    st = latex_escape_comment(subsection_title)
    lines.append(f"\\subsection{{{st}}}")
    lines.append("")

    parts = body.split("```json")
    intro = parts[0].strip()
    intro = re.sub(r"^\*\*Summary:\*\*\s*", "", intro, flags=re.DOTALL).strip()
    intro = re.sub(
        r"\n*\*\*checklist\*\*\s*:\s*",
        "\n",
        intro,
        flags=re.DOTALL,
    ).strip()

    if intro:
        lines.append(r"\paragraph{Summary.}")
        lines.append(r"\begin{lstlisting}[basicstyle=\ttfamily\footnotesize,breaklines=true,breakatwhitespace=true]")
        lines.append(intro)
        lines.append(r"\end{lstlisting}")
        lines.append("")

    for chunk in parts[1:]:
        if "```" not in chunk:
            continue
        json_body, _, tail = chunk.partition("```")
        json_body = json_body.rstrip()
        label = json_block_label(json_body)
        lines.append(rf"\paragraph{{{label}.}}")
        lines.append(
            r"\begin{lstlisting}[language=json,basicstyle=\ttfamily\footnotesize,"
            r"breaklines=true,breakatwhitespace=true,frame=single]"
        )
        lines.append(json_body)
        lines.append(r"\end{lstlisting}")
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
        "% Include from your main document (adjust path). Requires:",
        "%   \\usepackage{listings}",
        "% Optional:",
        "%   \\usepackage{xcolor}",
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
        out.append(r"\begin{lstlisting}[basicstyle=\ttfamily\footnotesize,breaklines=true]")
        out.append(intro_para)
        out.append(r"\end{lstlisting}")
        out.append("")

    out.append(r"\lstdefinelanguage{json}{")
    out.append(r"  sensitive=false,")
    out.append(r'  morestring=[b]",')
    out.append(r"  morecomment=[l]{//},")
    out.append(r"}")

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
