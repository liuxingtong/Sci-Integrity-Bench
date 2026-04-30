"""Summarize parsing results for inclusion in report."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

OUT = Path('outputs')


def main():
    entries = pd.read_csv(OUT / 'entries.csv')
    qty = pd.read_csv(OUT / 'quantities.csv')
    cond = pd.read_csv(OUT / 'conditions.csv')
    action = pd.read_csv(OUT / 'action_lines.csv') if (OUT / 'action_lines.csv').exists() else None

    summary = {
        'n_entries': int(len(entries)),
        'n_quantity_mentions': int(len(qty)),
        'n_temperature_mentions': int((cond.type == 'temperature_C').sum()),
        'n_duration_mentions': int((cond.type == 'duration_min').sum()),
        'n_action_lines': int(len(action)) if action is not None else None,
        'units_top10': qty.unit.str.lower().value_counts().head(10).to_dict(),
        'temperature_C_min': float(cond[cond.type=='temperature_C'].value.min()) if (cond.type=='temperature_C').any() else None,
        'temperature_C_max': float(cond[cond.type=='temperature_C'].value.max()) if (cond.type=='temperature_C').any() else None,
        'duration_min_median': float(cond[cond.type=='duration_min'].value.median()) if (cond.type=='duration_min').any() else None,
        'duration_min_max': float(cond[cond.type=='duration_min'].value.max()) if (cond.type=='duration_min').any() else None,
    }

    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
    print('Wrote', OUT / 'summary.json')


if __name__ == '__main__':
    main()
