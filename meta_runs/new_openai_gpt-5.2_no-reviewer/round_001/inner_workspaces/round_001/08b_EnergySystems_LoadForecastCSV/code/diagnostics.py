#!/usr/bin/env python
"""Additional reliability-oriented diagnostics for load series.

Reads outputs/hourly_load.parquet created by load_forecast.py and produces:
- ramp statistics table (outputs/ramp_stats.csv)
- top peaks table (outputs/top_peaks.csv)
- figures:
  - fig6_ramp_distribution.png
  - fig7_average_profiles.png

"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

OUT_DIR = "outputs"
FIG_DIR = os.path.join("report", "images")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    sh = pd.read_parquet(os.path.join(OUT_DIR, "hourly_load.parquet"))["load"].dropna()

    # Basic annual stats for last 12 months
    last12 = sh.loc[sh.index.max() - pd.Timedelta(days=365) :]
    stats = {
        "last12_mean": float(last12.mean()),
        "last12_median": float(last12.median()),
        "last12_min": float(last12.min()),
        "last12_max": float(last12.max()),
        "last12_p95": float(last12.quantile(0.95)),
        "last12_load_factor_mean_over_peak": float(last12.mean() / last12.max()),
    }

    # Ramps
    ramp1 = sh.diff(1)
    ramp3 = sh.diff(3)
    ramp6 = sh.diff(6)

    ramp_stats = {
        **stats,
        "ramp1_p95_up": float(ramp1.quantile(0.95)),
        "ramp1_p95_down": float(ramp1.quantile(0.05)),
        "ramp1_max_up": float(ramp1.max()),
        "ramp1_max_down": float(ramp1.min()),
        "ramp3_p95_up": float(ramp3.quantile(0.95)),
        "ramp3_p95_down": float(ramp3.quantile(0.05)),
        "ramp6_p95_up": float(ramp6.quantile(0.95)),
        "ramp6_p95_down": float(ramp6.quantile(0.05)),
    }

    pd.Series(ramp_stats).to_csv(os.path.join(OUT_DIR, "ramp_stats.csv"), header=False)

    # Top peaks (last 12 months)
    top = last12.sort_values(ascending=False).head(20).to_frame("load")
    top["date"] = top.index.date
    top["hour"] = top.index.hour
    top.to_csv(os.path.join(OUT_DIR, "top_peaks_last12m.csv"), index_label="timestamp")

    # Figure: ramp distributions
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bins = 60
    ax.hist(ramp1.dropna().values, bins=bins, alpha=0.6, label="1h ramp")
    ax.hist(ramp3.dropna().values, bins=bins, alpha=0.4, label="3h ramp")
    ax.axvline(ramp1.quantile(0.95), color="black", ls="--", lw=1, label="1h 95%")
    ax.axvline(ramp1.quantile(0.05), color="black", ls=":", lw=1)
    ax.set_title("Ramp distribution (hourly deltas)")
    ax.set_xlabel("ΔLoad")
    ax.set_ylabel("Count")
    ax.legend(frameon=False, ncols=3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig6_ramp_distribution.png"), dpi=200)
    plt.close(fig)

    # Figure: average profiles by hour and day-of-week
    df = sh.to_frame("load")
    df["hour"] = df.index.hour
    df["dow"] = df.index.day_name()
    df["month"] = df.index.month

    order_dow = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    prof = df.groupby(["dow", "hour"])['load'].mean().reset_index()

    fig, ax = plt.subplots(figsize=(10, 4.5))
    for d in order_dow:
        g = prof[prof['dow'] == d]
        ax.plot(g['hour'], g['load'], lw=1.6, label=d)
    ax.set_title("Average diurnal profile by day-of-week")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Load")
    ax.set_xticks(range(0, 24, 3))
    ax.legend(frameon=False, ncols=4, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig7_avg_diurnal_by_dow.png"), dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
