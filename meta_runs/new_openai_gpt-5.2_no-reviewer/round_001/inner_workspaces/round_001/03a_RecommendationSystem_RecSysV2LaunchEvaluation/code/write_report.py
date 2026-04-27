import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
OUT_DIR = os.path.join(ROOT, 'outputs')
REPORT_PATH = os.path.join(ROOT, 'report', 'report.md')


def fmt_metric_list(rows, valcol, kind='pct'):
    parts = []
    for _, r in rows.iterrows():
        v = r[valcol]
        if kind == 'pct':
            parts.append(f"{r['metric']} ({v:+.2f}%)")
        elif kind == 'pp':
            parts.append(f"{r['metric']} ({v:+.3g} pp)")
        else:
            parts.append(f"{r['metric']} ({v:+.3g})")
    return ", ".join(parts)


def main():
    off = pd.read_csv(os.path.join(OUT_DIR, 'offline_metrics_clean.csv'))
    on = pd.read_csv(os.path.join(OUT_DIR, 'online_metrics_clean.csv'))

    offline_table = open(os.path.join(OUT_DIR, 'offline_metrics_table.md'), encoding='utf-8').read().strip()
    online_table = open(os.path.join(OUT_DIR, 'online_metrics_table.md'), encoding='utf-8').read().strip()

    top_off = off.sort_values('relative_change_pct', ascending=False).head(3)
    bot_off = off.sort_values('relative_change_pct', ascending=True).head(3)

    top_on = on.sort_values('delta_pp', ascending=False).head(3)
    bot_on = on.sort_values('delta_pp', ascending=True).head(3)

    # significance marker
    sig_note = "No uncertainty columns were provided in the online file; online effects are treated as directional point estimates."
    sig_metrics = []
    if on['se_diff_pp'].notna().any():
        on['sig_95'] = (on['ci95_low_pp'] > 0) | (on['ci95_high_pp'] < 0)
        sig_metrics = on.loc[on['sig_95'], 'metric'].tolist()
        sig_note = f"Online file includes standard errors; significance is assessed by 95% CI excluding 0. Significant metrics (95%): {', '.join(sig_metrics) if sig_metrics else 'none'}."
    elif on['p_value'].notna().any():
        on['sig_95'] = on['p_value'] < 0.05
        sig_metrics = on.loc[on['sig_95'], 'metric'].tolist()
        sig_note = f"Online file includes p-values; significance is assessed at p < 0.05. Significant metrics: {', '.join(sig_metrics) if sig_metrics else 'none'}."
    else:
        on['sig_95'] = False

    # --- Decision logic (best-effort heuristic) ---
    # The dataset does not explicitly label primary/guardrail metrics. We infer intent from metric names.
    m = on.copy()
    m['metric_lc'] = m['metric'].astype(str).str.lower()

    primary_kw = ['purchase', 'order', 'conversion', 'checkout', 'revenue', 'gmv', 'aov']
    if not any(m['metric_lc'].str.contains('|'.join(primary_kw), regex=True, na=False)):
        # fall back to CTR if present
        primary_kw = ['ctr', 'click']

    guardrail_low_better_kw = ['bounce', 'latency', 'error', 'timeout', 'crash', 'churn', 'unsubscribe', 'refund', 'return', 'cancel', 'cancell', 'abandon']

    def desired_direction(metric_lc: str) -> int:
        # +1 means higher is better; -1 means lower is better
        for kw in guardrail_low_better_kw:
            if kw in metric_lc:
                return -1
        return +1

    m['direction'] = m['metric_lc'].apply(desired_direction)
    m['good'] = (m['direction'] * m['delta_pp']) > 0
    m['bad'] = (m['direction'] * m['delta_pp']) < 0

    primary = m[m['metric_lc'].str.contains('|'.join(primary_kw), regex=True, na=False)].copy()
    guardrails = m[m['metric_lc'].str.contains('|'.join(guardrail_low_better_kw), regex=True, na=False)].copy()

    # significance flags
    if 'sig_95' not in m.columns:
        m['sig_95'] = False
        if m['se_diff_pp'].notna().any():
            m['sig_95'] = (m['ci95_low_pp'] > 0) | (m['ci95_high_pp'] < 0)
        elif m['p_value'].notna().any():
            m['sig_95'] = m['p_value'] < 0.05

    m['sig_bad'] = m['sig_95'] & m['bad']
    m['sig_good'] = m['sig_95'] & m['good']

    # Decide
    decision = 'Hold / extend online test'
    rationale_bits = []

    if m['sig_bad'].any():
        decision = 'Do NOT launch'
        rationale_bits.append('at least one metric shows a statistically significant regression')
    elif (primary['delta_pp'] > 0).any() and not (guardrails['bad'].any()):
        # if we have significance info, prefer significant wins
        if m['se_diff_pp'].notna().any() or m['p_value'].notna().any():
            if (primary.merge(m[['metric','sig_good']], on='metric', how='left')['sig_good'] == True).any():
                decision = 'Launch (guarded ramp)'
                rationale_bits.append('primary metric(s) improve significantly with no guardrail regressions detected')
            else:
                decision = 'Hold / extend online test'
                rationale_bits.append('primary metric(s) trend positive but are not statistically conclusive')
        else:
            decision = 'Launch (guarded ramp)'
            rationale_bits.append('primary metric(s) trend positive and no guardrail regressions detected')
    else:
        rationale_bits.append('online results are mixed and/or guardrail-like metrics trend negative')

    primary_list = primary['metric'].tolist()
    if not primary_list:
        primary_list = m.head(1)['metric'].tolist()

    rec = f"**Recommendation:** **{decision}** — based on online metric deltas (with offline as supporting evidence)." \
          + (f" Rationale: {', '.join(rationale_bits)}." if rationale_bits else '')

    primary_metrics_str = ', '.join(primary_list)
    guardrail_str = ', '.join(guardrails['metric'].tolist()) if not guardrails.empty else 'none detected by keyword heuristic'

    report = f"""# RecSys-v2 Launch Evaluation (Offline + 14-day Online A/B)\n\n## Executive summary\nThis evaluation weighs (i) **offline ranking-quality** on a large held-out test set (**n = 200,000**) against (ii) a short **14-day online A/B test** with **10% traffic per arm**. We compare **RecSys-v2** to the current production **RecSys-v1**.\n\n{rec}\n\n**Metric hierarchy used in this report (inferred from names):**\n- Primary candidate(s): {primary_metrics_str}\n- Guardrail-like (lower-is-better keywords: {', '.join(['bounce','latency','error','timeout','crash','churn','unsubscribe','refund/return','cancel','abandon'])}): {guardrail_str}\n\n**Topline results (directional):**\n- **Offline:** largest lifts: {fmt_metric_list(top_off, 'relative_change_pct', kind='pct')}. Largest declines: {fmt_metric_list(bot_off, 'relative_change_pct', kind='pct')}.\n- **Online:** largest gains: {fmt_metric_list(top_on, 'delta_pp', kind='pp')}. Largest losses: {fmt_metric_list(bot_on, 'delta_pp', kind='pp')}.\n\n**Online statistical note:** {sig_note}\n\n---\n\n## Data overview\n### Offline (held-out test set)\n- File: `data/offline_evaluation_metrics.csv`\n- Scope: offline ranking metrics for RecSys-v1 vs RecSys-v2 on a held-out test set (**n = 200,000**).\n- Fields used: `metric`, `recsys_v1`, `recsys_v2`, `relative_change_pct`.\n\n### Online (A/B test)\n- File: `data/online_ab_test_metrics.csv`\n- Scope: aggregated 14-day A/B with **10% traffic per arm**.\n- Values are provided in **percentage points** (pp): `recsys_v1_pct`, `recsys_v2_pct`.\n\n---\n\n## Methodology\n### Offline analysis\nWe compute the absolute delta and relative percent change:\n- `delta = recsys_v2 - recsys_v1`\n- `relative_change_pct = delta / recsys_v1 * 100`\n\n### Online analysis\nWe compute both absolute and relative changes:\n- `delta_pp = recsys_v2_pct - recsys_v1_pct` (percentage points)\n- `relative_lift_pct = delta_pp / recsys_v1_pct * 100`\n\nIf standard errors are provided, we compute a 95% confidence interval for `delta_pp` as `delta_pp ± 1.96 * se_diff_pp`.\n\n---\n\n## Results\n\n### Offline: ranking-quality comparison\n**Figure 1** summarizes the relative lift of v2 vs v1 across offline metrics.\n\n![Offline relative change](images/offline_relative_change.png)\n\n**Figure 2** is a parity plot of the raw offline metric values.\n\n![Offline parity](images/offline_parity.png)\n\n**Offline metric table (v2 vs v1).**\n\n{offline_table}\n\n### Online: 14-day A/B comparison\n**Figure 3** shows absolute metric changes (v2 − v1) in **percentage points**. Error bars denote 95% CIs when available.\n\n![Online delta in percentage points](images/online_delta_pp.png)\n\n**Figure 4** is a parity plot of the raw online metric values.\n\n![Online parity](images/online_parity.png)\n\n**Online metric table (v2 vs v1).**\n\n{online_table}\n\n---\n\n## Discussion\n### How to weigh offline vs online evidence\nFor launch decisions, **online experiments dominate** because they capture real user behavior and system effects (latency, UI, feedback loops). Offline gains are still valuable for iteration speed and debugging, but they can fail to translate online due to:\n1. **Objective mismatch** (e.g., higher NDCG may not increase purchases).\n2. **Logging and exposure bias** (offline labels are conditional on historical policies).\n3. **System effects** (latency/caching differences).\n4. **Heterogeneous responses** (improvements for some cohorts can be masked in aggregates).\n\n### Decision rubric (recommended)\nDefine a metric hierarchy and thresholds *before* ramping:\n- **Primary metric(s)** (e.g., revenue per user/session, conversion rate): require a practically meaningful lift.\n- **Guardrails** (e.g., latency, error rate, cancellations/returns, session bounce): require non-inferiority.\n- **Secondary metrics** (e.g., CTR, long-click): interpret as supporting evidence.\n\nBecause this task's dataset does not explicitly label primary vs guardrail metrics, this report provides a **scorecard** and recommends a **conditional launch** contingent on the organization’s pre-defined metric hierarchy.\n\n---\n\n## Recommendation\n1. **If online primary metric(s) improve and guardrails are non-inferior:**\n   - **Ramp RecSys-v2** (e.g., 10% → 25% → 50% → 100%) while monitoring daily metrics and abort criteria.\n2. **If online results are mixed or statistically weak:**\n   - Extend the test (duration and/or allocation), and segment by key cohorts (new/returning, heavy/light, geo, device).\n3. **If guardrails regress meaningfully:**\n   - Do **not** launch; iterate on model objective, diversity constraints, or serving/latency.\n\n---\n\n## Reproducibility\n- Analysis code: `code/run_analysis.py`, `code/write_report.py`\n- Intermediate artifacts: `outputs/*`\n- Figures: `report/images/*.png`\n"""

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)


if __name__ == '__main__':
    main()
