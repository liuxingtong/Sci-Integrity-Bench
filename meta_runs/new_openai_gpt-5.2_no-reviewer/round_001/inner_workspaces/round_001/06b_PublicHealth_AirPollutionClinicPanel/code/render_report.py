import json
import pandas as pd

TEMPLATE_PATH = 'report/report.md'

meta = json.load(open('outputs/analysis_metadata.json'))
key = json.load(open('outputs/key_results.json'))

schema = meta['schema']
summary = meta['data_summary']

# Exceedance rates
ex = pd.read_csv('outputs/pm25_exceedance_rates.csv').iloc[0].to_dict()

# Main effects
main = key['main_effect_poisson']
nb = key['main_effect_negbin']

# Policy table
pol = pd.read_csv('outputs/policy_counterfactual_summary.csv').sort_values('cap_pm25')
rows = []
for _, r in pol.iterrows():
    rows.append(
        f"| {r['cap_pm25']:.0f} | {r['total_pred_visits']:.0f} | {r['total_averted_visits']:.0f} | {r['pct_reduction']:.2f}% |"
    )
policy_table = "\n".join(rows)

ex15 = ex.get('exceed_15', float('nan'))
ex25 = ex.get('exceed_25', float('nan'))
ex35 = ex.get('exceed_35', float('nan'))

repl = {
    '{DATE_MIN}': summary['date_min'],
    '{DATE_MAX}': summary['date_max'],
    '{N_DAYS}': str(summary['n_days']),
    '{N_ROWS}': str(summary['n_rows']),
    '{N_PANELS}': str(summary.get('n_panels', 1)),
    '{OUTCOME_COL}': schema['outcome_col'],
    '{PM25_COL}': schema['pm25_col'],
    '{PM_MEAN}': f"{summary['pm25_mean']:.2f}",
    '{PM_SD}': f"{summary['pm25_sd']:.2f}",
    '{PM_P05}': f"{summary['pm25_p05']:.2f}",
    '{PM_P50}': f"{summary['pm25_p50']:.2f}",
    '{PM_P95}': f"{summary['pm25_p95']:.2f}",
    '{Y_MEAN}': f"{summary['outcome_mean']:.2f}",
    '{Y_SD}': f"{summary['outcome_sd']:.2f}",
    '{Y_P05}': f"{summary['outcome_p05']:.2f}",
    '{Y_P50}': f"{summary['outcome_p50']:.2f}",
    '{Y_P95}': f"{summary['outcome_p95']:.2f}",
    # tolerate both raw placeholders and ones with inline percent formatting
    '{EX15}': f"{ex15:.3f}",
    '{EX25}': f"{ex25:.3f}",
    '{EX35}': f"{ex35:.3f}",
    '{EX15:.1%}': f"{ex15:.1%}",
    '{EX25:.1%}': f"{ex25:.1%}",
    '{EX35:.1%}': f"{ex35:.1%}",
    '{CLUSTER}': str(main.get('cluster', meta.get('schema', {}).get('panel_id_col') or 'date')),
    '{PHI}': f"{meta['main_overdispersion_phi']:.2f}",
    '{MAIN_EXPOSURE}': meta['main_exposure'],
    '{MAIN_PCT}': f"{main['pct_change_per10']:.2f}",
    '{MAIN_LCL}': f"{main['pct_change_lcl']:.2f}",
    '{MAIN_UCL}': f"{main['pct_change_ucl']:.2f}",
    '{MAIN_RR}': f"{main['rr_per10']:.3f}",
    '{MAIN_RR_LCL}': f"{main['rr_per10_lcl']:.3f}",
    '{MAIN_RR_UCL}': f"{main['rr_per10_ucl']:.3f}",
    '{NB_PCT}': f"{nb['pct_change_per10']:.2f}",
    '{NB_LCL}': f"{nb['pct_change_lcl']:.2f}",
    '{NB_UCL}': f"{nb['pct_change_ucl']:.2f}",
    '{POLICY_TABLE}': policy_table,
}

text = open(TEMPLATE_PATH, 'r', encoding='utf-8').read()
for k, v in repl.items():
    text = text.replace(k, v)

open('report/report.md', 'w', encoding='utf-8').write(text)
print('Rendered report/report.md')
