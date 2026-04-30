"""Fill placeholders in report/report.md with LLM thematic outputs (if available)."""

from __future__ import annotations

import json
from pathlib import Path

REPORT_PATH = Path('report/report.md')
OUT_DIR = Path('outputs')


def main():
    md = REPORT_PATH.read_text()

    # Themes table
    themes_table = (OUT_DIR / 'themes_table.md').read_text() if (OUT_DIR / 'themes_table.md').exists() else "(No theme table.)\n"

    # Tensions and synthesis from parsed JSON
    tensions_block = "(Thematic analysis output not available.)"
    synth_block = "(Thematic analysis output not available.)"

    p = OUT_DIR / 'thematic_analysis_parsed.json'
    if p.exists():
        obj = json.loads(p.read_text())
        if isinstance(obj, dict) and 'tensions' in obj:
            tens = obj.get('tensions')
            if isinstance(tens, list) and tens:
                lines = []
                for t in tens[:6]:
                    if isinstance(t, dict):
                        name = t.get('tension_name') or t.get('name') or 'Tension'
                        desc = t.get('description') or ''
                        lines.append(f"- **{name}**: {desc}".strip())
                        quotes = t.get('evidence') or t.get('quotes') or []
                        # include up to 2 quotes
                        for q in quotes[:2]:
                            if isinstance(q, dict):
                                qt = (q.get('quote') or '').replace('\n',' ').strip()
                                rid = q.get('respondent_id','')
                                coh = q.get('cohort','')
                                if qt:
                                    lines.append(f"  - \"{qt}\" ({rid}, {coh})")
                            elif isinstance(q, str) and q.strip():
                                lines.append(f"  - \"{q.strip()}\"")
                tensions_block = "\n".join(lines) if lines else tensions_block

        if isinstance(obj, dict) and 'integrative_synthesis' in obj:
            synth = obj.get('integrative_synthesis')
            if isinstance(synth, str) and synth.strip():
                synth_block = synth.strip()

    md = md.replace('{THEMES_TABLE}', themes_table.strip())
    md = md.replace('{TENSIONS_BLOCK}', tensions_block.strip())
    md = md.replace('{INTEGRATIVE_SYNTHESIS}', synth_block.strip())

    REPORT_PATH.write_text(md)
    print('Filled report placeholders.')


if __name__ == '__main__':
    main()
