"""Validate SOP coverage against notebook action lines.

Heuristic mapping: map each action log line to a SOP procedure section by keywords.
Outputs:
- outputs/sop_coverage.csv
- report/images/figure_sop_coverage.png

Run after synthesis_sop.md exists.
"""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

SOP_PATH = Path('synthesis_sop.md')
OUT = Path('outputs')
IMG = Path('report/images')
IMG.mkdir(parents=True, exist_ok=True)

# Map to SOP procedural subsections (aligned to synthesis_sop.md)
MAP = [
    ('Support pre-treatment', re.compile(r"\b(pre-?dry|desiccator|support)\b", re.I)),
    ('Precursor solution', re.compile(r"\b(dissolv|solution|precursor)\b", re.I)),
    ('Impregnation/addition', re.compile(r"\b(impregn|dropwise|aliquot|add|charge)\b", re.I)),
    ('Aging/hold', re.compile(r"\b(age|hold|overnight)\b", re.I)),
    ('Drying', re.compile(r"\b(dry|oven|vacuum)\b", re.I)),
    ('Calcination', re.compile(r"\b(calcine|muffle|furnace|air)\b", re.I)),
    ('Activation/reduction', re.compile(r"\b(activate|reduc|H2|hydrogen|purge|argon|nitrogen|N2\b|Ar\b)\b", re.I)),
    ('Workup/isolation', re.compile(r"\b(filter|wash|decant|centrifuge)\b", re.I)),
    ('Packaging/QC', re.compile(r"\b(label|jar|vial|retain|BET|XRD|ICP|yield|mass)\b", re.I)),
]


def main():
    if not SOP_PATH.exists():
        raise FileNotFoundError('Missing synthesis_sop.md')

    action_path = OUT / 'action_lines.csv'
    if not action_path.exists():
        raise FileNotFoundError('Run code/analyze_notebook.py first')

    action = pd.read_csv(action_path)
    action['msg'] = action['msg'].astype(str)

    # Assign mapping
    cats = []
    for msg in action['msg']:
        cat = 'Unmapped'
        for name, rx in MAP:
            if rx.search(msg):
                cat = name
                break
        cats.append(cat)
    action['mapped_section'] = cats

    cov = action['mapped_section'].value_counts().reset_index()
    cov.columns = ['mapped_section', 'count']
    cov.to_csv(OUT / 'sop_coverage.csv', index=False)

    # Plot
    order = [m[0] for m in MAP] + ['Unmapped']
    cov2 = cov.set_index('mapped_section').reindex(order).fillna(0).reset_index()

    plt.figure(figsize=(9.5, 4.8))
    sns.barplot(data=cov2, x='count', y='mapped_section', palette='mako')
    plt.title('Heuristic coverage: notebook action lines mapped to SOP procedure sections')
    plt.xlabel('Count of action-like notebook lines')
    plt.ylabel('SOP section')
    plt.tight_layout()
    plt.savefig(IMG / 'figure_sop_coverage.png', dpi=200)
    plt.close()

    # Print unmapped examples for human review
    unm = action[action['mapped_section'] == 'Unmapped'].head(25)
    (OUT / 'unmapped_examples.txt').write_text('\n'.join(unm['msg'].tolist()))
    print('Wrote outputs/sop_coverage.csv and figure_sop_coverage.png')


if __name__ == '__main__':
    main()
