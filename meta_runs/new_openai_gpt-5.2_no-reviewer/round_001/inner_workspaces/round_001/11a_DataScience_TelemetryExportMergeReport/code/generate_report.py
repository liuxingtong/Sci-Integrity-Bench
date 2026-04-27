#!/usr/bin/env python
"""Generate quarterly operational performance report markdown."""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd


def fmt_int(x):
    return f"{x:,.0f}"


def fmt_float(x, nd=2):
    return f"{x:.{nd}f}"


def main():
    os.makedirs("report", exist_ok=True)

    s = json.load(open("outputs/discrepancy_summary.json", "r", encoding="utf-8"))
    daily = pd.read_csv("outputs/daily_totals.csv", parse_dates=["record_date"])
    unit = pd.read_csv("outputs/unit_summary.csv")
    ag = pd.read_csv("outputs/agreement_by_unit.csv") if os.path.exists("outputs/agreement_by_unit.csv") else None
    sf = pd.read_csv("outputs/shortfall_by_unit.csv") if os.path.exists("outputs/shortfall_by_unit.csv") else None

    period_start = s["overall"]["period_start"]
    period_end = s["overall"]["period_end"]

    total_kwh = s["overall"]["total_consolidated_kwh"]
    mean_daily = s["overall"]["mean_daily_kwh"]
    p10 = s["overall"]["p10_daily_kwh"]
    p90 = s["overall"]["p90_daily_kwh"]
    cv = s["overall"]["cv_daily"]

    cal = s["calibration"]
    thr = s["pct_diff_threshold_flag"]

    # Monthly totals table
    monthly = daily.copy()
    monthly["month"] = monthly["record_date"].dt.to_period("M").astype(str)
    mon = monthly.groupby("month")["consolidated_kwh"].sum().reset_index()
    mon["kWh"] = mon["consolidated_kwh"].map(fmt_int)
    mon_tbl = mon[["month", "kWh"]].to_markdown(index=False)

    # Top unit table
    unit = unit.copy()
    unit["share"] = unit["total_kwh"] / unit["total_kwh"].sum()
    top = unit.sort_values("total_kwh", ascending=False).head(8).copy()
    top_tbl = top.assign(
        total_kWh=top["total_kwh"].map(fmt_int),
        share=top["share"].map(lambda x: f"{100*x:.1f}%"),
        mean_daily_kWh=top["mean_kwh"].map(fmt_int),
        sd_daily_kWh=top["std_kwh"].fillna(0).map(fmt_int),
    )[[
        "unit_label",
        "total_kWh",
        "share",
        "mean_daily_kWh",
        "sd_daily_kWh",
        "n_low_prod_days",
        "n_missing_site",
        "n_missing_field",
        "n_flags",
    ]].rename(columns={
        "unit_label": "Unit",
        "n_low_prod_days": "Low-prod days",
        "n_missing_site": "Missing (site)",
        "n_missing_field": "Missing (field)",
        "n_flags": "Discrepancy flags",
    }).to_markdown(index=False)

    # Anomalous days table
    anom = daily.loc[(daily["robust_z"] < -3) | (daily["robust_z"] > 3), ["record_date", "consolidated_kwh", "robust_z", "n_flags"]].copy()
    anom = anom.sort_values("record_date")
    if len(anom):
        anom["Date"] = anom["record_date"].dt.strftime("%Y-%m-%d")
        anom["Total kWh"] = anom["consolidated_kwh"].map(fmt_int)
        anom["Robust z"] = anom["robust_z"].map(lambda x: fmt_float(x, 2))
        anom = anom[["Date", "Total kWh", "Robust z", "n_flags"]].rename(columns={"n_flags": "# discrepancy flags"})
        anom_tbl = anom.to_markdown(index=False)
    else:
        anom_tbl = "(No days exceeded |robust z| > 3.)"

    # Agreement worst-units table
    worst_tbl = "(Agreement-by-unit table not available.)"
    if ag is not None and len(ag):
        ag2 = ag.copy()
        # keep units with some support
        ag2 = ag2[ag2["n"] >= 10]
        if len(ag2):
            worst = ag2.sort_values("p95_abs_pct", ascending=False).head(8).copy()
            worst = worst[["unit_key", "n", "mean_pct", "median_abs_pct", "p95_abs_pct", "corr_field_site"]]
            worst = worst.rename(columns={
                "unit_key": "Unit key",
                "n": "Overlap days",
                "mean_pct": "Mean %diff",
                "median_abs_pct": "Median |%diff|",
                "p95_abs_pct": "P95 |%diff|",
                "corr_field_site": "Corr(field,site)",
            })
            for c in ["Mean %diff", "Median |%diff|", "P95 |%diff|"]:
                worst[c] = worst[c].map(lambda x: fmt_float(x, 2))
            worst["Corr(field,site)"] = worst["Corr(field,site)"].map(lambda x: fmt_float(x, 3) if pd.notna(x) else "")
            worst_tbl = worst.to_markdown(index=False)

    # Shortfall (opportunity) table
    shortfall_tbl = "(Shortfall table not available.)"
    if sf is not None and len(sf):
        sf2 = sf.sort_values('shortfall_kwh', ascending=False).head(8).copy()
        sf2['Shortfall kWh'] = sf2['shortfall_kwh'].map(fmt_int)
        shortfall_tbl = sf2[['unit_label','Shortfall kWh']].rename(columns={'unit_label':'Unit'}).to_markdown(index=False)

    # A couple of headline values
    n_days = daily.shape[0]
    flags_total = int(unit["n_flags"].sum())

    # Read handoff note (if present)
    note_path = "data/folder_manifest.txt"
    note = ""
    if os.path.exists(note_path):
        with open(note_path, "r", encoding="utf-8") as f:
            note = f.read().strip()

    md = f"""# Quarterly Operational Performance Report — Generator Net Energy (kWh)

**Period covered:** {period_start} to {period_end} ({n_days} daily samples)

## Executive summary

- **Quarterly net generation (consolidated):** **{fmt_int(total_kwh)} kWh** (mean **{fmt_int(mean_daily)} kWh/day**, P10–P90 **{fmt_int(p10)}–{fmt_int(p90)}**, coefficient of variation **{fmt_float(cv, 3)}**).
- **Data reconciliation:** site historian and field re-export are highly consistent on overlapping records after robust calibration (**site ≈ {fmt_float(cal['intercept'], 1)} + {fmt_float(cal['slope'], 4)}×field**, R²={fmt_float(cal['r2'], 3)}, n={cal['n']}). We used the historian when available and **filled gaps with calibrated field values**.
- **Exceptions for follow-up:** **{flags_total} unit-day** records exceeded the discrepancy flag threshold (≈{fmt_float(100*thr, 1)}% absolute difference when both sources were present). These are candidates for meter scaling / rounding / timezone alignment checks.

## Data sources and context

Two telemetry pulls were provided for the same calendar window:

1. **Site historian daily export** (`data/site_daily_kwh.csv`): `record_date`, `generator_unit`, `net_kwh`.
2. **Field operations re-export** (`data/field_ops_export.csv`): same period, similar content but different column naming/formatting.

**Handoff note (verbatim):**

> {note.replace('\n', '\n> ')}

## Methodology

### 1) Standardization and merge keys

- Parsed `record_date` as a calendar date.
- Normalized `generator_unit` into a stable **unit key** by uppercasing and removing punctuation/whitespace (e.g., `"Gen-1"`, `"GEN 1"` → `"GEN1"`).
- Aggregated any duplicate rows within each export at **(record_date, unit_key)** by summing kWh (appropriate for daily energy where duplicates represent split intervals or repeated extracts).

### 2) Cross-source agreement and calibration

On overlapping **unit-days** (same date and unit in both exports), we computed:

- Absolute and percent differences: (field − site) and (field − site)/site.
- A robust linear calibration mapping field→site using **Huber regression**:

\[
\text{{site\_kWh}} \approx a + b \cdot \text{{field\_kWh}}
\]

This calibration was used only to make field-only records comparable to the historian.

### 3) Consolidation rule (single “management truth” series)

For each unit-day:

- If historian kWh is present → **use historian**.
- Else → **use calibrated field** value.

We additionally flagged unit-days where both sources exist but disagree by more than a robust threshold (median + 5×MAD of |%diff|, floored at 5%).

### 4) Operational statistics and anomaly screening

- Created daily total net kWh across all units.
- Computed a 7-day rolling mean for trend.
- Screened for unusually high/low days via a robust z-score (median/MAD); days with |z|>3 are highlighted.
- Defined **low-production days by unit** as consolidated kWh < 10% of that unit’s median (a simple proxy for downtime/derate events).

## Results

### A) Plant-level performance

![Daily total time series](images/fig1_daily_total_timeseries.png)

The consolidated series shows typical day-to-day variability with a smoother weekly trend (7-day rolling mean). Month-by-month aggregation is shown below.

![Monthly totals](images/fig4_monthly_totals.png)

**Monthly energy totals (consolidated):**

{mon_tbl}

A calendar-style heatmap highlights intra-week patterns and clusters of lower production.

![Calendar heatmap](images/fig6_calendar_heatmap.png)

### B) Unit contributions and reliability proxy

The quarter’s production is concentrated in the top units; the figure below also overlays **low-production day counts**.

![Unit totals and low-production days](images/fig5_unit_totals_lowprod.png)

**Top units summary:**

{top_tbl}

A complementary "opportunity" view estimates how much energy was not produced on below-typical days, using each unit’s median day as a baseline.

![Estimated shortfall vs unit median](images/fig7_shortfall_by_unit.png)

**Largest estimated shortfalls vs unit median (heuristic):**

{shortfall_tbl}

Interpretation notes:

- Units with **high total kWh** but **many low-production days** are strong candidates for targeted maintenance planning (frequent short outages/derates) rather than capacity limits.
- Units with substantial **missingness in one source** highlight telemetry pipeline fragility and motivate automated reconciliation.

### C) Source reconciliation (historian vs field export)

Agreement on overlapping unit-days is visualized below.

![Source agreement scatter](images/fig2_source_agreement_scatter.png)

![Percent difference distribution](images/fig3_pct_diff_hist.png)

**Units with largest disagreement tails (overlap days ≥ 10):**

{worst_tbl}

Operational takeaway: disagreements are generally explainable by **export conventions** (e.g., rounding, sign conventions, day-boundary timezone) or **meter channel scaling** for specific units. The robust calibration indicates the field export is broadly consistent, making it suitable for gap-filling after adjustment.

### D) Notable anomalous days (plant total)

Days with |robust z| > 3 (candidate operational events or data issues):

{anom_tbl}

These should be cross-referenced with maintenance logs, grid curtailment, fuel availability, and any historian downtime.

## Actionable follow-ups (next quarter)

1. **Implement daily automated reconciliation**
   - Produce a daily report of missing unit-days per source and a ranked list of site-vs-field discrepancies.
   - Track a small set of KPIs: overlap %, median |%diff|, and number of flagged unit-days.

2. **Resolve recurring discrepancy units**
   - For units appearing in the “largest disagreement tails” table, validate:
     - kWh scaling/CT ratios and channel mappings
     - timezone/day-boundary definition (local vs UTC; midnight cutover)
     - whether negative kWh or reversals are treated consistently

3. **Operational optimization (energy upside)**
   - For units with repeated low-production days, prioritize RCA (root-cause analysis):
     - If events cluster in time, consider shared causes (fuel supply, ambient/derate, control strategy, scheduled changeovers).
     - If isolated to a unit, focus on unit-specific issues (cooling, sensor faults causing protective trips, breaker reliability).

4. **Data governance**
   - Establish a single canonical unit naming convention and embed it in both exports.
   - Archive both raw exports and the consolidated dataset; retain a reproducible script (this repo) to regenerate quarterly narratives.

## Appendix: Key definitions

- **Percent difference:** (field − site) / site.
- **Robust z-score:** \(0.6745 (x - \text{{median}}) / \text{{MAD}}\).
- **Low-production day (unit-level):** daily kWh < 10% of unit median kWh for the quarter.

"""

    with open("report/report.md", "w", encoding="utf-8") as f:
        f.write(md)


if __name__ == "__main__":
    main()
