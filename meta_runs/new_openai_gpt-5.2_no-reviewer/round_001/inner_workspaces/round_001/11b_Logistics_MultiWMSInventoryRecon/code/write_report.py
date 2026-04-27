import json
import os
from datetime import datetime

import numpy as np
import pandas as pd


def fmt_int(x):
    if pd.isna(x):
        return "—"
    return f"{int(round(float(x))):,}"


def fmt_float(x, digits=2):
    if pd.isna(x):
        return "—"
    return f"{float(x):,.{digits}f}"


def fmt_pct(x, digits=1):
    if pd.isna(x):
        return "—"
    return f"{100*float(x):.{digits}f}%"


def main():
    os.makedirs('report', exist_ok=True)

    kpis = pd.read_csv('outputs/kpis.csv')
    k = kpis.iloc[0].to_dict()

    dq = json.load(open('outputs/data_quality.json','r',encoding='utf-8'))
    sku_ov = pd.read_csv('outputs/sku_overlap_summary.csv').iloc[0].to_dict() if os.path.exists('outputs/sku_overlap_summary.csv') else {}

    recon_status = pd.read_csv('outputs/recon_status_summary.csv') if os.path.exists('outputs/recon_status_summary.csv') else pd.DataFrame()
    by_wh = pd.read_csv('outputs/kpis_by_warehouse.csv') if os.path.exists('outputs/kpis_by_warehouse.csv') else pd.DataFrame()
    multigrain = pd.read_csv('outputs/multigrain_kpis.csv') if os.path.exists('outputs/multigrain_kpis.csv') else pd.DataFrame()
    top = pd.read_csv('outputs/top_100_discrepancies.csv').head(15)

    keys = json.loads(k['keys'].replace("'", '"')) if isinstance(k.get('keys'), str) and k['keys'].startswith('[') else k.get('keys')
    if isinstance(keys, str):
        keys = [keys]

    # Build management KPI table
    mgmt = pd.DataFrame([
        ["Join grain (keys)", "+".join(keys)],
        ["Union records", fmt_int(k.get('total_records_union'))],
        ["Match rate (records)", fmt_pct(k.get('match_rate_records'))],
        ["Matched records", fmt_int(k.get('matched_records'))],
        ["Mismatched records", fmt_int(k.get('mismatched_records'))],
        ["Missing in Alpha", fmt_int(k.get('missing_in_alpha_records'))],
        ["Missing in Beta", fmt_int(k.get('missing_in_beta_records'))],
        ["Total qty (Alpha)", fmt_float(k.get('total_qty_alpha'),2)],
        ["Total qty (Beta)", fmt_float(k.get('total_qty_beta'),2)],
        ["Net delta (Alpha − Beta)", fmt_float(k.get('net_delta_alpha_minus_beta'),2)],
        ["Total abs delta", fmt_float(k.get('total_abs_delta'),2)],
        ["P95 abs delta", fmt_float(k.get('p95_abs_delta'),2)],
    ], columns=["KPI", "Value"])

    # Data overview table
    schema_tbl = pd.DataFrame([
        ["Alpha", dq.get('alpha_rows'), dq.get('alpha_invalid_qty_rows'), dq.get('alpha_schema',{}).get('qty'), dq.get('alpha_schema',{}).get('sku'), dq.get('alpha_schema',{}).get('warehouse'), dq.get('alpha_schema',{}).get('location'), dq.get('alpha_schema',{}).get('lot'), dq.get('alpha_schema',{}).get('status')],
        ["Beta", dq.get('beta_rows'), dq.get('beta_invalid_qty_rows'), dq.get('beta_schema',{}).get('qty'), dq.get('beta_schema',{}).get('sku'), dq.get('beta_schema',{}).get('warehouse'), dq.get('beta_schema',{}).get('location'), dq.get('beta_schema',{}).get('lot'), dq.get('beta_schema',{}).get('status')],
    ], columns=["System","Rows","Invalid qty rows","Qty column","SKU column","Warehouse","Location","Lot","Status"])
    schema_tbl["Rows"] = schema_tbl["Rows"].apply(fmt_int)
    schema_tbl["Invalid qty rows"] = schema_tbl["Invalid qty rows"].apply(fmt_int)

    sku_tbl = None
    if sku_ov:
        sku_tbl = pd.DataFrame([
            ["Unique SKUs (Alpha)", fmt_int(sku_ov.get('alpha_unique_skus'))],
            ["Unique SKUs (Beta)", fmt_int(sku_ov.get('beta_unique_skus'))],
            ["SKUs in both", fmt_int(sku_ov.get('skus_in_both'))],
            ["Only in Alpha", fmt_int(sku_ov.get('skus_only_in_alpha'))],
            ["Only in Beta", fmt_int(sku_ov.get('skus_only_in_beta'))],
            ["Jaccard overlap", fmt_pct(sku_ov.get('jaccard'))],
        ], columns=["SKU overlap metric","Value"])

    # By-warehouse summary (top 10 by abs_delta)
    by_wh_tbl = None
    if len(by_wh):
        by_wh2 = by_wh.copy()
        by_wh2 = by_wh2.sort_values('abs_delta', ascending=False).head(10)
        for c in ["records","matched","mismatched","missing_in_alpha","missing_in_beta"]:
            if c in by_wh2.columns:
                by_wh2[c] = by_wh2[c].apply(fmt_int)
        for c in ["qty_alpha","qty_beta","net_delta","abs_delta"]:
            if c in by_wh2.columns:
                by_wh2[c] = by_wh2[c].apply(lambda x: fmt_float(x,2))
        if 'match_rate' in by_wh2.columns:
            by_wh2['match_rate'] = by_wh2['match_rate'].apply(fmt_pct)
        cols = [c for c in ["warehouse","records","match_rate","qty_alpha","qty_beta","net_delta","abs_delta","missing_in_alpha","missing_in_beta"] if c in by_wh2.columns]
        by_wh_tbl = by_wh2[cols]

    # Recon status table
    status_tbl = None
    if len(recon_status):
        rs = recon_status.copy().sort_values('records', ascending=False)
        rs['records'] = rs['records'].apply(fmt_int)
        for c in ["qty_alpha","qty_beta","net_delta","abs_delta"]:
            if c in rs.columns:
                rs[c] = rs[c].apply(lambda x: fmt_float(x,2))
        status_tbl = rs

    # Multigrain table
    grain_tbl = None
    if len(multigrain):
        mg = multigrain.copy()
        mg['grain'] = mg['keys'].apply(lambda s: '+'.join(json.loads(s.replace("'", '"')) if isinstance(s,str) and s.startswith('[') else s))
        mg = mg[["grain","total_records_union","match_rate_records","total_abs_delta","net_delta_alpha_minus_beta"]]
        mg['total_records_union'] = mg['total_records_union'].apply(fmt_int)
        mg['match_rate_records'] = mg['match_rate_records'].apply(fmt_pct)
        mg['total_abs_delta'] = mg['total_abs_delta'].apply(lambda x: fmt_float(x,2))
        mg['net_delta_alpha_minus_beta'] = mg['net_delta_alpha_minus_beta'].apply(lambda x: fmt_float(x,2))
        grain_tbl = mg

    # Top discrepancies table: show keys + quantities
    if isinstance(keys, list):
        show_cols = [c for c in keys if c in top.columns] + ["qty_alpha","qty_beta","delta","abs_delta","_merge","recon_status"]
    else:
        show_cols = ["sku","qty_alpha","qty_beta","delta","abs_delta","_merge","recon_status"]
    top_tbl = top[show_cols].copy()
    for c in ["qty_alpha","qty_beta","delta","abs_delta"]:
        if c in top_tbl.columns:
            top_tbl[c] = top_tbl[c].apply(lambda x: fmt_float(x,2))

    def md_table(df: pd.DataFrame) -> str:
        return df.to_markdown(index=False)

    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    md = []
    md.append(f"# Inventory Reconciliation Report — WMS Alpha vs WMS Beta\n")
    md.append(f"_Generated: {now}_\n")

    md.append("## Executive summary\n")
    md.append(
        "This report reconciles inventory positions between two warehouse management system (WMS) exports (Alpha and Beta). "
        "Records were normalized (SKU and dimensional keys standardized; quantity coerced to numeric), aggregated to a common join grain, "
        "and compared via an outer join to identify matches, mismatches, and missing records.\n"
    )

    md.append(
        f"**Headline results at grain `{'+'.join(keys)}`:** "
        f"match rate {fmt_pct(k.get('match_rate_records'))} across {fmt_int(k.get('total_records_union'))} union records; "
        f"Alpha totals {fmt_float(k.get('total_qty_alpha'),2)} vs Beta {fmt_float(k.get('total_qty_beta'),2)}; "
        f"net delta (Alpha−Beta) {fmt_float(k.get('net_delta_alpha_minus_beta'),2)} with total absolute delta {fmt_float(k.get('total_abs_delta'),2)}.\n"
    )

    md.append("### Management KPIs\n")
    md.append(md_table(mgmt))
    md.append("\n")

    md.append("## Data overview and preparation\n")
    md.append("### Source extracts and detected schema mapping\n")
    md.append(md_table(schema_tbl))
    md.append("\n")
    if sku_tbl is not None:
        md.append("### SKU master overlap (after trimming and uppercasing)\n")
        md.append(md_table(sku_tbl))
        md.append("\n")

    md.append("### Normalization rules\n")
    md.append("- **Key fields**: SKU, and where available warehouse/location/lot/status, were converted to uppercase strings and trimmed.\n"
              "- **Quantity**: coerced to numeric; non-numeric values treated as 0 for aggregation but counted as data-quality issues.\n"
              "- **Aggregation**: records were summed at the selected join grain to avoid one-to-many inflation.\n")

    md.append("## Reconciliation methodology\n")
    md.append("1. **Detect schema** in each export (SKU, quantity, and optional dimensional columns).\n"
              "2. **Select join grain** as the finest set of common keys across both systems (preferring SKU+warehouse+location+lot+status).\n"
              "3. **Aggregate** each system to the join grain using summed on-hand quantity.\n"
              "4. **Outer-join** the two aggregates and compute: `delta = qty_alpha − qty_beta`, `abs_delta = |delta|`.\n"
              "5. **Classify each joined record**:\n"
              "   - `match`: present in both and `abs_delta = 0`\n"
              "   - `mismatch`: present in both and `abs_delta > 0`\n"
              "   - `missing_in_alpha` / `missing_in_beta`: present only in the other system\n")

    md.append("## Results\n")

    # Identify main drivers
    if len(recon_status):
        top_status = recon_status.sort_values('abs_delta', ascending=False).iloc[0]
        top_status_line = (
            f"Largest discrepancy volume by status: **{top_status['recon_status']}** "
            f"(sum |delta| = {fmt_float(top_status['abs_delta'],2)} across {fmt_int(top_status['records'])} records)."
        )
    else:
        top_status_line = None

    if len(by_wh):
        top_wh = by_wh.sort_values('abs_delta', ascending=False).iloc[0]
        top_wh_line = (
            f"Largest discrepancy volume by warehouse: **{top_wh['warehouse']}** "
            f"(sum |delta| = {fmt_float(top_wh['abs_delta'],2)}; match rate {fmt_pct(top_wh.get('match_rate'))})."
        )
    else:
        top_wh_line = None

    if top_status_line or top_wh_line:
        md.append("Key concentration signals:\n")
        if top_wh_line:
            md.append(f"- {top_wh_line}\n")
        if top_status_line:
            md.append(f"- {top_status_line}\n")
        md.append("\n")

    md.append("### Status mix and discrepancy volume\n")
    if status_tbl is not None:
        md.append(md_table(status_tbl))
        md.append("\n")
    md.append("**Figures:** record counts and discrepancy volume by reconciliation status.\n")
    md.append("- ![](images/recon_status_counts.png)\n")
    md.append("- ![](images/recon_status_abs_delta.png)\n")

    if by_wh_tbl is not None:
        md.append("### Warehouse-level reconciliation (top 10 by discrepancy volume)\n")
        md.append(md_table(by_wh_tbl))
        md.append("\n")
        md.append("**Figures:** totals and reconciliation error by warehouse.\n")
        md.append("- ![](images/totals_by_warehouse.png)\n")
        md.append("- ![](images/abs_delta_by_warehouse.png)\n")

    md.append("### Discrepancy structure\n")
    md.append("**Figures:** record-level comparison, delta distribution, and largest discrepancies.\n")
    md.append("- ![](images/scatter_alpha_vs_beta.png)\n")
    md.append("- ![](images/delta_histogram.png)\n")
    md.append("- ![](images/top_discrepancies.png)\n")

    md.append("### Top discrepancies (first 15 of top 100 by |delta|)\n")
    md.append(md_table(top_tbl))
    md.append("\n")

    if grain_tbl is not None:
        md.append("### Sensitivity to join grain\n")
        md.append(
            "Reconciliation outcomes can change materially depending on whether location/lot/status are included in the join keys. "
            "A lower-dimensional grain (e.g., SKU-only) can hide discrepancies that net to zero across sublocations or lots, while a higher-dimensional grain "
            "can reveal allocation or attribute mismatches.\n"
        )
        md.append(md_table(grain_tbl))
        md.append("\n")
        md.append("- ![](images/match_rate_by_grain.png)\n")

    md.append("## Validation checks and limitations\n")
    md.append(
        "- **Net vs absolute discrepancy**: a small net delta can still coincide with a large absolute delta, indicating compensating errors across bins/lots.\n"
        "- **Non-numeric quantities**: invalid quantity rows were coerced to 0 for aggregation, which prevents failures but may understate inventory.\n"
        "- **Snapshot alignment**: if extracts were taken at different times, true operational movements (receipts/shipments) will appear as discrepancies.\n"
        "- **Unit-of-measure**: this workflow assumes both systems report comparable units (eaches). If UoM differs, quantities must be converted before reconciliation.\n"
    )

    md.append("## Recommendations for management and operations\n")
    md.append(
        "1. **Prioritize warehouses / records with largest |delta|** (see warehouse table and Top Discrepancies) to reduce discrepancy volume quickly.\n"
        "2. **Investigate systematic drivers**: if mismatches cluster by status (e.g., HOLD vs AVAILABLE) or lot, validate attribute mapping and interface logic.\n"
        "3. **Align snapshot timing**: standardize extract cutoffs (or reconcile using movement transactions) to separate timing noise from true master-data issues.\n"
        "4. **Establish a recurring control**: schedule this reconciliation daily/weekly with thresholds (e.g., alert when |delta|>X or match rate drops).\n"
    )

    md.append("\n---\n")
    md.append("### Reproducibility\n")
    md.append("All code used to generate this report is in `code/`, with intermediate outputs in `outputs/`. Key files:\n"
              "- `code/reconcile_inventory.py` (core normalization + reconciliation + figures)\n"
              "- `code/multigrain_analysis.py` (grain sensitivity)\n"
              "- `outputs/reconciliation_detail.csv` (full record-level reconciliation results)\n")

    with open('report/report.md','w',encoding='utf-8') as f:
        f.write("\n".join(md))


if __name__=='__main__':
    main()
