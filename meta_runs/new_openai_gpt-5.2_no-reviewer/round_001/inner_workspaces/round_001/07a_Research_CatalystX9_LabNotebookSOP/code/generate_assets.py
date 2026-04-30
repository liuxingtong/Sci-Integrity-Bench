"""Generate figures and draft SOP scaffold from parsed notebook.

This script consumes outputs/*.csv produced by parse_notebook.py and creates:
- report/images/figure_units.png
- report/images/figure_temperature_mentions.png
- report/images/figure_duration_distribution.png
- outputs/sop_scaffold.md (machine-drafted scaffold; final SOP assembled separately)

Run:
  python code/parse_notebook.py
  python code/generate_assets.py
"""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

WS = Path('.')
OUT = WS / 'outputs'
REPORT_IMG = WS / 'report' / 'images'
REPORT_IMG.mkdir(parents=True, exist_ok=True)


def _load(name: str) -> pd.DataFrame:
    p = OUT / name
    if not p.exists():
        raise FileNotFoundError(p)
    return pd.read_csv(p)


def fig_units(df_qty: pd.DataFrame) -> Path:
    df = df_qty.copy()
    df['unit'] = df['unit'].str.lower().str.replace('ml', 'mL')
    order = df['unit'].value_counts().index.tolist()
    plt.figure(figsize=(8, 4.5))
    sns.countplot(data=df, y='unit', order=order, color='#4C72B0')
    plt.title('Extracted quantity mentions by unit (heuristic)')
    plt.xlabel('Count')
    plt.ylabel('Unit')
    plt.tight_layout()
    out = REPORT_IMG / 'figure_units.png'
    plt.savefig(out, dpi=200)
    plt.close()
    return out


def fig_temperature_mentions(df_cond: pd.DataFrame) -> Path:
    df = df_cond[df_cond['type'] == 'temperature_C'].copy()
    if df.empty:
        # create placeholder figure
        plt.figure(figsize=(7, 3))
        plt.text(0.5, 0.5, 'No temperature values parsed', ha='center', va='center')
        plt.axis('off')
        out = REPORT_IMG / 'figure_temperature_mentions.png'
        plt.savefig(out, dpi=200)
        plt.close()
        return out

    # Use line number as x-axis proxy for progression.
    df = df.sort_values('line')
    plt.figure(figsize=(9, 4))
    plt.plot(df['line'], df['value'], marker='o', linewidth=1.5)
    plt.title('Temperature values mentioned across notebook (line-number proxy)')
    plt.xlabel('Notebook line number')
    plt.ylabel('Temperature (°C)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    out = REPORT_IMG / 'figure_temperature_mentions.png'
    plt.savefig(out, dpi=200)
    plt.close()
    return out


def fig_duration_distribution(df_cond: pd.DataFrame) -> Path:
    df = df_cond[df_cond['type'] == 'duration_min'].copy()
    df = df[df['value'].notna()]
    if df.empty:
        plt.figure(figsize=(7, 3))
        plt.text(0.5, 0.5, 'No durations parsed', ha='center', va='center')
        plt.axis('off')
        out = REPORT_IMG / 'figure_duration_distribution.png'
        plt.savefig(out, dpi=200)
        plt.close()
        return out

    plt.figure(figsize=(8, 4.5))
    sns.histplot(df['value'], bins=20, color='#55A868')
    plt.title('Distribution of parsed step durations')
    plt.xlabel('Duration (min)')
    plt.ylabel('Count')
    plt.tight_layout()
    out = REPORT_IMG / 'figure_duration_distribution.png'
    plt.savefig(out, dpi=200)
    plt.close()
    return out


def draft_scaffold(entries: pd.DataFrame) -> str:
    # Extract likely imperative lines: added/charge/heat/stir/filter/wash/dry/calcine
    key_re = re.compile(r"\b(add|added|charge|charged|heat|heated|cool|cooled|stir|stirred|hold|aged|filter|filtered|wash|washed|dry|dried|calcine|calcined|ramp|purge|sparge|nitrogen|argon|vacuum)\b",
                        re.IGNORECASE)
    cand = entries[entries['msg'].astype(str).str.contains(key_re)].copy()
    # keep distinct contexts
    lines = []
    for _, r in cand.iterrows():
        sec = r['section'] if isinstance(r['section'], str) and r['section'] else ''
        t = r['time'] if isinstance(r['time'], str) else ''
        prefix = ' - '
        label = f"[{sec}] " if sec else ''
        label += f"{t} " if t else ''
        lines.append(prefix + label + str(r['msg']).strip())

    scaffold = """# Catalyst-X9 Synthesis SOP (DRAFT scaffold)\n\n## Extracted action-like log lines (for human curation)\n\n""" + "\n".join(lines[:250]) + "\n\n"  # cap length
    return scaffold


def main():
    entries = _load('entries.csv')
    qty = _load('quantities.csv')
    cond = _load('conditions.csv')

    fig_units(qty)
    fig_temperature_mentions(cond)
    fig_duration_distribution(cond)

    scaffold = draft_scaffold(entries)
    (OUT / 'sop_scaffold.md').write_text(scaffold)
    print('Wrote scaffold to', OUT / 'sop_scaffold.md')


if __name__ == '__main__':
    main()
