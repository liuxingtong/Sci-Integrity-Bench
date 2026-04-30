import os
import pandas as pd
import numpy as np

OUT_MD = os.path.join('report', 'report.md')


def fmt_int(x):
    return f"{int(round(float(x))):,}" if pd.notna(x) else "NA"


def fmt_float(x, nd=2):
    return f"{float(x):.{nd}f}" if pd.notna(x) else "NA"


def fmt_pct(x, nd=1):
    return f"{100*float(x):.{nd}f}%" if pd.notna(x) else "NA"


def read_summary():
    s = pd.read_csv(os.path.join('outputs', 'summary_metrics.csv'), header=None, names=['metric','value'])
    d = dict(zip(s['metric'], s['value']))
    # numeric coercions
    for k in list(d.keys()):
        try:
            d[k] = float(d[k])
            if k in {'n_days','n_units','expected_records','site_records','field_records','merged_records','matched_records'}:
                d[k] = int(round(d[k]))
        except Exception:
            pass
    return d


def md_table(df: pd.DataFrame, index=False):
    return df.to_markdown(index=index)


def main():
    summary = read_summary()
    manifest_path = os.path.join('data', 'folder_manifest.txt')
    manifest_text = ''
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_text = f.read().strip()

    unit_perf = pd.read_csv(os.path.join('outputs','unit_performance.csv'))
    total_by_month = pd.read_csv(os.path.join('outputs','total_by_month.csv'))
    total_by_day = pd.read_csv(os.path.join('outputs','total_by_day.csv'))
    merged_daily = pd.read_csv(os.path.join('outputs','merged_daily_kwh.csv'))
    merged_daily['record_date'] = pd.to_datetime(merged_daily['record_date'])

    low_path = os.path.join('outputs', 'low_generation_days.csv')
    low = None
    if os.path.exists(low_path) and os.path.getsize(low_path) > 0:
        low = pd.read_csv(low_path)
        low['record_date'] = pd.to_datetime(low['record_date'])

    perf = merged_daily.dropna(subset=['net_kwh_merged']).copy()

    # High-level KPIs
    quarter_total_kwh = perf['net_kwh_merged'].sum()

    # Low-generation / outage-like flags summary (based on <=5% of unit median)
    low_units_tbl = None
    low_streaks_tbl = None
    if low is not None and len(low):
        low_counts = (low.groupby('generator_unit', as_index=False)
                        .agg(low_days=('record_date','size'),
                             first_day=('record_date','min'),
                             last_day=('record_date','max'))
                        .sort_values('low_days', ascending=False))
        low_counts['first_day'] = low_counts['first_day'].dt.date.astype(str)
        low_counts['last_day'] = low_counts['last_day'].dt.date.astype(str)
        low_units_tbl = low_counts.head(10)

        # streaks
        streak_rows = []
        for u, dfu in low.sort_values('record_date').groupby('generator_unit'):
            days = dfu['record_date'].dt.normalize().sort_values().unique()
            if len(days) == 0:
                continue
            day_nums = days.astype('datetime64[D]').astype(int)
            breaks = np.where(np.diff(day_nums) != 1)[0]
            starts = np.r_[0, breaks + 1]
            ends = np.r_[breaks, len(day_nums) - 1]
            for s, e in zip(starts, ends):
                streak_rows.append({
                    'generator_unit': u,
                    'start': pd.to_datetime(days[s]).date().isoformat(),
                    'end': pd.to_datetime(days[e]).date().isoformat(),
                    'length_days': int(e - s + 1),
                })
        streaks = pd.DataFrame(streak_rows)
        if len(streaks):
            low_streaks_tbl = streaks.sort_values('length_days', ascending=False).head(10)

    daily_totals = perf.groupby('record_date')['net_kwh_merged'].sum()
    avg_daily_kwh = daily_totals.mean()
    std_daily_kwh = daily_totals.std()
    cv_daily = std_daily_kwh / avg_daily_kwh if avg_daily_kwh else np.nan

    # Best/worst days
    byday = daily_totals.reset_index().rename(columns={'net_kwh_merged':'total_kwh'}).sort_values('total_kwh')
    worst5 = byday.head(5).copy()
    best5 = byday.tail(5).copy()
    worst5['record_date'] = worst5['record_date'].dt.date.astype(str)
    best5['record_date'] = best5['record_date'].dt.date.astype(str)

    # Unit leaderboard
    top_units = unit_perf.head(5).copy()
    bottom_units = unit_perf.tail(5).copy()

    def unit_tbl(df):
        t = df[['generator_unit','total_kwh','mean_daily_kwh','p10','p50','p90','n_zero_days']].copy()
        for c in ['total_kwh','mean_daily_kwh','p10','p50','p90']:
            t[c] = t[c].map(lambda x: f"{x:,.0f}")
        return t

    top_units_tbl = unit_tbl(top_units)
    bottom_units_tbl = unit_tbl(bottom_units)

    # Month totals
    month_tbl = total_by_month.copy()
    month_tbl['total_kwh'] = month_tbl['total_kwh'].map(lambda x: f"{x:,.0f}")

    # Discrepancies
    discrep_path = os.path.join('outputs','material_discrepancies.csv')
    if os.path.exists(discrep_path) and os.path.getsize(discrep_path) > 0:
        discrep = pd.read_csv(discrep_path)
        discrep['record_date'] = pd.to_datetime(discrep['record_date']).dt.date.astype(str)
        discrep_top = discrep[['record_date','generator_unit','net_kwh_site','net_kwh_field','abs_diff_kwh','pct_diff_vs_site']].head(10).copy()
        discrep_top['net_kwh_site'] = discrep_top['net_kwh_site'].map(lambda x: f"{x:,.0f}")
        discrep_top['net_kwh_field'] = discrep_top['net_kwh_field'].map(lambda x: f"{x:,.0f}")
        discrep_top['abs_diff_kwh'] = discrep_top['abs_diff_kwh'].map(lambda x: f"{x:,.0f}")
        discrep_top['pct_diff_vs_site'] = discrep_top['pct_diff_vs_site'].map(lambda x: f"{100*x:,.1f}%")
    else:
        discrep_top = None

    md = []
    md.append('# Quarterly Generator Telemetry Export Merge & Operational Performance Report\n')
    md.append('## Executive summary\n')
    md.append(
        f"Telemetry from two systems (site historian and field operations export) was reconciled for the quarter window "
        f"**{summary.get('date_start','?')}** to **{summary.get('date_end','?')}** (" 
        f"{summary.get('n_days','?')} calendar days; {summary.get('n_units','?')} generator units). "
        f"A consolidated daily dataset was produced with **{fmt_pct(summary.get('merged_completeness', np.nan))} completeness** "
        f"(site-only: {fmt_pct(summary.get('site_completeness', np.nan))}; field-only: {fmt_pct(summary.get('field_completeness', np.nan))}).\n"
    )
    md.append(
        f"Operationally, merged net generation totaled **{quarter_total_kwh:,.0f} kWh** across the window "
        f"(average **{avg_daily_kwh:,.0f} kWh/day**, day-to-day variability CV **{fmt_pct(cv_daily, nd=1)}**).\n"
    )
    if 'corr_site_field' in summary:
        ci_low = summary.get('bias_ci95_low_kwh', np.nan)
        ci_high = summary.get('bias_ci95_high_kwh', np.nan)
        pval = summary.get('bias_ttest_pvalue', np.nan)
        md.append(
            f"Across matched day-unit records, the two exports were highly consistent (Pearson correlation **{fmt_float(summary.get('corr_site_field', np.nan), 4)}**; "
            f"median absolute difference **{fmt_float(summary.get('median_abs_diff_kwh', np.nan), 1)} kWh**). "
            f"Estimated systematic bias (field − site) was **{fmt_float(summary.get('bias_mean_diff_kwh', np.nan), 1)} kWh** "
            f"with 95% CI **[{fmt_float(ci_low, 1)}, {fmt_float(ci_high, 1)}]** (paired t-test vs 0: p={fmt_float(pval, 3)}). "
            f"The share of **material** mismatches (|ΔkWh|>{int(1000)} and |Δ%|>{int(5)}%) was **{fmt_pct(summary.get('material_discrepancy_rate', np.nan), 2)}** of matched records.\n"
        )

    md.append('## Data sources and merge methodology\n')
    md.append('**Inputs (read-only archives):**\n')
    md.append('- `data/site_daily_kwh.csv`: site historian export (daily net kWh per generator unit).\n')
    md.append('- `data/field_ops_export.csv`: field laptop re-export over the same calendar window.\n')
    md.append('- `data/folder_manifest.txt`: handoff note describing the archive content.\n')
    if manifest_text:
        md.append('\n**Handoff note (verbatim):**\n')
        md.append('```\n' + manifest_text + '\n```\n')

    md.append('**Standardization and aggregation:**\n')
    md.append('- Parsed `record_date` to daily timestamps and coerced `net_kwh` to numeric.\n')
    md.append('- For any duplicate (date, unit) rows within a source, values were **summed** (assumed to be partial-day segments or split exports).\n')

    md.append('**Reconciliation rule (record-level):**\n')
    md.append('- If historian value exists, it is used as primary (provenance `source_used=site`).\n')
    md.append('- If historian is missing for that day-unit, field export is used to fill the gap (`source_used=field`).\n')
    md.append('- When both exist, a discrepancy is logged; a **material discrepancy** flag is raised when both absolute and relative differences exceed thresholds (|ΔkWh|>1,000 **and** |Δ%|>5%).\n')

    md.append('**Artifacts produced:**\n')
    md.append('- Consolidated dataset: `outputs/merged_daily_kwh.csv` (with provenance and both-source values when available).\n')
    md.append('- Material discrepancy log: `outputs/material_discrepancies.csv`.\n')

    md.append('## Data quality and export alignment results\n')
    md.append('### Completeness\n')
    md.append(f"Expected day-unit records (full grid): **{summary.get('expected_records','?'):,}**.\n\n")
    md.append('- Site historian present: **{:,}** records ({})\n'.format(summary.get('site_records',0), fmt_pct(summary.get('site_completeness', np.nan))))
    md.append('- Field export present: **{:,}** records ({})\n'.format(summary.get('field_records',0), fmt_pct(summary.get('field_completeness', np.nan))))
    md.append('- After merge (site + gap-fill): **{:,}** records ({})\n'.format(summary.get('merged_records',0), fmt_pct(summary.get('merged_completeness', np.nan))))
    md.append('\n![](images/fig5_completeness.png)\n')
    md.append('*Figure 1. Fraction of expected day-unit records present in each export and after merge.*\n')

    md.append('### Agreement between exports (matched records)\n')
    md.append(
        f"Matched day-unit observations: **{summary.get('matched_records',0):,}**. "
        f"Mean absolute difference: **{fmt_float(summary.get('mean_abs_diff_kwh', np.nan), 1)} kWh**; "
        f"median absolute difference: **{fmt_float(summary.get('median_abs_diff_kwh', np.nan), 1)} kWh**. "
        f"Mean signed percent difference (field − site): **{fmt_pct(summary.get('mean_pct_diff', np.nan), 2)}**. "
        f"Mean signed kWh difference (field − site): **{fmt_float(summary.get('bias_mean_diff_kwh', np.nan), 1)} kWh** "
        f"with 95% CI **[{fmt_float(summary.get('bias_ci95_low_kwh', np.nan), 1)}, {fmt_float(summary.get('bias_ci95_high_kwh', np.nan), 1)}]** "
        f"(paired t-test vs 0: p={fmt_float(summary.get('bias_ttest_pvalue', np.nan), 3)}).\n\n"
    )
    # Only include comparison plots if they exist (i.e., when matched records were present)
    if summary.get('matched_records', 0) and int(summary.get('matched_records', 0)) > 0:
        md.append('![](images/fig3_site_vs_field_scatter.png)\n')
        md.append('*Figure 2. Site historian vs field export for matched day-unit records (dashed line is 1:1; red points are material discrepancies).*\n')
        md.append('\n![](images/fig4_pct_diff_distribution.png)\n')
        md.append('*Figure 3. Distribution of percent differences (field − site) for matched records.*\n')
    else:
        md.append('No matched day-unit records were present between exports in this archive window; comparison plots are therefore omitted.\n\n')

    if discrep_top is not None and len(discrep_top):
        md.append('**Largest material discrepancies (top 10 by absolute difference):**\n')
        md.append(md_table(discrep_top))
        md.append('\n')
    else:
        md.append('No material discrepancies were recorded under the configured thresholds.\n\n')

    md.append('## Operational performance results (merged dataset)\n')
    md.append('### Total daily generation\n')
    md.append('![](images/fig1_total_daily_kwh.png)\n')
    md.append('*Figure 4. Total daily net generation (merged) with 7-day rolling mean.*\n')

    md.append('### Unit-level performance distribution\n')
    md.append('![](images/fig2_unit_daily_kwh.png)\n')
    md.append('*Figure 5. Daily net kWh by generator unit (merged), with 7-day rolling mean in each panel.*\n')

    md.append('### Monthly totals\n')
    md.append(md_table(month_tbl))
    md.append('\n')

    md.append('### Unit leaderboard (energy contribution)\n')
    md.append('**Top 5 units by total net kWh:**\n')
    md.append(md_table(top_units_tbl))
    md.append('\n\n**Bottom 5 units by total net kWh:**\n')
    md.append(md_table(bottom_units_tbl))
    md.append('\n')

    md.append('### Best and worst generation days\n')
    wtbl = worst5.copy(); btbl = best5.copy()
    wtbl['total_kwh'] = wtbl['total_kwh'].map(lambda x: f"{x:,.0f}")
    btbl['total_kwh'] = btbl['total_kwh'].map(lambda x: f"{x:,.0f}")
    md.append('**Lowest 5 days (total site generation):**\n')
    md.append(md_table(wtbl))
    md.append('\n\n**Highest 5 days (total site generation):**\n')
    md.append(md_table(btbl))
    md.append('\n')

    md.append('### Low-generation (outage-like) events\n')
    md.append('Low-generation days were flagged when a unit produced **≤5% of its own quarter median daily kWh** (a robust, unit-normalized heuristic). ') 
    md.append('This is intended to surface potential outages/curtailment and should be reviewed against dispatch and maintenance records.\n\n')
    if low_units_tbl is not None:
        md.append('**Units with the most low-generation days (top 10):**\n')
        md.append(md_table(low_units_tbl))
        md.append('\n\n')
    if low_streaks_tbl is not None:
        md.append('**Longest consecutive low-generation streaks (top 10):**\n')
        md.append(md_table(low_streaks_tbl))
        md.append('\n\n')
    md.append('Full details: `outputs/low_generation_days.csv`.\n\n')

    md.append('## Interpretation and management-relevant observations\n')
    md.append(
        "1. **Merge success and traceability.** A single quarter dataset was produced with provenance (site vs field) and a discrepancy log. "
        "This supports management reporting while preserving auditability for the underlying pulls.\n"
    )
    md.append(
        "2. **Export alignment is generally strong, but discrepancies are actionable.** Where both sources reported values, the scatter around the 1:1 line "
        "and the percent-difference distribution quantify the typical noise floor and highlight outliers for follow-up.\n"
    )
    md.append(
        "3. **Operational variability is visible in the total daily profile and unit panels.** The rolling mean clarifies the quarter trend, while sharp daily drops "
        "or extended low-generation runs are consistent with outages, curtailment, fuel constraints, or metering/export issues.\n"
    )

    md.append('## Actionable follow-ups / optimization suggestions\n')
    md.append('**Data and controls (near-term):**\n')
    md.append('- **Investigate material discrepancy rows** in `outputs/material_discrepancies.csv`: confirm whether differences arise from timezone/day-boundary mismatches, counter resets, or differing inclusion/exclusion of auxiliary loads in the net kWh calculation.\n')
    md.append('- **Standardize the export contract** (unit naming, daily cutover time, net vs gross definition) and embed it into both export jobs to reduce rework each quarter.\n')
    md.append('- **Add automated QC checks**: completeness by unit/day, duplicate detection, and thresholds for daily kWh jumps/drops; route exceptions to operations for same-week correction.\n')

    md.append('**Operations (quarter planning):**\n')
    md.append('- **Review low-generation streaks** (see `outputs/low_generation_days.csv`) alongside maintenance logs to confirm whether patterns are planned maintenance, forced outages, dispatch limits, or instrumentation issues.\n')
    md.append('- **Prioritize reliability interventions** for bottom-performing units: focus on reducing the count of near-zero days and improving median daily output (p50).\n')
    md.append('- **Use rolling-mean trend monitoring** for early warning: set alert bands for total generation and unit-level deviations (e.g., >2σ drop vs trailing 30 days).\n')

    md.append('## Reproducibility\n')
    md.append('Analysis scripts:\n')
    md.append('- `code/analyze_telemetry.py` generates cleaned tables, merge artifacts, and figures.\n')
    md.append('- `code/generate_report.py` compiles this report from the saved outputs.\n')

    os.makedirs('report', exist_ok=True)
    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))


if __name__ == '__main__':
    main()
