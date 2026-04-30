#!/usr/bin/env python3
"""Telemetry export merge + quarterly ops analytics.

Reads:
- data/site_daily_kwh.csv (site historian)
- data/field_ops_export.csv (field re-export)
- data/folder_manifest.txt (handoff note)

Writes:
- outputs/*.csv
- report/images/*.png

Run:
  python code/telemetry_merge_analysis.py
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


WORKDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(WORKDIR, "data")
OUT_DIR = os.path.join(WORKDIR, "outputs")
IMG_DIR = os.path.join(WORKDIR, "report", "images")


def _find_col(cols: List[str], patterns: List[str]) -> str:
    cols_l = [c.lower().strip() for c in cols]
    for pat in patterns:
        rx = re.compile(pat)
        matches = [c for c, cl in zip(cols, cols_l) if rx.search(cl)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            # prefer the shortest / most standard-looking
            matches_sorted = sorted(matches, key=lambda x: (len(x), x))
            return matches_sorted[0]
    raise KeyError(f"Could not find column using patterns={patterns}. Available={cols}")


def load_telemetry(path: str, source: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

    date_col = _find_col(df.columns.tolist(), [r"record_date$", r"^date$", r"date"]) 
    unit_col = _find_col(df.columns.tolist(), [r"generator_unit$", r"unit$", r"generator", r"gen"]) 

    # pick a kwh column: prefer net_kwh if present
    kwh_candidates = [c for c in df.columns if re.search(r"kwh", c, flags=re.I)]
    if not kwh_candidates:
        raise KeyError(f"No kWh column found in {path}. Columns={df.columns.tolist()}")
    net_like = [c for c in kwh_candidates if re.search(r"net", c, flags=re.I)]
    kwh_col = net_like[0] if net_like else kwh_candidates[0]

    out = df[[date_col, unit_col, kwh_col]].copy()
    out = out.rename(columns={date_col: "record_date", unit_col: "generator_unit", kwh_col: "net_kwh"})
    out["source"] = source

    out["record_date"] = pd.to_datetime(out["record_date"], errors="coerce")
    out["generator_unit"] = out["generator_unit"].astype(str).str.strip()
    out["net_kwh"] = pd.to_numeric(out["net_kwh"], errors="coerce")

    out = out.dropna(subset=["record_date", "generator_unit"]).reset_index(drop=True)

    # daily exports should be unique per date/unit; if not, aggregate and record duplication severity
    dup = out.duplicated(subset=["record_date", "generator_unit"], keep=False)
    if dup.any():
        agg = (
            out.groupby(["record_date", "generator_unit", "source"], as_index=False)
            .agg(net_kwh=("net_kwh", "sum"), n_records=("net_kwh", "size"))
        )
        out = agg
    else:
        out["n_records"] = 1

    return out


def reconcile(site: pd.DataFrame, field: pd.DataFrame) -> pd.DataFrame:
    s = site.rename(columns={"net_kwh": "site_kwh", "n_records": "site_n"})
    f = field.rename(columns={"net_kwh": "field_kwh", "n_records": "field_n"})

    m = pd.merge(
        s[["record_date", "generator_unit", "site_kwh", "site_n"]],
        f[["record_date", "generator_unit", "field_kwh", "field_n"]],
        on=["record_date", "generator_unit"],
        how="outer",
        validate="one_to_one",
    )

    m["delta_kwh"] = m["field_kwh"] - m["site_kwh"]
    m["abs_delta_kwh"] = m["delta_kwh"].abs()

    denom = np.maximum(m[["site_kwh", "field_kwh"]].max(axis=1), 1.0)
    m["abs_pct_delta"] = (m["abs_delta_kwh"] / denom) * 100.0

    # consistency rule: effectively equal within 0.5% or <= 50 kWh
    m["consistent"] = (m["abs_delta_kwh"].fillna(0) <= 50) | (m["abs_pct_delta"].fillna(0) <= 0.5)

    # choose a reconciled value
    sel = []
    rec = []
    for _, r in m.iterrows():
        sk, fk = r.get("site_kwh"), r.get("field_kwh")
        if pd.isna(sk) and pd.isna(fk):
            sel.append("missing_both")
            rec.append(np.nan)
        elif pd.isna(sk):
            sel.append("field_only")
            rec.append(fk)
        elif pd.isna(fk):
            sel.append("site_only")
            rec.append(sk)
        else:
            # both present
            if (sk <= 0) and (fk > 0):
                sel.append("field_over_site_zero")
                rec.append(fk)
            elif (fk <= 0) and (sk > 0):
                sel.append("site_over_field_zero")
                rec.append(sk)
            elif r["consistent"]:
                sel.append("avg_consistent")
                rec.append(np.nanmean([sk, fk]))
            else:
                # prefer historian for traceability; flag as conflict for follow-up
                sel.append("site_preferred_conflict")
                rec.append(sk)

    m["selected_source"] = sel
    m["net_kwh"] = rec
    m["conflict_flag"] = (~m["consistent"]) & m["site_kwh"].notna() & m["field_kwh"].notna()

    return m


def quarter_label(dt: pd.Timestamp) -> str:
    q = (dt.month - 1) // 3 + 1
    return f"{dt.year}Q{q}"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    sns.set_theme(style="whitegrid")

    site = load_telemetry(os.path.join(DATA_DIR, "site_daily_kwh.csv"), source="site_historian")
    field = load_telemetry(os.path.join(DATA_DIR, "field_ops_export.csv"), source="field_ops")

    merged = reconcile(site, field)

    # Determine analysis window as intersection/union? We'll report union and focus on common quarter.
    min_date = merged["record_date"].min()
    max_date = merged["record_date"].max()
    merged["quarter"] = merged["record_date"].apply(quarter_label)

    # if multiple quarters, use the most frequent quarter as the "current quarter".
    q_mode = merged["quarter"].value_counts().idxmax()
    q_df = merged[merged["quarter"] == q_mode].copy()

    # coverage grid for the quarter
    days = pd.date_range(q_df["record_date"].min(), q_df["record_date"].max(), freq="D")
    units = sorted(q_df["generator_unit"].dropna().unique().tolist())
    full_index = pd.MultiIndex.from_product([days, units], names=["record_date", "generator_unit"])
    q_df = q_df.set_index(["record_date", "generator_unit"]).reindex(full_index).reset_index()

    # recompute derived columns after reindex
    q_df["delta_kwh"] = q_df["field_kwh"] - q_df["site_kwh"]
    q_df["abs_delta_kwh"] = q_df["delta_kwh"].abs()
    denom = np.maximum(q_df[["site_kwh", "field_kwh"]].max(axis=1), 1.0)
    q_df["abs_pct_delta"] = (q_df["abs_delta_kwh"] / denom) * 100.0
    q_df["consistent"] = (q_df["abs_delta_kwh"].fillna(0) <= 50) | (q_df["abs_pct_delta"].fillna(0) <= 0.5)
    q_df["conflict_flag"] = (~q_df["consistent"]) & q_df["site_kwh"].notna() & q_df["field_kwh"].notna()

    # Re-apply selection logic vectorized-ish by re-running reconcile on quarter subset (keeping NaNs)
    # Simpler: join back with selection from merged where available.
    sel_cols = merged[["record_date", "generator_unit", "net_kwh", "selected_source"]]
    q_df = q_df.merge(sel_cols, on=["record_date", "generator_unit"], how="left")
    # if we reindexed to include missing combos, fill net_kwh using rule: prefer site->field
    missing_net = q_df["net_kwh"].isna()
    q_df.loc[missing_net & q_df["site_kwh"].notna(), "net_kwh"] = q_df.loc[missing_net & q_df["site_kwh"].notna(), "site_kwh"]
    q_df.loc[missing_net & q_df["site_kwh"].isna() & q_df["field_kwh"].notna(), "net_kwh"] = q_df.loc[missing_net & q_df["site_kwh"].isna() & q_df["field_kwh"].notna(), "field_kwh"]
    q_df.loc[missing_net & q_df["net_kwh"].notna(), "selected_source"] = q_df.loc[missing_net & q_df["net_kwh"].notna(), "selected_source"].fillna("rule_fallback")

    # basic data quality checks
    q_df["negative_kwh"] = q_df["net_kwh"] < 0
    q_df["zero_kwh"] = q_df["net_kwh"].fillna(0) == 0

    # summaries
    daily_total = q_df.groupby("record_date", as_index=False).agg(
        total_kwh=("net_kwh", "sum"),
        n_units=("generator_unit", "nunique"),
        n_conflicts=("conflict_flag", "sum"),
        n_missing_site=("site_kwh", lambda s: s.isna().sum()),
        n_missing_field=("field_kwh", lambda s: s.isna().sum()),
    )
    daily_total["rolling7_kwh"] = daily_total["total_kwh"].rolling(7, min_periods=1).mean()

    unit_summary = q_df.groupby("generator_unit", as_index=False).agg(
        quarter_kwh=("net_kwh", "sum"),
        mean_daily_kwh=("net_kwh", "mean"),
        median_daily_kwh=("net_kwh", "median"),
        std_daily_kwh=("net_kwh", "std"),
        p10_daily_kwh=("net_kwh", lambda s: np.nanpercentile(s, 10)),
        p90_daily_kwh=("net_kwh", lambda s: np.nanpercentile(s, 90)),
        n_days=("net_kwh", "size"),
        n_zero_days=("zero_kwh", "sum"),
        n_negative_days=("negative_kwh", "sum"),
        n_conflict_days=("conflict_flag", "sum"),
        n_missing_site=("site_kwh", lambda s: s.isna().sum()),
        n_missing_field=("field_kwh", lambda s: s.isna().sum()),
    )
    unit_summary["cv_daily_kwh"] = unit_summary["std_daily_kwh"] / unit_summary["mean_daily_kwh"].replace({0: np.nan})
    unit_summary["pct_zero_days"] = unit_summary["n_zero_days"] / unit_summary["n_days"] * 100.0

    # export comparison on overlapping rows
    overlap = q_df[q_df["site_kwh"].notna() & q_df["field_kwh"].notna()].copy()
    export_cmp = overlap.groupby("generator_unit", as_index=False).agg(
        n_overlap=("site_kwh", "size"),
        mean_site_kwh=("site_kwh", "mean"),
        mean_field_kwh=("field_kwh", "mean"),
        mean_delta_kwh=("delta_kwh", "mean"),
        median_abs_pct_delta=("abs_pct_delta", "median"),
        p95_abs_pct_delta=("abs_pct_delta", lambda s: np.nanpercentile(s, 95)),
        conflict_rate=("conflict_flag", "mean"),
    )
    export_cmp["conflict_rate"] *= 100.0

    # overall export agreement stats
    overall = {
        "quarter": q_mode,
        "start_date": str(q_df["record_date"].min().date()),
        "end_date": str(q_df["record_date"].max().date()),
        "n_units": len(units),
        "n_days": len(days),
        "total_kwh": float(np.nansum(q_df["net_kwh"])),
        "site_total_kwh": float(np.nansum(q_df["site_kwh"])),
        "field_total_kwh": float(np.nansum(q_df["field_kwh"])),
        "n_conflict_rows": int(q_df["conflict_flag"].sum()),
        "pct_conflict_of_overlap": float(overlap["conflict_flag"].mean() * 100.0) if len(overlap) else np.nan,
        "pct_missing_site": float(q_df["site_kwh"].isna().mean() * 100.0),
        "pct_missing_field": float(q_df["field_kwh"].isna().mean() * 100.0),
        "pct_zero_days_overall": float((q_df["net_kwh"].fillna(0) == 0).mean() * 100.0),
        "pct_negative_rows": float((q_df["net_kwh"] < 0).mean() * 100.0),
    }

    pd.Series(overall).to_csv(os.path.join(OUT_DIR, "quarter_overall_metrics.csv"), header=False)
    q_df.to_csv(os.path.join(OUT_DIR, "merged_quarter_daily_unit_kwh.csv"), index=False)
    daily_total.to_csv(os.path.join(OUT_DIR, "daily_total_kwh.csv"), index=False)
    unit_summary.sort_values("quarter_kwh", ascending=False).to_csv(os.path.join(OUT_DIR, "unit_quarter_summary.csv"), index=False)
    export_cmp.sort_values("conflict_rate", ascending=False).to_csv(os.path.join(OUT_DIR, "export_comparison_by_unit.csv"), index=False)

    # --- Figures ---
    # Fig 1: Daily total kWh with rolling average + conflict markers
    fig, ax1 = plt.subplots(figsize=(11, 4.5))
    ax1.plot(daily_total["record_date"], daily_total["total_kwh"], lw=1.0, label="Daily total")
    ax1.plot(daily_total["record_date"], daily_total["rolling7_kwh"], lw=2.0, label="7-day rolling mean")
    ax1.set_title(f"{q_mode} Daily Net Energy (Merged)")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Net kWh")
    ax1.legend(loc="upper left")
    ax2 = ax1.twinx()
    ax2.bar(daily_total["record_date"], daily_total["n_conflicts"], alpha=0.2, color="red", label="# conflicts")
    ax2.set_ylabel("Conflicting rows (site vs field)")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "fig1_daily_total_kwh.png"), dpi=200)
    plt.close(fig)

    # Fig 2: Unit contribution over time (stacked area for top units)
    top_units = unit_summary.sort_values("quarter_kwh", ascending=False).head(6)["generator_unit"].tolist()
    piv = q_df[q_df["generator_unit"].isin(top_units)].pivot_table(
        index="record_date", columns="generator_unit", values="net_kwh", aggfunc="sum"
    ).fillna(0)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.stackplot(piv.index, [piv[c].values for c in piv.columns], labels=piv.columns, alpha=0.85)
    ax.set_title(f"{q_mode} Daily Net kWh: Top Unit Contributions (Merged)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Net kWh")
    ax.legend(loc="upper left", ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "fig2_top_unit_stackplot.png"), dpi=200)
    plt.close(fig)

    # Fig 3: Site vs Field agreement scatter (overlap only)
    if len(overlap) > 0:
        sample = overlap.copy()
        # downsample if huge
        if len(sample) > 5000:
            sample = sample.sample(5000, random_state=7)
        fig, ax = plt.subplots(figsize=(6.2, 6.2))
        sns.scatterplot(
            data=sample,
            x="site_kwh",
            y="field_kwh",
            hue="conflict_flag",
            alpha=0.5,
            ax=ax,
            palette={False: "#1f77b4", True: "#d62728"},
            edgecolor=None,
        )
        maxv = np.nanmax([sample["site_kwh"].max(), sample["field_kwh"].max()])
        ax.plot([0, maxv], [0, maxv], ls="--", c="black", lw=1)
        ax.set_title(f"{q_mode} Export Agreement: Site vs Field (Daily/Unit)")
        ax.set_xlabel("Site historian kWh")
        ax.set_ylabel("Field export kWh")
        ax.legend(title="Conflict")
        fig.tight_layout()
        fig.savefig(os.path.join(IMG_DIR, "fig3_site_vs_field_scatter.png"), dpi=200)
        plt.close(fig)

    # Fig 4: Conflict + missingness by unit
    fig, ax = plt.subplots(figsize=(11, 4.5))
    plot_df = unit_summary.copy()
    plot_df = plot_df.sort_values("n_conflict_days", ascending=False)
    x = np.arange(len(plot_df))
    ax.bar(x, plot_df["n_conflict_days"], label="Conflict days", color="#d62728", alpha=0.8)
    ax.bar(x, plot_df["n_missing_site"], bottom=plot_df["n_conflict_days"], label="Missing site", color="#ff9896", alpha=0.6)
    ax.bar(x, plot_df["n_missing_field"], bottom=plot_df["n_conflict_days"] + plot_df["n_missing_site"], label="Missing field", color="#c5b0d5", alpha=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(plot_df["generator_unit"].tolist(), rotation=45, ha="right")
    ax.set_ylabel("Days")
    ax.set_title(f"{q_mode} Data Quality by Unit: Conflicts & Missingness")
    ax.legend(ncol=3, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "fig4_data_quality_by_unit.png"), dpi=200)
    plt.close(fig)

    # Fig 5: Distribution of daily unit kWh (boxplot for top units)
    top_units2 = unit_summary.sort_values("quarter_kwh", ascending=False).head(10)["generator_unit"].tolist()
    box_df = q_df[q_df["generator_unit"].isin(top_units2)].copy()
    fig, ax = plt.subplots(figsize=(11, 4.8))
    sns.boxplot(data=box_df, x="generator_unit", y="net_kwh", ax=ax)
    ax.set_title(f"{q_mode} Daily Net kWh Distribution (Top 10 Units)")
    ax.set_xlabel("Generator unit")
    ax.set_ylabel("Net kWh")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "fig5_unit_daily_kwh_boxplot.png"), dpi=200)
    plt.close(fig)

    print("Wrote outputs to:", OUT_DIR)
    print("Wrote figures to:", IMG_DIR)


if __name__ == "__main__":
    main()
