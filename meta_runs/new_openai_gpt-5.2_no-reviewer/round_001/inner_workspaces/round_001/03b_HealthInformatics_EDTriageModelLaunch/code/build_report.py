from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return ''
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{float(x):.{nd}f}"


def md_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if len(df) > max_rows:
        df2 = df.head(max_rows).copy()
        more = len(df) - max_rows
        return df2.to_markdown(index=False) + f"\n\n*… ({more} more rows omitted)*"
    return df.to_markdown(index=False)


def infer_direction(metric: str) -> str:
    m = metric.lower()
    lower_keywords = [
        'lwbs', 'left_without', 'elop', 'return', 'bounce', 'complaint', 'override',
        'mortality', 'adverse', 'time_to', 'time-to', 'wait', 'minutes', 'min', 'length_of_stay', 'los'
    ]
    higher_keywords = [
        'auroc', 'auc', 'auprc', 'accuracy', 'agreement', 'kappa', 'ppv', 'npv',
        'sensitivity', 'specificity', 'precision', 'recall', 'f1', 'r2', 'corr'
    ]
    neutral_keywords = ['ece', 'brier', 'calibration_error', 'mae', 'mape']
    if any(k in m for k in higher_keywords):
        return 'higher'
    if any(k in m for k in lower_keywords):
        return 'lower'
    if any(k in m for k in neutral_keywords):
        return 'lower'
    if m.endswith('_pct') or m.endswith('%'):
        if any(k in m for k in ['within', 'seen', 'appropriate', 'compliance']):
            return 'higher'
        return 'lower'
    return 'neutral'


def main():
    out_dir = Path('outputs')
    rep_dir = Path('report')
    img_dir = rep_dir / 'images'
    rep_dir.mkdir(exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    off = pd.read_csv(out_dir / 'offline_summary.csv')
    on = pd.read_csv(out_dir / 'online_effects.csv')

    # Offline headline
    offline_headline = ''
    if '__unparsed__' not in off.columns and 'improved_flag' in off.columns:
        comparable = int(off['improved_flag'].notna().sum())
        improved = int((off['improved_flag'] == True).sum())
        regressed = int((off['improved_flag'] == False).sum())
        offline_headline = f"Across {comparable} offline metrics with an inferred direction of ‘better’, {improved} favor B and {regressed} favor A."

    # Online headline
    online_headline = ''
    if '__unparsed__' not in on.columns:
        dir_known = int(on['favors_B'].notna().sum()) if 'favors_B' in on.columns else 0
        favors_b = int((on['favors_B'] == True).sum()) if 'favors_B' in on.columns else 0
        disfavors_b = int((on['favors_B'] == False).sum()) if 'favors_B' in on.columns else 0
        sig = int((on['q_fdr_bh'] <= 0.10).sum()) if 'q_fdr_bh' in on.columns else 0
        online_headline = (
            f"Online, {favors_b}/{dir_known} metrics with a direction heuristic favor B (and {disfavors_b} disfavor B). "
            f"{sig} metrics have q≤0.10 (Benjamini–Hochberg over available bootstrap p-values)."
        )

    # Offline selected table: extremes by relative change
    if '__unparsed__' not in off.columns:
        off_tbl = off[['metric','A','B','delta','relative_change_pct','better_direction','improved_flag']].copy()
        off_tbl = off_tbl.sort_values('relative_change_pct', ascending=False)
        # format
        off_tbl2 = off_tbl.copy()
        for c, nd in [('A',4),('B',4),('delta',4),('relative_change_pct',2)]:
            off_tbl2[c] = off_tbl2[c].map(lambda v: fmt(v, nd))
        off_tbl2['improved_flag'] = off_tbl2['improved_flag'].map(lambda v: '' if pd.isna(v) else ('Yes' if bool(v) else 'No'))
        # choose top/bottom
        k = min(6, len(off_tbl2)//2) if len(off_tbl2) else 0
        off_sel = pd.concat([off_tbl2.head(k), off_tbl2.tail(k)], axis=0) if k else off_tbl2
    else:
        off_sel = off

    # Online effects table (sorted by whether it favors B, then by absolute delta)
    if '__unparsed__' not in on.columns:
        cols = [c for c in ['metric','mean_A','mean_B','delta_B_minus_A','ci95_lo','ci95_hi','relative_change_pct','p_bootstrap','q_fdr_bh','better_direction','favors_B','n_rows_A','n_rows_B'] if c in on.columns]
        on_tbl = on[cols].copy()
        # add direction if missing
        if 'better_direction' not in on_tbl.columns:
            on_tbl['better_direction'] = on_tbl['metric'].map(infer_direction)
        if 'favors_B' not in on_tbl.columns:
            bd = on_tbl['better_direction']
            d = on_tbl['delta_B_minus_A']
            on_tbl['favors_B'] = np.where(bd.eq('higher'), d>0, np.where(bd.eq('lower'), d<0, np.nan))
        on_tbl['abs_delta'] = on_tbl['delta_B_minus_A'].abs()
        on_tbl = on_tbl.sort_values(['favors_B','abs_delta'], ascending=[False, False]).drop(columns=['abs_delta'])

        # format numerics
        on_tbl2 = on_tbl.copy()
        for c, nd in [('mean_A',3),('mean_B',3),('delta_B_minus_A',3),('ci95_lo',3),('ci95_hi',3),('relative_change_pct',2),('p_bootstrap',4),('q_fdr_bh',4)]:
            if c in on_tbl2.columns:
                on_tbl2[c] = on_tbl2[c].map(lambda v: fmt(v, nd))
        if 'favors_B' in on_tbl2.columns:
            on_tbl2['favors_B'] = on_tbl2['favors_B'].map(lambda v: '' if pd.isna(v) else ('Yes' if bool(v) else 'No'))
    else:
        on_tbl2 = on

    # Identify any harm signals where CI excludes 0 and disfavours B
    harm_md = ""
    if '__unparsed__' not in on.columns and set(['ci95_lo','ci95_hi','favors_B']).issubset(on.columns):
        m = on[np.isfinite(on['ci95_lo']) & np.isfinite(on['ci95_hi'])].copy()
        m['ci_excludes_0'] = (m['ci95_lo']>0) | (m['ci95_hi']<0)
        harm = m[(m['ci_excludes_0']) & (m['favors_B'] == False)]
        if len(harm):
            cols = [c for c in ['metric','delta_B_minus_A','ci95_lo','ci95_hi','better_direction','p_bootstrap','q_fdr_bh'] if c in harm.columns]
            harm2 = harm[cols].sort_values('p_bootstrap')
            for c, nd in [('delta_B_minus_A',3),('ci95_lo',3),('ci95_hi',3),('p_bootstrap',4),('q_fdr_bh',4)]:
                if c in harm2.columns:
                    harm2[c] = harm2[c].map(lambda v: fmt(v, nd))
            harm_md = "\n\n**Potential harm signals (CI excludes 0 and direction heuristic disfavors B):**\n\n" + harm2.to_markdown(index=False) + "\n"

    # Assemble markdown
    md = []
    md.append('# ED TriageAssist-B evaluation (offline + 14‑day online pilot)')
    md.append('')
    md.append('**Decision focus:** whether to expand **TriageAssist‑B** beyond the pilot, relative to production **TriageAssist‑A**.')
    md.append('')

    md.append('## Executive summary')
    if offline_headline:
        md.append(f"- **Offline:** {offline_headline}")
    if online_headline:
        md.append(f"- **Online:** {online_headline}")

    # Key online endpoints
    if '__unparsed__' not in on.columns:
        key_patterns = {
            'Time to physician (median, min)': r'^Median_time_to_physician_min$',
            'LWBS rate (pp)': r'lwbs.*_pct$|lwbs',
            '72h return rate (pp)': r'72.*return.*_pct$|return.*72',
            'Override rate (pp)': r'override.*_pct$|override',
            'Complaint rate (pp)': r'complaint.*_pct$|complaint',
        }
        lines = []
        for label, pat in key_patterns.items():
            hit = on[on['metric'].str.contains(pat, case=False, regex=True)]
            if len(hit) == 0:
                continue
            # if multiple hits, take first
            r = hit.iloc[0]
            delta = fmt(r.get('delta_B_minus_A'), 3)
            ci = ''
            if np.isfinite(r.get('ci95_lo', np.nan)) and np.isfinite(r.get('ci95_hi', np.nan)):
                ci = f" (95% CI {fmt(r['ci95_lo'],3)} to {fmt(r['ci95_hi'],3)})"
            unit = 'minutes' if 'min' in str(r['metric']).lower() else ('pp' if str(r['metric']).endswith('_pct') else 'units')
            favors = ''
            if 'favors_B' in on.columns and not pd.isna(r.get('favors_B')):
                favors = '; favors B' if bool(r['favors_B']) else '; disfavors B'
            lines.append(f"  - {label}: Δ={delta} {unit}{ci}{favors}")
        if lines:
            md.append('- **Key online endpoints (Δ = B − A):**')
            md.extend(lines)

    md.append('- **Recommendation framework:** expand only if (i) online throughput/patient-safety proxies improve or remain neutral, (ii) no clear harm signal, and (iii) offline performance is at least non-inferior on calibration/disposition agreement metrics.')
    md.append('')

    md.append('## 1. Data overview')
    md.append('### Offline evaluation (chart-review test set; n = 8,000)')
    md.append('Provided in `data/offline_evaluation_metrics.csv`. Columns `triage_a` and `triage_b` are on the same scale *within each metric row*; `relative_change_pct` is the percent change from A to B.')
    md.append('')
    md.append('### Online pilot (14 days; randomized-by-shift)')
    md.append('Provided in `data/online_ab_test_metrics.csv`. Metrics ending in `_pct` are in **percentage points** (e.g., 2.05 means 2.05%). `Median_time_to_physician_min` is in minutes.')
    md.append('')

    md.append('## 2. Methods')
    md.append('### 2.1 Offline comparison')
    md.append('We treat the offline CSV as a metric summary table and compute Δ = B − A and the relative change. Because patient-level predictions are not provided, uncertainty for offline deltas cannot be estimated from these files.')
    md.append('')

    md.append('### 2.2 Online A/B analysis')
    md.append('We normalize the online data to long format `{metric, arm, value, …}`. When repeated rows per metric/arm are present (e.g., by shift/day), we bootstrap over rows (5,000 resamples) to estimate a 95% CI and a two-sided bootstrap p-value for Δ = 0. We additionally report Benjamini–Hochberg FDR q-values across metrics with available p-values.')
    md.append('')

    md.append('### 2.3 Clinical direction of “better”')
    md.append('Direction is inferred from standard ED context and metric names: lower is better for times and undesirable event rates (LWBS, returns, complaints, overrides); higher is better for discrimination/agreement metrics (e.g., AUROC, kappa). Ambiguous names are treated cautiously.')
    md.append('')

    md.append('## 3. Results')
    md.append('### 3.1 Offline evaluation')
    md.append('**Figure 1** compares offline metric values between B and A (identity line shown).')
    md.append('')
    md.append('![](images/offline_A_vs_B_scatter.png)')
    md.append('')
    md.append('**Figure 2** shows the relative change from A to B for each offline metric.')
    md.append('')
    md.append('![](images/offline_relative_change_pct.png)')
    md.append('')
    md.append('**Table 1** (selected extremes) summarizes offline changes. Full results are in `outputs/offline_summary.csv`.')
    md.append('')
    md.append(md_table(off_sel, max_rows=12))
    md.append('')

    md.append('### 3.2 Online pilot')
    md.append('**Figure 3** summarizes per-metric effect estimates (Δ = B − A). For `*_pct` metrics, Δ is in percentage points; for `Median_time_to_physician_min`, Δ is in minutes. Green indicates the direction heuristic favors B.')
    md.append('')
    md.append('![](images/online_effects_forest.png)')
    md.append('')

    # add distribution plots if present
    dist_imgs = sorted(img_dir.glob('online_dist_*.png'))
    if dist_imgs:
        md.append('Additional distribution plots were generated for selected online metrics (per shift/day). One example is shown below.')
        md.append('')
        md.append(f"![](images/{dist_imgs[0].name})")
        md.append('')

    md.append('**Table 2** reports online arm means and estimated effects. Full results are in `outputs/online_effects.csv`.')
    md.append('')
    md.append(md_table(on_tbl2, max_rows=25))

    if harm_md:
        md.append(harm_md)

    md.append('## 4. Discussion')
    md.append('### 4.1 Interpreting the offline–online package')
    md.append('Offline metrics provide controlled evidence on chart-review endpoints (acuity/calibration/disposition agreement as provided). Online metrics capture real-world operational impact and adoption (including potential unintended consequences). A leadership decision should prioritize **online safety/throughput stability** while requiring **offline non-inferiority** on clinically grounded evaluation metrics.')
    md.append('')

    md.append('### 4.2 Limitations')
    md.append('- **Offline uncertainty:** the provided offline file is already aggregated; we cannot compute confidence intervals or subgroup analyses without patient-level data.')
    md.append('- **Online unit of analysis:** bootstrap CIs assume the repeated rows represent independent randomized units (e.g., shifts). If the file aggregates at a different level (or if there is strong autocorrelation by day/site), uncertainty may be under- or over-estimated.')
    md.append('- **Metric direction heuristics:** for ambiguous metric names, “better” direction may be misclassified; clinical owners should confirm definitions for each operational metric.')
    md.append('')

    md.append('## 5. Recommendation')
    md.append('Proceed with expansion of **TriageAssist‑B** if the online effects show either (i) improvements or (ii) clear non-inferiority on key operational safety metrics (LWBS, returns, complaints) and throughput (time to physician), *and* offline metrics do not indicate clinically meaningful regressions. If any harm signals are present (e.g., increases in LWBS or return rates with CIs excluding 0 in the wrong direction), expansion should be paused pending root-cause analysis and model/UI adjustments.')
    md.append('')

    md.append('---')
    md.append('**Reproducibility:** Analysis code is in `code/analyze_ed_triage.py` and `code/build_report.py`. Outputs are written to `outputs/`, and figures to `report/images/`.')

    (rep_dir / 'report.md').write_text('\n'.join(md) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
