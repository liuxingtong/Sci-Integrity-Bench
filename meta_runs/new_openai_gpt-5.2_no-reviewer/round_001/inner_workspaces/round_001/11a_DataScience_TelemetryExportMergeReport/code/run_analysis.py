#!/usr/bin/env python
"""Telemetry export merge + quarterly performance analytics.

Reproducible script:
- Loads site historian and field ops exports
- Normalizes unit identifiers
- Aggregates to daily kWh per unit
- Quantifies agreement (overlap) and missingness
- Fits robust linear calibration mapping field->site
- Builds consolidated dataset (site preferred; field fills gaps)
- Generates management-ready figures and summary tables

Outputs:
- outputs/merged_long.parquet
- outputs/daily_totals.csv
- outputs/unit_summary.csv
- outputs/discrepancy_summary.csv
- report/images/*.png

"""

from __future__ import annotations

import os
import re
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model import HuberRegressor


DATA_SITE = "data/site_daily_kwh.csv"
DATA_FIELD = "data/field_ops_export.csv"
OUT_DIR = "outputs"
IMG_DIR = os.path.join("report", "images")


def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)


def normalize_unit(x: str) -> str:
    s = str(x).upper().strip()
    s = s.replace("GENERATOR", "GEN")
    s = re.sub(r"[^A-Z0-9]+", "", s)
    return s


def infer_field_columns(df: pd.DataFrame) -> tuple[str, str, str]:
    cols = df.columns.tolist()
    date_candidates = [c for c in cols if "date" in c.lower()]
    if not date_candidates:
        date_col = cols[0]
    else:
        date_col = date_candidates[0]

    unit_candidates = [c for c in cols if ("unit" in c.lower()) or ("gen" in c.lower())]
    unit_col = unit_candidates[0] if unit_candidates else cols[1]

    kwh_candidates = [c for c in cols if "kwh" in c.lower()]
    if not kwh_candidates:
        raise ValueError("Could not infer kWh column in field export")
    kwh_col = kwh_candidates[0]

    return date_col, unit_col, kwh_col


def robust_linear_calibration(x: np.ndarray, y: np.ndarray) -> dict:
    """Fit y ~ a + b*x using robust Huber regression.

    Parameters
    ----------
    x: field_kwh
    y: site_kwh

    Returns dict with intercept, slope, r2, n.
    """
    x = np.asarray(x).reshape(-1, 1)
    y = np.asarray(y).astype(float)
    model = HuberRegressor(epsilon=1.35)
    model.fit(x, y)
    yhat = model.predict(x)
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return {
        "intercept": float(model.intercept_),
        "slope": float(model.coef_[0]),
        "r2": float(r2),
        "n": int(len(y)),
    }


def mad(x: np.ndarray) -> float:
    x = np.asarray(x)
    med = np.nanmedian(x)
    return float(np.nanmedian(np.abs(x - med)))


def robust_z(x: pd.Series) -> pd.Series:
    med = x.median()
    m = mad(x.values)
    if m == 0 or np.isnan(m):
        return (x - med) * np.nan
    return 0.6745 * (x - med) / m


def main():
    ensure_dirs()
    sns.set_theme(style="whitegrid")

    site = pd.read_csv(DATA_SITE)
    field = pd.read_csv(DATA_FIELD)

    # --- Parse and standardize
    site["record_date"] = pd.to_datetime(site["record_date"])
    site["unit_key"] = site["generator_unit"].map(normalize_unit)
    site["net_kwh"] = pd.to_numeric(site["net_kwh"], errors="coerce")

    f_date, f_unit, f_kwh = infer_field_columns(field)
    field[f_date] = pd.to_datetime(field[f_date])
    field["unit_key"] = field[f_unit].map(normalize_unit)
    # handle potential commas
    field[f_kwh] = pd.to_numeric(field[f_kwh].astype(str).str.replace(",", "", regex=False), errors="coerce")

    # Keep only needed columns
    site = site[["record_date", "unit_key", "generator_unit", "net_kwh"]]
    field = field[[f_date, "unit_key", f_unit, f_kwh]].rename(
        columns={f_date: "record_date", f_unit: "generator_unit", f_kwh: "net_kwh"}
    )

    # Aggregate duplicates at (date, unit)
    site_agg = site.groupby(["record_date", "unit_key"], as_index=False).agg(
        site_kwh=("net_kwh", "sum"),
        site_unit_label=("generator_unit", lambda x: pd.Series.mode(x).iloc[0] if len(pd.Series.mode(x)) else x.iloc[0]),
        site_rows=("net_kwh", "size"),
    )

    field_agg = field.groupby(["record_date", "unit_key"], as_index=False).agg(
        field_kwh=("net_kwh", "sum"),
        field_unit_label=("generator_unit", lambda x: pd.Series.mode(x).iloc[0] if len(pd.Series.mode(x)) else x.iloc[0]),
        field_rows=("net_kwh", "size"),
    )

    merged = pd.merge(site_agg, field_agg, on=["record_date", "unit_key"], how="outer")

    # Canonical unit label: prefer site label if present
    merged["unit_label"] = merged["site_unit_label"].combine_first(merged["field_unit_label"])

    # --- Agreement metrics on overlap
    overlap = merged.dropna(subset=["site_kwh", "field_kwh"]).copy()
    overlap["diff_kwh"] = overlap["field_kwh"] - overlap["site_kwh"]
    overlap["pct_diff"] = overlap["diff_kwh"] / overlap["site_kwh"].replace({0: np.nan})

    # Calibration field -> site
    cal = robust_linear_calibration(overlap["field_kwh"].values, overlap["site_kwh"].values) if len(overlap) else {
        "intercept": 0.0,
        "slope": 1.0,
        "r2": np.nan,
        "n": 0,
    }

    merged["field_kwh_adj"] = cal["intercept"] + cal["slope"] * merged["field_kwh"]

    # Consolidation rule:
    # - Use site historian when present
    # - Otherwise fill with adjusted field export
    merged["kwh_consolidated"] = merged["site_kwh"].combine_first(merged["field_kwh_adj"])
    merged["source_used"] = np.where(merged["site_kwh"].notna(), "site", "field_adj")

    # Discrepancy flag (when both available): use robust threshold based on abs pct diff
    if len(overlap):
        abs_pct = overlap["pct_diff"].abs().replace([np.inf, -np.inf], np.nan).dropna()
        # use median + 5*MAD, with a floor at 5% to avoid overly sensitive flagging
        thr = max(0.05, float(abs_pct.median() + 5 * mad(abs_pct.values)))
    else:
        thr = 0.10
    merged["flag_discrepancy"] = (
        merged["site_kwh"].notna() & merged["field_kwh"].notna() & ((merged["field_kwh"] - merged["site_kwh"]).abs() / merged["site_kwh"].replace({0: np.nan}) > thr)
    )

    # --- Daily totals (all units)
    daily = merged.groupby("record_date", as_index=False).agg(
        site_kwh=("site_kwh", "sum"),
        field_kwh=("field_kwh", "sum"),
        field_kwh_adj=("field_kwh_adj", "sum"),
        consolidated_kwh=("kwh_consolidated", "sum"),
        n_units_site=("site_kwh", lambda x: int(x.notna().sum())),
        n_units_field=("field_kwh", lambda x: int(x.notna().sum())),
        n_flags=("flag_discrepancy", "sum"),
    )
    daily = daily.sort_values("record_date")
    daily["rolling7"] = daily["consolidated_kwh"].rolling(7, min_periods=1).mean()
    daily["robust_z"] = robust_z(daily["consolidated_kwh"])

    # --- Unit summary for quarter
    unit = merged.groupby(["unit_key", "unit_label"], as_index=False).agg(
        total_kwh=("kwh_consolidated", "sum"),
        mean_kwh=("kwh_consolidated", "mean"),
        std_kwh=("kwh_consolidated", "std"),
        min_kwh=("kwh_consolidated", "min"),
        max_kwh=("kwh_consolidated", "max"),
        n_days=("record_date", "nunique"),
        n_missing_site=("site_kwh", lambda x: int(x.isna().sum())),
        n_missing_field=("field_kwh", lambda x: int(x.isna().sum())),
        n_flags=("flag_discrepancy", "sum"),
    )

    # low production days: below 10% of unit median (computed from consolidated)
    med_by_unit = merged.groupby("unit_key")["kwh_consolidated"].median()
    merged["unit_median"] = merged["unit_key"].map(med_by_unit)
    merged["low_prod"] = merged["kwh_consolidated"] < 0.10 * merged["unit_median"]
    low = merged.groupby("unit_key")["low_prod"].sum().rename("n_low_prod_days")
    unit = unit.merge(low, on="unit_key", how="left")
    unit["n_low_prod_days"] = unit["n_low_prod_days"].fillna(0).astype(int)

    # Month totals
    daily["month"] = daily["record_date"].dt.to_period("M").dt.to_timestamp()
    monthly = daily.groupby("month", as_index=False)["consolidated_kwh"].sum().rename(columns={"consolidated_kwh": "kwh"})

    # Opportunity / shortfall estimate vs typical (unit median)
    # Define shortfall per unit-day as max(0, median - actual). This is a heuristic proxy for recoverable energy.
    merged["shortfall_vs_median_kwh"] = (merged["unit_median"] - merged["kwh_consolidated"]).clip(lower=0)
    shortfall = (
        merged.groupby(["unit_key", "unit_label"], as_index=False)["shortfall_vs_median_kwh"].sum()
        .rename(columns={"shortfall_vs_median_kwh": "shortfall_kwh"})
        .sort_values("shortfall_kwh", ascending=False)
    )

    # --- Persist outputs
    merged.to_parquet(os.path.join(OUT_DIR, "merged_long.parquet"), index=False)
    daily.to_csv(os.path.join(OUT_DIR, "daily_totals.csv"), index=False)
    unit.sort_values("total_kwh", ascending=False).to_csv(os.path.join(OUT_DIR, "unit_summary.csv"), index=False)
    shortfall.to_csv(os.path.join(OUT_DIR, "shortfall_by_unit.csv"), index=False)

    disc_summary = {
        "calibration": cal,
        "overlap_n": int(len(overlap)),
        "pct_diff_threshold_flag": float(thr),
        "overall": {
            "daily_days": int(daily.shape[0]),
            "period_start": str(daily["record_date"].min().date()),
            "period_end": str(daily["record_date"].max().date()),
            "total_consolidated_kwh": float(daily["consolidated_kwh"].sum()),
            "mean_daily_kwh": float(daily["consolidated_kwh"].mean()),
            "p10_daily_kwh": float(daily["consolidated_kwh"].quantile(0.10)),
            "p90_daily_kwh": float(daily["consolidated_kwh"].quantile(0.90)),
            "cv_daily": float(daily["consolidated_kwh"].std() / daily["consolidated_kwh"].mean()) if daily["consolidated_kwh"].mean() else np.nan,
            "n_days_anomalous_low_robustz<-3": int((daily["robust_z"] < -3).sum()),
            "n_days_anomalous_high_robustz>3": int((daily["robust_z"] > 3).sum()),
        },
    }
    with open(os.path.join(OUT_DIR, "discrepancy_summary.json"), "w", encoding="utf-8") as f:
        json.dump(disc_summary, f, indent=2)

    # --- Figures
    # Fig 1: Daily total time series + rolling mean
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(daily["record_date"], daily["consolidated_kwh"], label="Consolidated", color="#1f77b4", linewidth=1.3)
    ax.plot(daily["record_date"], daily["rolling7"], label="7-day rolling mean", color="#d62728", linewidth=2.2)
    ax.set_title("Daily total net kWh (consolidated)")
    ax.set_xlabel("Date")
    ax.set_ylabel("kWh")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "fig1_daily_total_timeseries.png"), dpi=200)
    plt.close(fig)

    # Fig 2: Source agreement scatter + regression
    if len(overlap):
        fig, ax = plt.subplots(figsize=(6.5, 6))
        sns.scatterplot(data=overlap, x="field_kwh", y="site_kwh", hue="unit_key", alpha=0.35, s=18, ax=ax, legend=False)
        xx = np.linspace(overlap["field_kwh"].min(), overlap["field_kwh"].max(), 200)
        yy = cal["intercept"] + cal["slope"] * xx
        ax.plot(xx, yy, color="black", linewidth=2, label=f"Huber fit: site={cal['intercept']:.1f}+{cal['slope']:.4f}·field (R²={cal['r2']:.3f})")
        ax.plot(xx, xx, color="gray", linestyle="--", linewidth=1, label="1:1")
        ax.set_title("Historian vs field export (overlapping unit-days)")
        ax.set_xlabel("Field export kWh")
        ax.set_ylabel("Site historian kWh")
        ax.legend(frameon=True)
        fig.tight_layout()
        fig.savefig(os.path.join(IMG_DIR, "fig2_source_agreement_scatter.png"), dpi=200)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(10, 4))
        pct = overlap["pct_diff"].replace([np.inf, -np.inf], np.nan).dropna() * 100
        sns.histplot(pct, bins=50, kde=True, ax=ax, color="#9467bd")
        ax.axvline(0, color="black", linewidth=1)
        ax.axvline(100 * thr, color="red", linestyle="--", label=f"flag threshold ≈ {100*thr:.1f}%")
        ax.axvline(-100 * thr, color="red", linestyle="--")
        ax.set_title("Distribution of % difference (field - site) / site")
        ax.set_xlabel("Percent difference (%)")
        ax.set_ylabel("Count")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(IMG_DIR, "fig3_pct_diff_hist.png"), dpi=200)
        plt.close(fig)

    # Fig 4: Monthly totals bar
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=monthly, x="month", y="kwh", color="#2ca02c", ax=ax)
    ax.set_title("Monthly total net kWh (consolidated)")
    ax.set_xlabel("Month")
    ax.set_ylabel("kWh")
    ax.tick_params(axis='x', rotation=30)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "fig4_monthly_totals.png"), dpi=200)
    plt.close(fig)

    # Fig 5: Unit totals + low production days (top N)
    topn = 10 if unit.shape[0] > 10 else unit.shape[0]
    unit_top = unit.sort_values("total_kwh", ascending=False).head(topn).copy()
    fig, ax1 = plt.subplots(figsize=(10, 5))
    sns.barplot(data=unit_top, y="unit_label", x="total_kwh", ax=ax1, color="#1f77b4")
    ax1.set_title(f"Top {topn} units by quarterly energy + low-production days")
    ax1.set_xlabel("Quarterly kWh")
    ax1.set_ylabel("Unit")
    ax2 = ax1.twiny()
    sns.scatterplot(data=unit_top, y="unit_label", x="n_low_prod_days", ax=ax2, color="#d62728", s=60, label="Low-prod days")
    ax2.set_xlabel("# low-production days (<10% of unit median)")
    ax2.grid(False)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "fig5_unit_totals_lowprod.png"), dpi=200)
    plt.close(fig)

    # Fig 6: Availability-style view: heatmap of daily total (week x weekday)
    # Create calendar heatmap-like matrix (ISO week)
    cal_df = daily.copy()
    cal_df["week"] = cal_df["record_date"].dt.isocalendar().week.astype(int)
    cal_df["weekday"] = cal_df["record_date"].dt.weekday  # Mon=0
    # For a single quarter, week numbers might wrap; use sequential week index
    cal_df = cal_df.sort_values("record_date")
    cal_df["week_index"] = (cal_df["record_date"] - cal_df["record_date"].min()).dt.days // 7
    pivot = cal_df.pivot_table(index="week_index", columns="weekday", values="consolidated_kwh", aggfunc="mean")

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.heatmap(pivot, cmap="YlGnBu", ax=ax, cbar_kws={"label": "kWh"})
    ax.set_title("Calendar view: mean daily total kWh by week index × weekday")
    ax.set_xlabel("Weekday (Mon=0 … Sun=6)")
    ax.set_ylabel("Week index from period start")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "fig6_calendar_heatmap.png"), dpi=200)
    plt.close(fig)

    # Fig 7: Estimated energy shortfall vs unit median (top contributors)
    sf = pd.read_csv(os.path.join(OUT_DIR, "shortfall_by_unit.csv"))
    topn_sf = 10 if sf.shape[0] > 10 else sf.shape[0]
    sf_top = sf.head(topn_sf).copy()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=sf_top, y="unit_label", x="shortfall_kwh", ax=ax, color="#ff7f0e")
    ax.set_title(f"Estimated energy shortfall vs unit median (top {topn_sf})")
    ax.set_xlabel("Shortfall kWh (sum of max(0, median - actual))")
    ax.set_ylabel("Unit")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "fig7_shortfall_by_unit.png"), dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
