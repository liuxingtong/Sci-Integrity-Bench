import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
DATA_DIR = os.path.join(ROOT, 'data')
OUT_DIR = os.path.join(ROOT, 'outputs')
IMG_DIR = os.path.join(ROOT, 'report', 'images')

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

sns.set_theme(style='whitegrid', font_scale=1.0)


def _find_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def load_offline(path):
    df = pd.read_csv(path)
    # normalize column names
    df.columns = [c.strip() for c in df.columns]
    metric_col = _find_col(df, ['metric', 'Metric', 'name', 'metric_name'])
    v1_col = _find_col(df, ['recsys_v1', 'v1', 'baseline', 'control'])
    v2_col = _find_col(df, ['recsys_v2', 'v2', 'treatment'])
    rel_col = _find_col(df, ['relative_change_pct', 'relative_change', 'rel_change_pct', 'lift_pct'])

    if metric_col is None:
        raise ValueError(f'Could not find metric column in offline file. Columns={df.columns.tolist()}')
    if v1_col is None or v2_col is None:
        raise ValueError(f'Could not find recsys_v1/recsys_v2 columns in offline file. Columns={df.columns.tolist()}')

    out = df[[metric_col, v1_col, v2_col] + ([rel_col] if rel_col else [])].copy()
    out = out.rename(columns={metric_col: 'metric', v1_col: 'recsys_v1', v2_col: 'recsys_v2'})

    out['delta'] = out['recsys_v2'] - out['recsys_v1']
    out['relative_change_pct_calc'] = np.where(out['recsys_v1'] != 0, (out['delta'] / out['recsys_v1']) * 100.0, np.nan)
    if rel_col:
        out = out.rename(columns={rel_col: 'relative_change_pct'})
        out['relative_change_pct_diff'] = out['relative_change_pct'] - out['relative_change_pct_calc']
    else:
        out['relative_change_pct'] = out['relative_change_pct_calc']
        out['relative_change_pct_diff'] = np.nan

    return out


def load_online(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    metric_col = _find_col(df, ['metric', 'Metric', 'name', 'metric_name'])
    v1_col = _find_col(df, ['recsys_v1_pct', 'recsys_v1', 'v1_pct', 'control_pct'])
    v2_col = _find_col(df, ['recsys_v2_pct', 'recsys_v2', 'v2_pct', 'treatment_pct'])

    if metric_col is None:
        raise ValueError(f'Could not find metric column in online file. Columns={df.columns.tolist()}')
    if v1_col is None or v2_col is None:
        raise ValueError(f'Could not find recsys_v1_pct/recsys_v2_pct columns in online file. Columns={df.columns.tolist()}')

    out = df.copy().rename(columns={metric_col: 'metric', v1_col: 'recsys_v1_pct', v2_col: 'recsys_v2_pct'})

    # any provided diff/se/pvalue columns
    diff_col = _find_col(out, ['diff_pp', 'delta_pp', 'difference_pp', 'absolute_diff_pp'])
    se_col = _find_col(out, ['se_diff_pp', 'stderr_diff_pp', 'se_pp', 'std_err_pp'])
    p_col = _find_col(out, ['p_value', 'pval', 'p'])

    out['delta_pp'] = out['recsys_v2_pct'] - out['recsys_v1_pct'] if diff_col is None else out[diff_col]
    out['relative_lift_pct'] = np.where(out['recsys_v1_pct'] != 0, (out['delta_pp'] / out['recsys_v1_pct']) * 100.0, np.nan)

    if se_col is not None:
        out['se_diff_pp'] = out[se_col]
        out['ci95_low_pp'] = out['delta_pp'] - 1.96 * out['se_diff_pp']
        out['ci95_high_pp'] = out['delta_pp'] + 1.96 * out['se_diff_pp']
    else:
        out['se_diff_pp'] = np.nan
        out['ci95_low_pp'] = np.nan
        out['ci95_high_pp'] = np.nan

    if p_col is not None:
        out['p_value'] = out[p_col]
    else:
        out['p_value'] = np.nan

    return out


def plot_offline(df, path_png):
    d = df.sort_values('relative_change_pct')
    plt.figure(figsize=(8, max(3.5, 0.4 * len(d))))
    colors = d['relative_change_pct'].apply(lambda x: '#2ca02c' if x >= 0 else '#d62728')
    plt.barh(d['metric'], d['relative_change_pct'], color=colors)
    plt.axvline(0, color='black', linewidth=1)
    plt.xlabel('Relative change v2 vs v1 (%)')
    plt.title('Offline ranking-quality metrics: RecSys-v2 vs RecSys-v1')
    plt.tight_layout()
    plt.savefig(path_png, dpi=200)
    plt.close()


def plot_online(df, path_png):
    d = df.sort_values('delta_pp')
    plt.figure(figsize=(8, max(3.5, 0.4 * len(d))))
    colors = d['delta_pp'].apply(lambda x: '#2ca02c' if x >= 0 else '#d62728')
    y = np.arange(len(d))
    plt.barh(y, d['delta_pp'], color=colors)

    # error bars if available
    if np.isfinite(d['se_diff_pp']).any():
        mask = np.isfinite(d['se_diff_pp']).values
        plt.errorbar(
            d.loc[mask, 'delta_pp'], y[mask],
            xerr=1.96 * d.loc[mask, 'se_diff_pp'],
            fmt='none', ecolor='black', capsize=3, linewidth=1
        )

    plt.yticks(y, d['metric'])
    plt.axvline(0, color='black', linewidth=1)
    plt.xlabel('Absolute difference v2 - v1 (percentage points)')
    plt.title('Online A/B (14 days, 10% traffic per arm): metric deltas')
    plt.tight_layout()
    plt.savefig(path_png, dpi=200)
    plt.close()


def plot_parity(df, xcol, ycol, title, xlabel, ylabel, path_png):
    d = df.copy()
    # keep finite
    d = d[np.isfinite(d[xcol]) & np.isfinite(d[ycol])]
    if d.empty:
        return
    plt.figure(figsize=(7, 6))
    ax = sns.scatterplot(data=d, x=xcol, y=ycol)
    mn = float(np.nanmin([d[xcol].min(), d[ycol].min()]))
    mx = float(np.nanmax([d[xcol].max(), d[ycol].max()]))
    pad = 0.02 * (mx - mn) if mx > mn else 1.0
    lo, hi = mn - pad, mx + pad
    ax.plot([lo, hi], [lo, hi], color='black', linewidth=1, linestyle='--')
    for _, r in d.iterrows():
        ax.text(r[xcol], r[ycol], str(r['metric']), fontsize=8, alpha=0.8)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(path_png, dpi=200)
    plt.close()


def main():
    offline_path = os.path.join(DATA_DIR, 'offline_evaluation_metrics.csv')
    online_path = os.path.join(DATA_DIR, 'online_ab_test_metrics.csv')

    offline = load_offline(offline_path)
    online = load_online(online_path)

    offline.to_csv(os.path.join(OUT_DIR, 'offline_metrics_clean.csv'), index=False)
    online.to_csv(os.path.join(OUT_DIR, 'online_metrics_clean.csv'), index=False)

    # Save compact markdown tables
    offline_tbl = offline[['metric', 'recsys_v1', 'recsys_v2', 'delta', 'relative_change_pct']].copy()
    online_cols = ['metric', 'recsys_v1_pct', 'recsys_v2_pct', 'delta_pp', 'relative_lift_pct']
    if np.isfinite(online['se_diff_pp']).any():
        online_cols += ['se_diff_pp', 'ci95_low_pp', 'ci95_high_pp']
    if np.isfinite(online['p_value']).any():
        online_cols += ['p_value']
    online_tbl = online[online_cols].copy()

    offline_tbl.to_markdown(os.path.join(OUT_DIR, 'offline_metrics_table.md'), index=False, floatfmt='.4g')
    online_tbl.to_markdown(os.path.join(OUT_DIR, 'online_metrics_table.md'), index=False, floatfmt='.4g')

    # Plots
    plot_offline(offline, os.path.join(IMG_DIR, 'offline_relative_change.png'))
    plot_online(online, os.path.join(IMG_DIR, 'online_delta_pp.png'))
    plot_parity(
        offline, 'recsys_v1', 'recsys_v2',
        title='Offline parity plot (v1 vs v2 values)',
        xlabel='RecSys-v1 (offline metric value)',
        ylabel='RecSys-v2 (offline metric value)',
        path_png=os.path.join(IMG_DIR, 'offline_parity.png')
    )
    plot_parity(
        online, 'recsys_v1_pct', 'recsys_v2_pct',
        title='Online parity plot (v1 vs v2 values)',
        xlabel='RecSys-v1 (metric, % points)',
        ylabel='RecSys-v2 (metric, % points)',
        path_png=os.path.join(IMG_DIR, 'online_parity.png')
    )

    # Also export a combined "scorecard" view for convenience
    scorecard = {
        'offline': offline_tbl,
        'online': online_tbl
    }
    # Topline summary stats
    summary = {
        'offline_num_metrics': int(len(offline)),
        'offline_num_positive': int((offline['relative_change_pct'] > 0).sum()),
        'offline_num_negative': int((offline['relative_change_pct'] < 0).sum()),
        'online_num_metrics': int(len(online)),
        'online_num_positive': int((online['delta_pp'] > 0).sum()),
        'online_num_negative': int((online['delta_pp'] < 0).sum()),
    }
    pd.Series(summary).to_csv(os.path.join(OUT_DIR, 'summary_counts.csv'), header=False)

    print('Wrote outputs to', OUT_DIR)
    print('Wrote figures to', IMG_DIR)


if __name__ == '__main__':
    main()
