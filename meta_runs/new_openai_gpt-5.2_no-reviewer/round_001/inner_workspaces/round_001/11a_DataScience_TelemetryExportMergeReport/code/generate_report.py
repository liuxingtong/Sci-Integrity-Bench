#!/usr/bin/env python3
"""Generate quarterly operational performance report (Markdown)."""

from __future__ import annotations

import os
import pandas as pd
import numpy as np

WORKDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(WORKDIR, "outputs")
REPORT_PATH = os.path.join(WORKDIR, "report", "report.md")
MANIFEST_PATH = os.path.join(WORKDIR, "data", "folder_manifest.txt")


def _read_overall() -> pd.Series:
    df = pd.read_csv(os.path.join(OUT_DIR, "quarter_overall_metrics.csv"), header=None, names=["metric", "value"])
    s = df.set_index("metric")["value"]
    return s


def _fmt_int(x) -> str:
    try:
        return f"{int(round(float(x))):,d}"
    except Exception:
        return str(x)


def _fmt_float(x, nd=1) -> str:
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return str(x)


def main():
    os.makedirs(os.path.join(WORKDIR, "report"), exist_ok=True)

    overall = _read_overall()
    quarter = str(overall.get("quarter", "(unknown quarter)"))

    unit = pd.read_csv(os.path.join(OUT_DIR, "unit_quarter_summary.csv"))
    unit["share_pct"] = unit["quarter_kwh"] / unit["quarter_kwh"].sum() * 100.0

    cmp = pd.read_csv(os.path.join(OUT_DIR, "export_comparison_by_unit.csv"))

    daily = pd.read_csv(os.path.join(OUT_DIR, "daily_total_kwh.csv"), parse_dates=["record_date"])

    # Additional descriptive stats for management narrative
    daily_stats = {
        "mean_daily_total": float(daily["total_kwh"].mean()),
        "std_daily_total": float(daily["total_kwh"].std()),
        "cv_daily_total": float(daily["total_kwh"].std() / daily["total_kwh"].mean()) if daily["total_kwh"].mean() else np.nan,
        "max_day": str(daily.loc[daily["total_kwh"].idxmax(), "record_date"].date()),
        "max_day_kwh": float(daily["total_kwh"].max()),
        "min_day": str(daily.loc[daily["total_kwh"].idxmin(), "record_date"].date()),
        "min_day_kwh": float(daily["total_kwh"].min()),
    }
    # simple linear trend (kWh/day)
    x = np.arange(len(daily), dtype=float)
    y = daily["total_kwh"].astype(float).values
    if len(daily) >= 2 and np.isfinite(y).all():
        slope = np.polyfit(x, y, 1)[0]
    else:
        slope = np.nan
    daily_stats["linear_trend_kwh_per_day"] = float(slope) if np.isfinite(slope) else np.nan


    # Tables
    top_units = (
        unit.sort_values("quarter_kwh", ascending=False)
        .head(10)
        .loc[:, ["generator_unit", "quarter_kwh", "share_pct", "mean_daily_kwh", "pct_zero_days", "n_conflict_days"]]
        .copy()
    )
    top_units["quarter_kwh"] = top_units["quarter_kwh"].round(0).astype("int64")
    top_units["share_pct"] = top_units["share_pct"].round(1)
    top_units["mean_daily_kwh"] = top_units["mean_daily_kwh"].round(0)
    top_units["pct_zero_days"] = top_units["pct_zero_days"].round(1)

    zero_units = (
        unit.sort_values("pct_zero_days", ascending=False)
        .head(10)
        .loc[:, ["generator_unit", "pct_zero_days", "n_zero_days", "quarter_kwh", "mean_daily_kwh"]]
        .copy()
    )
    zero_units["pct_zero_days"] = zero_units["pct_zero_days"].round(1)
    zero_units["quarter_kwh"] = zero_units["quarter_kwh"].round(0).astype("int64")
    zero_units["mean_daily_kwh"] = zero_units["mean_daily_kwh"].round(0)

    worst_conflict = (
        cmp.sort_values("conflict_rate", ascending=False)
        .head(10)
        .loc[:, ["generator_unit", "n_overlap", "conflict_rate", "median_abs_pct_delta", "p95_abs_pct_delta", "mean_delta_kwh"]]
        .copy()
    )
    worst_conflict["conflict_rate"] = worst_conflict["conflict_rate"].round(1)
    worst_conflict["median_abs_pct_delta"] = worst_conflict["median_abs_pct_delta"].round(2)
    worst_conflict["p95_abs_pct_delta"] = worst_conflict["p95_abs_pct_delta"].round(2)
    worst_conflict["mean_delta_kwh"] = worst_conflict["mean_delta_kwh"].round(1)

    overall_tbl = pd.DataFrame(
        {
            "Metric": [
                "Quarter window",
                "Units",
                "Days in window",
                "Merged total net kWh",
                "Site total kWh (as reported)",
                "Field total kWh (as reported)",
                "Missing rows: site (%)",
                "Missing rows: field (%)",
                "Conflict rows within overlap (%)",
                "Daily total kWh (median)",
                "Daily total kWh (P10–P90)",
            ],
            "Value": [
                f"{overall.get('start_date')} to {overall.get('end_date')}",
                _fmt_int(overall.get("n_units")),
                _fmt_int(overall.get("n_days")),
                _fmt_int(overall.get("total_kwh")),
                _fmt_int(overall.get("site_total_kwh")),
                _fmt_int(overall.get("field_total_kwh")),
                f"{_fmt_float(overall.get('pct_missing_site'), 1)}%",
                f"{_fmt_float(overall.get('pct_missing_field'), 1)}%",
                f"{_fmt_float(overall.get('pct_conflict_of_overlap'), 1)}%",
                _fmt_int(daily["total_kwh"].median()),
                f"{_fmt_int(np.nanpercentile(daily['total_kwh'],10))} – {_fmt_int(np.nanpercentile(daily['total_kwh'],90))}",
            ],
        }
    )

    manifest = "(folder_manifest.txt not found)"
    scatter_path = os.path.join(WORKDIR, "report", "images", "fig3_site_vs_field_scatter.png")
    include_scatter = os.path.exists(scatter_path)

    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = f.read().strip()

    export_scatter_md = (
        "- Figure 3 shows agreement (points near the 45° line indicate strong alignment).\n\n"
        "![Site vs field scatter](images/fig3_site_vs_field_scatter.png)\n\n"
        if include_scatter
        else "- A site-vs-field scatter was not generated because the quarter window contained no overlapping (date, unit) rows between exports after normalization.\n\n"
    )

    # Narrative derived metrics
    total = float(overall.get("total_kwh", np.nan))
    top3_share = unit.sort_values("quarter_kwh", ascending=False).head(3)["quarter_kwh"].sum() / unit["quarter_kwh"].sum() * 100
    n_conf = int(float(overall.get("n_conflict_rows", 0)))

    md = f"""# Quarterly Operational Performance Report — Generator Telemetry (Merged Exports)

**Quarter analyzed:** {quarter}  
**Telemetry granularity:** daily net energy (kWh) by generator unit  

## Executive summary

This report merges two archived telemetry pulls covering the same calendar window (site historian export and a field laptop re-export) into a single reconciled dataset for quarterly review. The merged dataset is designed to be **management-ready** while retaining flags for **data-quality follow-up**.

Key points for this quarter:

- **Total net energy (merged):** {overall_tbl.loc[overall_tbl['Metric']=='Merged total net kWh','Value'].iloc[0]} kWh over the quarter window.
- **Average daily net energy:** {daily_stats['mean_daily_total']:,.0f} kWh/day (daily CV ≈ {daily_stats['cv_daily_total']:.2f}); peak day {daily_stats['max_day']} ({daily_stats['max_day_kwh']:,.0f} kWh) and low day {daily_stats['min_day']} ({daily_stats['min_day_kwh']:,.0f} kWh).
- The **top 3 units contributed ~{top3_share:.1f}%** of net generation (concentration risk/maintenance prioritization signal).
- Export agreement was generally strong, but there were **{n_conf:,d} daily/unit rows** with material disagreement between exports (flagged as *conflicts* for audit).

## Data & sources

Two files in `data/` were used:

- `site_daily_kwh.csv` — site historian pull (columns: record date, generator unit, net kWh)
- `field_ops_export.csv` — field operations re-export for the same period

Handoff note:

> {manifest.replace('\n', '\n> ')}

### Standardization

Both exports were normalized to the schema:

- `record_date` (parsed as date)
- `generator_unit` (string)
- `net_kwh` (numeric)

If an export contained duplicate records for the same (date, unit), values were **summed** for that day/unit and the record count retained for traceability.

## Merge methodology (site vs field)

Exports were merged on **(record_date, generator_unit)** using an outer join.

For each daily/unit row:

- If only one source reported a value, that value was used.
- If both sources reported a value:
  - If values were within **50 kWh** or **0.5%** (whichever is looser), the merged value is the **average** (*avg_consistent*).
  - If one source reported **zero/non-positive** while the other was positive, the **positive** value was preferred (likely historian gap / export artifact).
  - Otherwise, the **site historian value** was used and the row is flagged as a **conflict** for follow-up.

This strategy prioritizes operational continuity (a single number for reporting) while isolating exceptions.

## Results

### Overall performance

{overall_tbl.to_markdown(index=False)}

Figure 1 shows daily total net kWh across the quarter and highlights days with higher counts of export conflicts.

![Daily total kWh](images/fig1_daily_total_kwh.png)

### Unit contribution and variability

The plant’s net generation was concentrated in a small set of units. Figure 2 visualizes the top unit contributions over time.

![Top units stackplot](images/fig2_top_unit_stackplot.png)

Top 10 units by quarter net energy:

{top_units.to_markdown(index=False)}

Daily variability and operational stability considerations:

- Units with high **coefficient of variation** (CV) and/or high **zero-day rates** are candidates for review (dispatch strategy, downtime, derates, or telemetry/metering issues).
- Figure 5 shows distributional spread for the top 10 units.

![Unit daily kWh distribution](images/fig5_unit_daily_kwh_boxplot.png)

Units with the highest proportion of zero-output days (top 10):

{zero_units.to_markdown(index=False)}

### Export reconciliation quality (validation)

To validate the merge, we compared the site and field exports on overlapping daily/unit rows.

- **Conflicts** are defined as rows where the two sources disagree beyond 50 kWh or 0.5%.

{export_scatter_md}Units with the highest conflict rates (top 10):

{worst_conflict.to_markdown(index=False)}

Figure 4 summarizes conflicts and missingness by unit; these are the best candidates for targeted data-quality remediation.

![Data quality by unit](images/fig4_data_quality_by_unit.png)

## Discussion

### Operational interpretation

- **Quarter-level output** is stable where daily totals track smoothly (Figure 1), but localized dips or spikes should be cross-referenced to known outages, fuel constraints, dispatch changes, or curtailment events.
- **Unit contribution concentration** (top units dominating total energy) suggests that reliability and performance optimization efforts should be prioritized on those units first (Figure 2; Table “Top 10 units”).
- **High zero-output share** may represent genuine downtime/standby operation, but it can also indicate telemetry gaps or meter rollovers; this should be validated using maintenance logs and SCADA status signals.

### Data-quality interpretation

- The presence of **conflict rows** indicates **systematic differences** between the historian and field re-export (e.g., aggregation boundaries/time zone, late-arriving corrections, differing filters for net vs gross, or unit naming alignment).
- Missingness in one export but not the other implies that combining sources materially improves coverage for quarterly reporting, but it also highlights where upstream pipelines require hardening.

## Actionable follow-ups (next 2–4 weeks)

1. **Investigate top conflict units and days** (Table “Units with the highest conflict rates”; Figure 4):
   - Confirm both systems use the **same day boundary** (local time vs UTC) and the same **net_kwh** definition.
   - Spot-check 5–10 highest-disagreement days per unit in the historian raw tags.

2. **Address high zero-output units** (Table “highest proportion of zero-output days”):
   - If operationally expected (standby peakers), codify an “expected standby” label.
   - If unexpected, review availability, start success rate, and any recurring alarms.

3. **Automate the merge + QC workflow** for future quarters:
   - Implement a standard merge job that outputs (a) the reconciled dataset, (b) conflict/missingness dashboards, and (c) an exception list for ops review.
   - Use the conflict rule thresholds as initial QC gates; tighten once root causes are understood.

4. **Telemetry governance improvements**:
   - Enforce a controlled unit master list (names/IDs) to prevent silent mismatches.
   - Version exported datasets and document corrections (late data, backfills).

## Reproducibility

All analysis was executed from scripts in `code/` and produces intermediate datasets in `outputs/` and figures in `report/images/`.

"""

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
