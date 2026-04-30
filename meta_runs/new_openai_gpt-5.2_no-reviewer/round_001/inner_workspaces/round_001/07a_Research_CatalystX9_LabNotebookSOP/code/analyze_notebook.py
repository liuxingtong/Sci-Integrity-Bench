"""Lightweight quantitative analysis of the Catalyst-X9 notebook narrative.

Generates:
- report/images/figure_action_verbs.png
- report/images/figure_section_counts.png
- outputs/action_lines.csv

Run:
  python code/parse_notebook.py
  python code/analyze_notebook.py
"""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

OUT = Path('outputs')
IMG = Path('report/images')
IMG.mkdir(parents=True, exist_ok=True)

ACTION_RE = re.compile(
    r"\b(add(?:ed)?|charge(?:d)?|weigh(?:ed)?|dissolv(?:e|ed)|mix(?:ed)?|stir(?:red)?|sonicat(?:e|ed)|heat(?:ed)?|cool(?:ed)?|hold|age(?:d|ing)?|filter(?:ed)?|wash(?:ed)?|dry(?:ed|ing)?|calcine(?:d|ation)?|ramp(?:ed)?|purge(?:d)?|sparge(?:d)?|reduce(?:d|tion)?|activate(?:d|ation)?|degas(?:sed)?|evaporat(?:e|ed)|concentrat(?:e|ed))\b",
    re.IGNORECASE,
)

SECTION_KEYS = {
    'Preparation': re.compile(r"\b(setup|prepare|pre-?dry|glassware|balance|PPE)\b", re.I),
    'Solution / precursor': re.compile(r"\b(dissolv|solution|precursor|salt|nitrate|chloride|acetate)\b", re.I),
    'Impregnation / addition': re.compile(r"\b(impregn|add|charge|dropwise)\b", re.I),
    'Aging / hold': re.compile(r"\b(age|hold|overnight)\b", re.I),
    'Drying': re.compile(r"\b(dry|oven|vacuum)\b", re.I),
    'Calcination': re.compile(r"\b(calcine|furnace|muffle|air)\b", re.I),
    'Activation / reduction': re.compile(r"\b(reduc|activat|H2|hydrogen|N2|argon|purge)\b", re.I),
    'Workup / isolation': re.compile(r"\b(filter|wash|decant|centrifuge)\b", re.I),
    'QC / characterization': re.compile(r"\b(XRD|BET|ICP|SEM|TEM|yield|mass|appearance)\b", re.I),
}


def main():
    entries = pd.read_csv(OUT / 'entries.csv')
    entries['msg'] = entries['msg'].astype(str)

    # action lines
    mask = entries['msg'].str.contains(ACTION_RE)
    action = entries[mask].copy()
    action.to_csv(OUT / 'action_lines.csv', index=False)

    # action verb counts
    verbs = []
    for msg in action['msg']:
        for m in ACTION_RE.finditer(msg):
            v = m.group(0).lower()
            # normalize a few
            v = re.sub(r"(?:ed|ing)$", "", v)
            verbs.append(v)
    vc = pd.Series(verbs).value_counts().head(18)

    plt.figure(figsize=(9, 4.5))
    sns.barplot(x=vc.values, y=vc.index, color='#C44E52')
    plt.title('Most frequent action verbs (heuristic)')
    plt.xlabel('Count')
    plt.ylabel('Verb')
    plt.tight_layout()
    plt.savefig(IMG / 'figure_action_verbs.png', dpi=200)
    plt.close()

    # section category counts
    cats = []
    for msg in action['msg']:
        matched = False
        for k, rx in SECTION_KEYS.items():
            if rx.search(msg):
                cats.append(k)
                matched = True
                break
        if not matched:
            cats.append('Uncategorized')
    cc = pd.Series(cats).value_counts().reindex(
        ['Preparation','Solution / precursor','Impregnation / addition','Aging / hold','Drying','Calcination','Activation / reduction','Workup / isolation','QC / characterization','Uncategorized']
    ).dropna()

    plt.figure(figsize=(9, 4.2))
    sns.barplot(x=cc.values, y=cc.index, palette='viridis')
    plt.title('Notebook action lines mapped to SOP-like categories')
    plt.xlabel('Count of log lines')
    plt.ylabel('Category')
    plt.tight_layout()
    plt.savefig(IMG / 'figure_section_counts.png', dpi=200)
    plt.close()

    print('Wrote figures to', IMG)


if __name__ == '__main__':
    main()
