#!/usr/bin/env python3
"""Insert academic-style headings and **目录名:** lines into docs/TASK_INFO_REGISTER.md."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "docs" / "TASK_INFO_REGISTER.md"
TITLES = ROOT / "docs" / "_scenario_register_titles.json"


def main() -> None:
    titles: dict[str, dict[str, str]] = json.loads(TITLES.read_text(encoding="utf-8"))
    text = MD.read_text(encoding="utf-8")
    parts = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    out: list[str] = [parts[0]]
    for part in parts[1:]:
        line0, _, body = part.partition("\n")
        head = line0.strip()
        m = re.match(r"^##\s+(\d{2}[a-z]_[A-Za-z0-9_]+)\s*$", head)
        if not m:
            out.append(part)
            continue
        sid = m.group(1)
        if sid not in titles:
            raise KeyError(f"No title mapping for {sid}")
        if body.lstrip().startswith("**目录名：**"):
            out.append(part)
            continue
        zh = titles[sid]["zh"]
        out.append(f"## {zh}\n\n**目录名：** `{sid}`\n\n{body}")
    MD.write_text("".join(out), encoding="utf-8", newline="\n")
    print(f"Updated {MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
