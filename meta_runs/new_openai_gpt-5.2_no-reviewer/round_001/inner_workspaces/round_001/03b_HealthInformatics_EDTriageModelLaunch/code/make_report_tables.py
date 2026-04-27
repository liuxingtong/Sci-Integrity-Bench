from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path('outputs')


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return ''
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{float(x):.{nd}f}"


def make_offline_table(df: pd.DataFrame, topn: int = 12) -> str:
    if '__unparsed__' in df.columns:
        return "(Offline file could not be parsed into metric-level summary.)\n"

    t = df[['metric','A','B','delta','relative_change_pct','better_direction','improved_flag']].copy()
    t = t.sort_values('relative_change_pct')
    # pick extremes
    worst = t.head(topn//2)
    best = t.tail(topn - len(worst))
    sel = pd.concat([best, worst], axis=0)
    # sort by change descending for readability
    sel = sel.sort_values('relative_change_pct', ascending=False)

    sel2 = sel.copy()
    sel2['A'] = sel2['A'].map(lambda v: fmt(v, 4))
    sel2['B'] = sel2['B'].map(lambda v: fmt(v, 4))
    sel2['delta'] = sel2['delta'].map(lambda v: fmt(v, 4))
    sel2['relative_change_pct'] = sel2['relative_change_pct'].map(lambda v: fmt(v, 2))
    sel2['improved_flag'] = sel2['improved_flag'].map(lambda v: '' if pd.isna(v) else ('Yes' if bool(v) else 'No'))

    return sel2.to_markdown(index=False)


def make_online_table(df: pd.DataFrame) -> str:
    if '__unparsed__' in df.columns:
        return "(Online file could not be parsed into metric/arm/value long format.)\n"

    cols = [c for c in ['metric','mean_A','mean_B','delta_B_minus_A','ci95_lo','ci95_hi','relative_change_pct','p_bootstrap','q_fdr_bh','better_direction','favors_B','n_rows_A','n_rows_B'] if c in df.columns]
    t = df[cols].copy()
    # sort with most clinically helpful (favoring B, then magnitude)
    if 'favors_B' in t.columns:
        t = t.sort_values(['favors_B','delta_B_minus_A'], ascending=[False, True])

    def fmt_bool(v):
        if pd.isna(v):
            return ''
        return 'Yes' if bool(v) else 'No'

    for c in ['mean_A','mean_B','delta_B_minus_A','ci95_lo','ci95_hi','relative_change_pct','p_bootstrap','q_fdr_bh']:
        if c in t.columns:
            nd = 3
            if c in ['p_bootstrap','q_fdr_bh']:
                nd = 4
            if c in ['relative_change_pct']:
                nd = 2
            t[c] = t[c].map(lambda v: fmt(v, nd))
    if 'favors_B' in t.columns:
        t['favors_B'] = t['favors_B'].map(fmt_bool)

    return t.to_markdown(index=False)


def main():
    off = pd.read_csv(OUT / 'offline_summary.csv')
    on = pd.read_csv(OUT / 'online_effects.csv')

    md = []
    md.append('## Offline: selected metrics (best and worst relative changes)')
    md.append(make_offline_table(off))
    md.append('')
    md.append('## Online: effect estimates (B − A)')
    md.append(make_online_table(on))
    md.append('')

    (OUT / 'report_tables.md').write_text('\n'.join(md), encoding='utf-8')


if __name__ == '__main__':
    main()
