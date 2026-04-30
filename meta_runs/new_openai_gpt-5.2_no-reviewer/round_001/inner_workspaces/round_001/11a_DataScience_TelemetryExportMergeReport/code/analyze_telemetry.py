import os
from dataclasses import dataclass
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

try:
    from scipy import stats
except Exception:  # pragma: no cover
    stats = None

DATA_SITE = os.path.join('data', 'site_daily_kwh.csv')
DATA_FIELD = os.path.join('data', 'field_ops_export.csv')
OUT_DIR = 'outputs'
IMG_DIR = os.path.join('report', 'images')

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

sns.set_theme(style='whitegrid', context='talk')


@dataclass
class QualityThresholds:
    # Material discrepancy thresholds for daily kWh per unit
    abs_kwh: float = 1000.0
    rel_pct: float = 0.05


def load_and_standardize(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.copy()

    # Flexible schema mapping across exports
    colmap_candidates = [
        # canonical
        {'record_date': 'record_date', 'generator_unit': 'generator_unit', 'net_kwh': 'net_kwh'},
        # field ops export observed
        {'record_date': 'ReadingDt', 'generator_unit': 'Unit', 'net_kwh': 'Delivered_kWh'},
        # other likely variants
        {'record_date': 'date', 'generator_unit': 'unit', 'net_kwh': 'kwh'},
        {'record_date': 'RecordDate', 'generator_unit': 'GeneratorUnit', 'net_kwh': 'Net_kWh'},
    ]

    chosen = None
    cols = set(df.columns)
    for m in colmap_candidates:
        if set(m.values()).issubset(cols):
            chosen = m
            break
    if chosen is None:
        raise ValueError(
            f"{path} does not contain a recognized schema. Found columns: {list(df.columns)}"
        )

    df = df.rename(columns={chosen['record_date']: 'record_date',
                            chosen['generator_unit']: 'generator_unit',
                            chosen['net_kwh']: 'net_kwh'})

    df['record_date'] = pd.to_datetime(df['record_date'], errors='coerce')
    df['generator_unit'] = df['generator_unit'].astype(str).str.strip()
    df['net_kwh'] = pd.to_numeric(df['net_kwh'], errors='coerce')

    # Drop rows with unparseable date/unit
    df = df.dropna(subset=['record_date', 'generator_unit'])

    return df


def aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    # If duplicates exist for a date/unit, assume they are additive (partial-day segments)
    return (
        df.groupby(['record_date', 'generator_unit'], as_index=False)
          .agg(net_kwh=('net_kwh', 'sum'), n_records=('net_kwh', 'size'))
    )


def build_merge(site: pd.DataFrame, field: pd.DataFrame, thr: QualityThresholds):
    m = site.merge(
        field,
        on=['record_date', 'generator_unit'],
        how='outer',
        suffixes=('_site', '_field'),
        indicator=True,
    )

    both = m['_merge'] == 'both'
    m['diff_kwh_field_minus_site'] = np.where(
        both,
        m['net_kwh_field'] - m['net_kwh_site'],
        np.nan,
    )
    m['abs_diff_kwh'] = m['diff_kwh_field_minus_site'].abs()
    m['pct_diff_vs_site'] = m['diff_kwh_field_minus_site'] / m['net_kwh_site'].replace(0, np.nan)

    # Discrepancy flag
    m['material_discrepancy'] = False
    m.loc[both, 'material_discrepancy'] = (
        (m.loc[both, 'abs_diff_kwh'] > thr.abs_kwh) &
        (m.loc[both, 'pct_diff_vs_site'].abs() > thr.rel_pct)
    )

    # Choose merged value (site preferred, field fills gaps)
    m['net_kwh_merged'] = m['net_kwh_site']
    m.loc[m['net_kwh_merged'].isna(), 'net_kwh_merged'] = m.loc[m['net_kwh_merged'].isna(), 'net_kwh_field']

    # Provenance
    m['source_used'] = np.where(m['net_kwh_site'].notna(), 'site', 'field')
    m.loc[(m['net_kwh_site'].isna()) & (m['net_kwh_field'].isna()), 'source_used'] = 'none'

    return m


def quarter_label(d: pd.Timestamp) -> str:
    q = (d.month - 1) // 3 + 1
    return f"{d.year}-Q{q}"


def main():
    thr = QualityThresholds()

    site_raw = load_and_standardize(DATA_SITE)
    field_raw = load_and_standardize(DATA_FIELD)

    site = aggregate_daily(site_raw)
    field = aggregate_daily(field_raw)

    # Save cleaned/aggregated
    site.to_csv(os.path.join(OUT_DIR, 'site_daily_agg.csv'), index=False)
    field.to_csv(os.path.join(OUT_DIR, 'field_daily_agg.csv'), index=False)

    merged = build_merge(site, field, thr)

    # Coverage grid
    start = min(site['record_date'].min(), field['record_date'].min())
    end = max(site['record_date'].max(), field['record_date'].max())
    all_days = pd.date_range(start.normalize(), end.normalize(), freq='D')
    units = sorted(set(site['generator_unit']).union(set(field['generator_unit'])))
    grid = pd.MultiIndex.from_product([all_days, units], names=['record_date', 'generator_unit']).to_frame(index=False)

    # Left join to quantify completeness
    cov = grid.merge(merged[['record_date','generator_unit','net_kwh_site','net_kwh_field','net_kwh_merged','material_discrepancy','source_used','_merge']],
                     on=['record_date','generator_unit'], how='left')
    cov['has_site'] = cov['net_kwh_site'].notna()
    cov['has_field'] = cov['net_kwh_field'].notna()
    cov['has_merged'] = cov['net_kwh_merged'].notna()

    # Summary stats
    summary = {}
    summary['date_start'] = str(start.date())
    summary['date_end'] = str(end.date())
    summary['n_days'] = int(len(all_days))
    summary['n_units'] = int(len(units))
    summary['expected_records'] = int(len(grid))
    summary['site_records'] = int(cov['has_site'].sum())
    summary['field_records'] = int(cov['has_field'].sum())
    summary['merged_records'] = int(cov['has_merged'].sum())
    summary['site_completeness'] = float(cov['has_site'].mean())
    summary['field_completeness'] = float(cov['has_field'].mean())
    summary['merged_completeness'] = float(cov['has_merged'].mean())

    both = merged[merged['_merge'] == 'both'].copy()
    if len(both):
        summary['matched_records'] = int(len(both))
        summary['mean_abs_diff_kwh'] = float(both['abs_diff_kwh'].mean())
        summary['median_abs_diff_kwh'] = float(both['abs_diff_kwh'].median())
        summary['mean_pct_diff'] = float((both['pct_diff_vs_site']).mean())
        summary['median_pct_diff'] = float((both['pct_diff_vs_site']).median())
        summary['material_discrepancy_rate'] = float(both['material_discrepancy'].mean())
        # Regression-esque diagnostics
        summary['corr_site_field'] = float(both[['net_kwh_site','net_kwh_field']].corr().iloc[0,1])

        # Bias test (field - site) in kWh
        d = both['diff_kwh_field_minus_site'].replace([np.inf, -np.inf], np.nan).dropna()
        n = int(d.shape[0])
        summary['bias_n'] = n
        summary['bias_mean_diff_kwh'] = float(d.mean())
        summary['bias_median_diff_kwh'] = float(d.median())
        summary['bias_std_diff_kwh'] = float(d.std(ddof=1)) if n > 1 else np.nan
        se = float(d.std(ddof=1) / np.sqrt(n)) if n > 1 else np.nan
        summary['bias_se_diff_kwh'] = se
        if stats is not None and n > 1:
            tcrit = float(stats.t.ppf(0.975, df=n-1))
            summary['bias_ci95_low_kwh'] = float(d.mean() - tcrit * se)
            summary['bias_ci95_high_kwh'] = float(d.mean() + tcrit * se)
            tstat, pval = stats.ttest_1samp(d, popmean=0.0, nan_policy='omit')
            summary['bias_ttest_pvalue'] = float(pval)
        else:
            summary['bias_ci95_low_kwh'] = np.nan
            summary['bias_ci95_high_kwh'] = np.nan
            summary['bias_ttest_pvalue'] = np.nan

        # Per-unit comparison table
        per_unit = both.groupby('generator_unit', as_index=False).agg(
            n_matched=('diff_kwh_field_minus_site', 'size'),
            mean_diff_kwh=('diff_kwh_field_minus_site', 'mean'),
            median_diff_kwh=('diff_kwh_field_minus_site', 'median'),
            mean_abs_diff_kwh=('abs_diff_kwh', 'mean'),
            mean_pct_diff=('pct_diff_vs_site', 'mean'),
            material_discrepancy_rate=('material_discrepancy', 'mean'),
        )
        # Correlation per unit
        cors = []
        for u, dfu in both.groupby('generator_unit'):
            if len(dfu) > 1:
                cors.append((u, float(dfu[['net_kwh_site', 'net_kwh_field']].corr().iloc[0, 1])))
            else:
                cors.append((u, np.nan))
        cors = pd.DataFrame(cors, columns=['generator_unit', 'corr_site_field'])
        per_unit = per_unit.merge(cors, on='generator_unit', how='left').sort_values('mean_abs_diff_kwh', ascending=False)
        per_unit.to_csv(os.path.join(OUT_DIR, 'source_comparison_by_unit.csv'), index=False)

        overall = pd.DataFrame([{
            'n_matched': n,
            'mean_diff_kwh': d.mean(),
            'median_diff_kwh': d.median(),
            'mean_abs_diff_kwh': both['abs_diff_kwh'].mean(),
            'median_abs_diff_kwh': both['abs_diff_kwh'].median(),
            'mean_pct_diff': both['pct_diff_vs_site'].mean(),
            'median_pct_diff': both['pct_diff_vs_site'].median(),
            'corr_site_field': both[['net_kwh_site', 'net_kwh_field']].corr().iloc[0, 1],
            'material_discrepancy_rate': both['material_discrepancy'].mean(),
            'bias_ci95_low_kwh': summary['bias_ci95_low_kwh'],
            'bias_ci95_high_kwh': summary['bias_ci95_high_kwh'],
            'bias_ttest_pvalue': summary['bias_ttest_pvalue'],
        }])
        overall.to_csv(os.path.join(OUT_DIR, 'source_comparison_overall.csv'), index=False)

    else:
        summary['matched_records'] = 0

    pd.Series(summary).to_csv(os.path.join(OUT_DIR, 'summary_metrics.csv'))

    # Create final merged daily table
    final = cov[['record_date','generator_unit','net_kwh_merged','source_used','material_discrepancy','net_kwh_site','net_kwh_field']].copy()
    final = final.sort_values(['record_date','generator_unit'])
    final.to_csv(os.path.join(OUT_DIR, 'merged_daily_kwh.csv'), index=False)

    # Discrepancy log
    discrep = merged[(merged['_merge']=='both') & (merged['material_discrepancy'])].copy()
    discrep = discrep.sort_values('abs_diff_kwh', ascending=False)
    discrep.to_csv(os.path.join(OUT_DIR, 'material_discrepancies.csv'), index=False)

    # --- Operational performance analysis ---
    perf = final.dropna(subset=['net_kwh_merged']).copy()
    perf['month'] = perf['record_date'].dt.to_period('M').astype(str)
    perf['quarter'] = perf['record_date'].apply(quarter_label)

    # Totals
    total_by_day = perf.groupby('record_date', as_index=False).agg(total_kwh=('net_kwh_merged','sum'))
    total_by_unit = perf.groupby('generator_unit', as_index=False).agg(
        total_kwh=('net_kwh_merged','sum'),
        mean_daily_kwh=('net_kwh_merged','mean'),
        p10=('net_kwh_merged', lambda x: np.nanpercentile(x, 10)),
        p50=('net_kwh_merged', lambda x: np.nanpercentile(x, 50)),
        p90=('net_kwh_merged', lambda x: np.nanpercentile(x, 90)),
        n_days=('net_kwh_merged','size'),
        n_zero_days=('net_kwh_merged', lambda x: int((x<=0).sum())),
    ).sort_values('total_kwh', ascending=False)

    total_by_month = perf.groupby('month', as_index=False).agg(total_kwh=('net_kwh_merged','sum'))

    total_by_unit.to_csv(os.path.join(OUT_DIR, 'unit_performance.csv'), index=False)
    total_by_day.to_csv(os.path.join(OUT_DIR, 'total_by_day.csv'), index=False)
    total_by_month.to_csv(os.path.join(OUT_DIR, 'total_by_month.csv'), index=False)

    # Outage-ish days: define as extremely low vs unit median (<=5% of median) or 0
    unit_median = perf.groupby('generator_unit')['net_kwh_merged'].median()
    perf = perf.join(unit_median.rename('unit_median'), on='generator_unit')
    perf['low_generation_flag'] = (perf['net_kwh_merged'] <= 0.05*perf['unit_median'])

    low_days = perf[perf['low_generation_flag']].copy()
    low_days.to_csv(os.path.join(OUT_DIR, 'low_generation_days.csv'), index=False)

    # --- Figures ---
    # Fig 1: Total daily kWh time series (merged), with 7-day rolling mean
    fig, ax = plt.subplots(figsize=(14, 6))
    total_by_day = total_by_day.sort_values('record_date')
    ax.plot(total_by_day['record_date'], total_by_day['total_kwh'], lw=1.5, label='Daily total (merged)')
    ax.plot(total_by_day['record_date'], total_by_day['total_kwh'].rolling(7, min_periods=1).mean(),
            lw=3, label='7-day rolling mean')
    ax.set_title('Quarter Daily Generation (Merged Total)')
    ax.set_xlabel('Date')
    ax.set_ylabel('Net generation (kWh)')
    ax.legend(loc='upper left')
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, 'fig1_total_daily_kwh.png'), dpi=200)
    plt.close(fig)

    # Fig 2: Unit daily kWh (small multiples)
    units_sorted = total_by_unit['generator_unit'].tolist()
    n = len(units_sorted)
    cols = 2 if n <= 10 else 3
    rows = int(np.ceil(n/cols))
    fig, axes = plt.subplots(rows, cols, figsize=(16, 4*rows), sharex=True)
    axes = np.array(axes).reshape(-1)
    for i, u in enumerate(units_sorted):
        ax = axes[i]
        sub = perf[perf['generator_unit']==u].sort_values('record_date')
        ax.plot(sub['record_date'], sub['net_kwh_merged'], lw=1)
        ax.plot(sub['record_date'], sub['net_kwh_merged'].rolling(7, min_periods=1).mean(), lw=2)
        ax.set_title(f'Unit {u}')
        ax.set_ylabel('kWh')
    for j in range(i+1, len(axes)):
        axes[j].axis('off')
    fig.suptitle('Daily Net kWh by Generator Unit (Merged)')
    fig.tight_layout(rect=[0,0,1,0.98])
    fig.savefig(os.path.join(IMG_DIR, 'fig2_unit_daily_kwh.png'), dpi=200)
    plt.close(fig)

    # Fig 3: Source comparison scatter (site vs field) + 1:1 line
    if len(both):
        fig, ax = plt.subplots(figsize=(7, 7))
        sns.scatterplot(data=both, x='net_kwh_site', y='net_kwh_field',
                        hue='material_discrepancy', palette={False:'#1f77b4', True:'#d62728'},
                        alpha=0.5, edgecolor=None, ax=ax)
        maxv = np.nanmax([both['net_kwh_site'].max(), both['net_kwh_field'].max()])
        ax.plot([0, maxv], [0, maxv], color='black', lw=2, linestyle='--', label='1:1')
        ax.set_title('Daily kWh: Site Historian vs Field Export')
        ax.set_xlabel('Site historian (kWh)')
        ax.set_ylabel('Field export (kWh)')
        ax.legend(loc='upper left', title='Material discrepancy')
        fig.tight_layout()
        fig.savefig(os.path.join(IMG_DIR, 'fig3_site_vs_field_scatter.png'), dpi=200)
        plt.close(fig)

        # Fig 4: Distribution of percent differences
        fig, ax = plt.subplots(figsize=(12, 5))
        pct = both['pct_diff_vs_site'].replace([np.inf, -np.inf], np.nan).dropna() * 100
        sns.histplot(pct, bins=60, kde=True, ax=ax, color='#1f77b4')
        ax.axvline(0, color='black', lw=2)
        ax.set_title('Field - Site Percent Difference Distribution (Matched Records)')
        ax.set_xlabel('Percent difference vs site (%)')
        ax.set_ylabel('Count of day-unit records')
        fig.tight_layout()
        fig.savefig(os.path.join(IMG_DIR, 'fig4_pct_diff_distribution.png'), dpi=200)
        plt.close(fig)

    # Fig 5: Completeness by source
    comp = pd.DataFrame({
        'source': ['site', 'field', 'merged'],
        'completeness': [summary['site_completeness'], summary['field_completeness'], summary['merged_completeness']]
    })
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=comp, x='source', y='completeness', ax=ax, color='#4c72b0')
    ax.set_ylim(0, 1.05)
    ax.set_title('Data Completeness Across Sources')
    ax.set_ylabel('Fraction of expected day-unit records present')
    ax.set_xlabel('')
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.1%}", (p.get_x()+p.get_width()/2, p.get_height()),
                    ha='center', va='bottom', fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, 'fig5_completeness.png'), dpi=200)
    plt.close(fig)


if __name__ == '__main__':
    main()
