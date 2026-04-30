"""Render a compact markdown table of themes from outputs/thematic_analysis_parsed.json."""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path('outputs')


def md_escape(s: str) -> str:
    return (s or '').replace('\n',' ').replace('|','\\|').strip()


def main():
    p = OUT_DIR / 'thematic_analysis_parsed.json'
    obj = json.loads(p.read_text())
    if not isinstance(obj, dict) or 'themes' not in obj:
        (OUT_DIR / 'themes_table.md').write_text("(Thematic analysis JSON not available.)\n")
        return

    lines = []
    lines.append('| Theme | Definition (abridged) | Prevalence estimate (transit vs car) |')
    lines.append('|---|---|---|')
    for t in obj['themes']:
        name = md_escape(t.get('theme_name',''))
        definition = md_escape(t.get('definition',''))
        definition = definition[:140] + ('…' if len(definition) > 140 else '')
        prev = t.get('prevalence_estimate', {})
        if isinstance(prev, dict):
            pv = f"{prev.get('transit_primary','?')} vs {prev.get('car_primary','?')}"
        else:
            pv = md_escape(str(prev))
        lines.append(f"| {name} | {definition} | {pv} |")

    (OUT_DIR / 'themes_table.md').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
