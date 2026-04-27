"""Update report/report.md with computed corpus statistics.

This script replaces the Data overview table and the 'Most frequent units' bullet list
with values computed from outputs/mentions.csv and outputs/actions.csv.

It is intentionally narrow and uses regex-based replacement for reproducibility.
"""

from __future__ import annotations

import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report" / "report.md"
SCRATCH = ROOT / "data" / "lab_scratch.txt"
MENTIONS = ROOT / "outputs" / "mentions.csv"
ACTIONS = ROOT / "outputs" / "actions.csv"


def main():
    rep = REPORT.read_text(encoding="utf-8")

    text = SCRATCH.read_text(errors="ignore")
    n_lines = len(text.splitlines())
    n_chars = len(text)

    m = pd.read_csv(MENTIONS)
    n_mentions = len(m)
    n_units = m["unit"].nunique()

    n_action_lines = 0
    if ACTIONS.exists():
        n_action_lines = len(pd.read_csv(ACTIONS))

    top_units = m["unit"].value_counts().head(8)
    top_bullets = "\n".join([f"- {u}: {int(c)}" for u, c in top_units.items()])

    # Replace the numeric table block
    table_re = re.compile(
        r"\| Item \| Value \|\n\|---\|---:\|\n"
        r"\| Lines in `lab_scratch\.txt` \| .*? \|\n"
        r"\| Characters \| .*? \|\n"
        r"\| Quantitative mentions \(value\+unit\) \| .*? \|\n"
        r"\| Unique units observed \| .*? \|\n"
        r"\| Action-bearing lines \| .*? \|\n",
        flags=re.MULTILINE,
    )

    new_table = (
        "| Item | Value |\n"
        "|---|---:|\n"
        f"| Lines in `lab_scratch.txt` | {n_lines} |\n"
        f"| Characters | {n_chars} |\n"
        f"| Quantitative mentions (value+unit) | {n_mentions} |\n"
        f"| Unique units observed | {n_units} |\n"
        f"| Action-bearing lines | {n_action_lines} |\n"
    )

    rep2, n_sub = table_re.subn(new_table, rep)
    if n_sub != 1:
        raise RuntimeError(f"Expected to replace 1 table block, replaced {n_sub}.")

    # Replace top units bullets under the marker
    marker = "**Most frequent units (top 8):** (see Fig. 2 for full plot)"
    if marker not in rep2:
        raise RuntimeError("Marker for top units not found.")

    rep3 = re.sub(
        re.escape(marker) + r"\n\n(?:- .*\n){1,20}",
        marker + "\n\n" + top_bullets + "\n",
        rep2,
        flags=re.MULTILINE,
    )

    REPORT.write_text(rep3, encoding="utf-8")


if __name__ == "__main__":
    main()
