"""ED TriageAssist A vs B evaluation.

Reads:
- data/offline_evaluation_metrics.csv
- data/online_ab_test_metrics.csv

Produces:
- outputs/*.csv intermediate tables
- report/images/*.png figures

Designed to be robust to either (a) metric-summary tables or (b) repeated measurements
(e.g., per-shift/per-day) in long format for the online pilot.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns


ROOT = Path('.')
DATA = ROOT / 'data'
OUT = ROOT / 'outputs'
IMG = ROOT / 'report' / 'images'


def ensure_dirs():
    OUT.mkdir(exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)


def _pick_col(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def parse_offline(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize offline table to columns: metric, A, B, rel_change_pct, delta."""
    metric_col = _pick_col(df, ['metric', 'metric_name', 'name', 'Metric'])
    a_col = _pick_col(df, ['triage_a', 'A', 'value_a', 'triageA', 'model_a'])
    b_col = _pick_col(df, ['triage_b', 'B', 'value_b', 'triageB', 'model_b'])
    rel_col = _pick_col(df, ['relative_change_pct', 'rel_change_pct', 'relative_change', 'pct_change'])

    if metric_col and a_col and b_col:
        out = df.copy()
        out = out.rename(columns={metric_col: 'metric', a_col: 'A', b_col: 'B'})
        out['delta'] = out['B'] - out['A']
        if rel_col and rel_col in out.columns:
            out = out.rename(columns={rel_col: 'relative_change_pct'})
        else:
            out['relative_change_pct'] = np.where(out['A'] != 0, 100 * out['delta'] / out['A'], np.nan)
        # strip whitespace
        out['metric'] = out['metric'].astype(str).str.strip()
        return out[['metric', 'A', 'B', 'delta', 'relative_change_pct'] + [c for c in out.columns if c not in ['metric','A','B','delta','relative_change_pct']]]

    # If we can't find a metric summary table, just return raw with a warning-like column.
    out = df.copy()
    out['__unparsed__'] = True
    return out


def infer_better_direction(metric: str) -> str:
    """Return 'higher', 'lower', or 'neutral' for what is clinically/analytically better."""
    m = metric.lower()

    # Online operational metrics (usually lower is better)
    lower_keywords = [
        'lwbs', 'left_without', 'elop', 'return', 'bounce', 'complaint', 'override',
        'mortality', 'adverse', 'time_to', 'time-to', 'wait', 'minutes', 'min', 'length_of_stay', 'los'
    ]
    higher_keywords = [
        'auroc', 'auc', 'auprc', 'accuracy', 'agreement', 'kappa', 'ppv', 'npv',
        'sensitivity', 'specificity', 'precision', 'recall', 'f1', 'r2', 'corr', 'calibration_slope'
    ]
    neutral_keywords = ['ece', 'brier', 'calibration_error', 'abs', 'mae', 'mape']  # lower is better but ambiguous

    # Explicit patterns
    if any(k in m for k in higher_keywords):
        return 'higher'
    if any(k in m for k in lower_keywords):
        return 'lower'
    if any(k in m for k in neutral_keywords):
        return 'lower'

    # Percent metrics: assume it's a "bad event rate" unless it says 'within' or 'seen'
    if m.endswith('_pct') or m.endswith('%'):
        if any(k in m for k in ['within', 'seen', 'appropriate', 'compliance']):
            return 'higher'
        return 'lower'

    return 'neutral'


def plot_offline_summary(off: pd.DataFrame):
    if '__unparsed__' in off.columns:
        return

    # Scatter A vs B
    plt.figure(figsize=(7, 7))
    sns.scatterplot(data=off, x='A', y='B', s=60)
    minv = np.nanmin(np.r_[off['A'].values, off['B'].values])
    maxv = np.nanmax(np.r_[off['A'].values, off['B'].values])
    pad = (maxv - minv) * 0.05 if np.isfinite(maxv - minv) else 1
    lo, hi = minv - pad, maxv + pad
    plt.plot([lo, hi], [lo, hi], linestyle='--', color='gray', linewidth=1)
    plt.xlabel('Offline metric value (TriageAssist-A)')
    plt.ylabel('Offline metric value (TriageAssist-B)')
    plt.title('Offline evaluation: B vs A (each point is a metric)')
    for _, r in off.iterrows():
        # avoid dense labels if too many
        if len(off) <= 30:
            plt.text(r['A'], r['B'], str(r['metric'])[:28], fontsize=8, alpha=0.85)
    plt.tight_layout()
    plt.savefig(IMG / 'offline_A_vs_B_scatter.png', dpi=200)
    plt.close()

    # Relative change bar plot
    off2 = off[['metric', 'relative_change_pct']].copy()
    off2 = off2.sort_values('relative_change_pct')
    plt.figure(figsize=(10, max(4, 0.25 * len(off2))))
    sns.barplot(data=off2, y='metric', x='relative_change_pct', color='#4C72B0')
    plt.axvline(0, color='black', linewidth=1)
    plt.xlabel('Relative change from A to B (%)')
    plt.ylabel('Metric')
    plt.title('Offline evaluation: relative change (B vs A)')
    plt.tight_layout()
    plt.savefig(IMG / 'offline_relative_change_pct.png', dpi=200)
    plt.close()


def summarize_offline(off: pd.DataFrame) -> pd.DataFrame:
    if '__unparsed__' in off.columns:
        return off

    s = off[['metric', 'A', 'B', 'delta', 'relative_change_pct']].copy()
    s['better_direction'] = s['metric'].apply(infer_better_direction)

    def is_improved(row):
        if row['better_direction'] == 'higher':
            return row['delta'] > 0
        if row['better_direction'] == 'lower':
            return row['delta'] < 0
        return np.nan

    s['improved_flag'] = s.apply(is_improved, axis=1)
    return s


def parse_online(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Return normalized long-format with columns [metric, arm, value, unit]."""
    metric_col = _pick_col(df, ['metric', 'metric_name', 'name', 'Metric'])
    arm_col = _pick_col(df, ['arm', 'variant', 'group'])
    value_col = _pick_col(df, ['value', 'metric_value', 'mean', 'estimate'])

    unit_by_metric: Dict[str, str] = {}

    if metric_col and arm_col and value_col:
        out = df.rename(columns={metric_col: 'metric', arm_col: 'arm', value_col: 'value'}).copy()
        out['metric'] = out['metric'].astype(str).str.strip()
        out['arm'] = out['arm'].astype(str).str.strip()
        # infer unit
        for m in out['metric'].unique():
            if str(m).endswith('_pct'):
                unit_by_metric[m] = 'percentage points'
            elif 'min' in str(m).lower() or 'minute' in str(m).lower() or 'time_to' in str(m).lower():
                unit_by_metric[m] = 'minutes'
            else:
                unit_by_metric[m] = 'units'
        return out[['metric', 'arm', 'value'] + [c for c in out.columns if c not in ['metric','arm','value']]], unit_by_metric

    # if wide format with A/B columns
    a_col = _pick_col(df, ['A', 'value_a', 'triage_a', 'arm_a'])
    b_col = _pick_col(df, ['B', 'value_b', 'triage_b', 'arm_b'])
    if metric_col and a_col and b_col:
        tmp = df.rename(columns={metric_col: 'metric', a_col: 'A', b_col: 'B'}).copy()
        long = tmp.melt(id_vars=['metric'], value_vars=['A', 'B'], var_name='arm', value_name='value')
        long['arm'] = long['arm'].map({'A': 'A', 'B': 'B'})
        for m in long['metric'].unique():
            if str(m).endswith('_pct'):
                unit_by_metric[m] = 'percentage points'
            elif 'min' in str(m).lower() or 'time_to' in str(m).lower():
                unit_by_metric[m] = 'minutes'
            else:
                unit_by_metric[m] = 'units'
        return long, unit_by_metric

    out = df.copy()
    out['__unparsed__'] = True
    return out, unit_by_metric


def compute_online_effects(long: pd.DataFrame, n_boot: int = 5000, seed: int = 7) -> pd.DataFrame:
    """Compute per-metric mean by arm and bootstrap CI of delta (B-A).

    Notes
    -----
    * If repeated rows exist per metric-arm (e.g., per shift/day), treats each row as an independent
      experimental unit and bootstraps over rows.
    * If only one row per metric-arm is available, uncertainty cannot be estimated from this file;
      CI and p-values will be NaN.
    """
    if '__unparsed__' in long.columns:
        return long

    rng = np.random.default_rng(seed)

    records = []
    for metric, g in long.groupby('metric', sort=False):
        # require both arms
        arms = set(g['arm'].unique())
        if not {'A', 'B'}.issubset(arms):
            # try map common names
            pass
        g2 = g.copy()
        # normalize arm labels (case-insensitive)
        g2['arm'] = g2['arm'].str.upper().str.replace('TRIAGEASSIST-', '', regex=False)
        # allow 'CONTROL'->A and 'TREATMENT'->B
        g2['arm'] = g2['arm'].replace({'CONTROL': 'A', 'TREATMENT': 'B', 'BASELINE': 'A', 'CANDIDATE': 'B'})

        if not {'A', 'B'}.issubset(set(g2['arm'].unique())):
            continue

        a = g2.loc[g2['arm'] == 'A', 'value'].astype(float).dropna().to_numpy()
        b = g2.loc[g2['arm'] == 'B', 'value'].astype(float).dropna().to_numpy()
        mean_a = float(np.mean(a)) if len(a) else np.nan
        mean_b = float(np.mean(b)) if len(b) else np.nan
        delta = mean_b - mean_a

        ci_lo = np.nan
        ci_hi = np.nan
        p = np.nan
        if len(a) >= 2 and len(b) >= 2:
            # bootstrap difference in means
            boot = np.empty(n_boot)
            for i in range(n_boot):
                aa = rng.choice(a, size=len(a), replace=True)
                bb = rng.choice(b, size=len(b), replace=True)
                boot[i] = bb.mean() - aa.mean()
            ci_lo, ci_hi = np.percentile(boot, [2.5, 97.5])
            # two-sided p-value against 0
            p = 2 * min((boot <= 0).mean(), (boot >= 0).mean())

        records.append({
            'metric': metric,
            'mean_A': mean_a,
            'mean_B': mean_b,
            'delta_B_minus_A': delta,
            'ci95_lo': ci_lo,
            'ci95_hi': ci_hi,
            'p_bootstrap': p,
            'n_rows_A': int(len(a)),
            'n_rows_B': int(len(b)),
        })

    return pd.DataFrame.from_records(records)


def plot_online_forest(effects: pd.DataFrame):
    if effects is None or len(effects) == 0 or '__unparsed__' in effects.columns:
        return

    eff = effects.copy()

    # order by delta
    eff = eff.sort_values('delta_B_minus_A')

    plt.figure(figsize=(10, max(4, 0.3 * len(eff))))
    y = np.arange(len(eff))
    x = eff['delta_B_minus_A'].values

    # CI bars
    lo = eff['ci95_lo'].values
    hi = eff['ci95_hi'].values
    has_ci = np.isfinite(lo) & np.isfinite(hi)

    plt.axvline(0, color='black', linewidth=1)

    # color by whether it favors B (if known)
    if 'favors_B' in eff.columns:
        colors = np.where(eff['favors_B'].fillna(False).to_numpy(), '#55A868', '#C44E52')
    else:
        colors = '#DD8452'

    plt.scatter(x, y, color=colors, zorder=3)
    for i in range(len(eff)):
        if has_ci[i]:
            plt.plot([lo[i], hi[i]], [y[i], y[i]], color=colors[i] if isinstance(colors, np.ndarray) else colors, linewidth=2, zorder=2)

    plt.yticks(y, eff['metric'])
    plt.xlabel('Delta (B − A) in reported units (percentage points for *_pct)')
    plt.title('Online pilot: effect sizes (B vs A); green=favors B by heuristic direction')
    plt.tight_layout()
    plt.savefig(IMG / 'online_effects_forest.png', dpi=200)
    plt.close()


def plot_online_distributions(long: pd.DataFrame, metrics: Optional[list] = None):
    """Box/strip plots by arm for selected metrics when repeated rows are present."""
    if '__unparsed__' in long.columns:
        return

    # detect repetition
    rep = long.groupby(['metric', 'arm']).size().reset_index(name='n')
    if rep['n'].max() <= 1:
        return

    if metrics is None:
        # pick common operational metrics if present
        preferred = [
            'Median_time_to_physician_min',
            'LWBS_rate_pct',
            '72hr_return_rate_pct',
            'ED_return_72h_pct',
            'Provider_override_rate_pct',
            'Override_rate_pct',
            'Patient_complaints_rate_pct',
            'Complaint_rate_pct'
        ]
        present = [m for m in preferred if m in set(long['metric'])]
        metrics = present if present else list(long['metric'].unique())[:6]

    # plot each metric separately for readability
    for m in metrics:
        g = long[long['metric'] == m].copy()
        if g.empty:
            continue
        plt.figure(figsize=(7, 5))
        sns.boxplot(data=g, x='arm', y='value', palette=['#4C72B0', '#DD8452'])
        sns.stripplot(data=g, x='arm', y='value', color='black', alpha=0.35, jitter=0.15, size=3)
        plt.xlabel('Arm')
        plt.ylabel(m)
        plt.title(f'Online pilot distribution by shift/day: {m}')
        plt.tight_layout()
        safe = re.sub(r'[^A-Za-z0-9_\-]+', '_', m)
        plt.savefig(IMG / f'online_dist_{safe}.png', dpi=200)
        plt.close()


def plot_online_timeseries(long: pd.DataFrame):
    """Plot daily trends if a date/day column exists."""
    if '__unparsed__' in long.columns:
        return

    time_col = None
    for c in ['date', 'day', 'shift_date', 'service_date']:
        if c in long.columns:
            time_col = c
            break
    if time_col is None:
        return

    df = long.copy()
    # coerce to datetime if possible
    if not np.issubdtype(df[time_col].dtype, np.datetime64):
        try:
            df[time_col] = pd.to_datetime(df[time_col])
        except Exception:
            pass

    # choose up to 4 metrics
    metrics = list(df['metric'].unique())
    preferred = [m for m in ['Median_time_to_physician_min', 'LWBS_rate_pct'] if m in metrics]
    if preferred:
        metrics = preferred + [m for m in metrics if m not in preferred]
    metrics = metrics[:4]

    for m in metrics:
        g = df[df['metric'] == m].copy()
        if g.empty:
            continue
        agg = g.groupby([time_col, 'arm'])['value'].mean().reset_index()
        plt.figure(figsize=(9, 4))
        sns.lineplot(data=agg, x=time_col, y='value', hue='arm', marker='o')
        plt.title(f'Online pilot mean by day: {m}')
        plt.xlabel(time_col)
        plt.ylabel('Mean value')
        plt.tight_layout()
        safe = re.sub(r'[^A-Za-z0-9_\-]+', '_', m)
        plt.savefig(IMG / f'online_timeseries_{safe}.png', dpi=200)
        plt.close()


def main():
    ensure_dirs()
    sns.set_theme(style='whitegrid', context='talk')

    # OFFLINE
    off_raw = pd.read_csv(DATA / 'offline_evaluation_metrics.csv')
    off = parse_offline(off_raw)
    off_summary = summarize_offline(off)
    off_summary.to_csv(OUT / 'offline_summary.csv', index=False)
    plot_offline_summary(off)

    # ONLINE
    on_raw = pd.read_csv(DATA / 'online_ab_test_metrics.csv')
    on_long, unit_map = parse_online(on_raw)
    on_long.to_csv(OUT / 'online_long_normalized.csv', index=False)

    # diagnostic plots from raw repeated-measure data (if present)
    plot_online_distributions(on_long)
    plot_online_timeseries(on_long)

    effects = compute_online_effects(on_long)
    if '__unparsed__' not in effects.columns and len(effects):
        effects['better_direction'] = effects['metric'].apply(infer_better_direction)
        effects['relative_change_pct'] = np.where(
            effects['mean_A'].to_numpy() != 0,
            100.0 * effects['delta_B_minus_A'].to_numpy() / effects['mean_A'].to_numpy(),
            np.nan,
        )
        effects['favors_B'] = np.where(
            effects['better_direction'].eq('higher'),
            effects['delta_B_minus_A'] > 0,
            np.where(effects['better_direction'].eq('lower'), effects['delta_B_minus_A'] < 0, np.nan)
        )
        # Benjamini–Hochberg FDR for bootstrap p-values (when available)
        p = effects['p_bootstrap'].to_numpy()
        q = np.full_like(p, np.nan, dtype=float)
        mask = np.isfinite(p)
        if mask.sum() > 0:
            p_m = p[mask]
            order = np.argsort(p_m)
            ranked = p_m[order]
            m = len(ranked)
            q_r = ranked * m / (np.arange(1, m + 1))
            # enforce monotonicity
            q_r = np.minimum.accumulate(q_r[::-1])[::-1]
            q_vals = np.empty_like(q_r)
            q_vals[order] = np.clip(q_r, 0, 1)
            q[mask] = q_vals
        effects['q_fdr_bh'] = q

    effects.to_csv(OUT / 'online_effects.csv', index=False)
    plot_online_forest(effects)

    # Save unit map
    if unit_map:
        pd.DataFrame({'metric': list(unit_map.keys()), 'unit': list(unit_map.values())}).to_csv(OUT / 'online_metric_units.csv', index=False)


if __name__ == '__main__':
    main()
