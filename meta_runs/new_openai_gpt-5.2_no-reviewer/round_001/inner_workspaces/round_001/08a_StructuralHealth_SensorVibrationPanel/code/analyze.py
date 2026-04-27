"""StructuralHealth SensorVibrationPanel analysis.

Reads sensor_panel_timeseries.csv and produces:
- overview tables in outputs/
- figures in report/images/

Reproducible, no external network access.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


DATA_PATH = Path("data/sensor_panel_timeseries.csv")
OUT_DIR = Path("outputs")
FIG_DIR = Path("report/images")


def ensure_dirs():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def parse_quality_good(df: pd.DataFrame) -> pd.Series:
    """Heuristic: treat explicit bad flags as not-good; otherwise good.

    Handles numeric and string flags.
    """
    q = df.get("quality_flag")
    if q is None:
        return pd.Series(True, index=df.index)

    # Normalize to string for robust matching
    q_str = q.astype(str).str.strip().str.lower()

    # Common 'bad' tokens
    bad_tokens = {
        "bad",
        "poor",
        "invalid",
        "fail",
        "fault",
        "suspect",
        "questionable",
        "0",  # sometimes 0=bad
        "false",
        "f",
        "reject",
    }
    good_tokens = {
        "good",
        "ok",
        "okay",
        "valid",
        "pass",
        "1",  # sometimes 1=good
        "true",
        "t",
        "accept",
    }

    # If looks numeric and only {0,1}, assume 1=good, 0=bad
    unique = set(q_str.dropna().unique().tolist())
    if unique.issubset({"0", "1"}):
        return q_str == "1"

    # Otherwise, treat explicit good/bad keywords accordingly; unknown -> good
    is_bad = q_str.isin(bad_tokens)
    is_good = q_str.isin(good_tokens)
    return is_good | (~is_bad)


def robust_time_summary(df: pd.DataFrame) -> dict:
    tmin = df["timestamp_utc"].min()
    tmax = df["timestamp_utc"].max()
    out = {
        "n_rows": int(len(df)),
        "n_assets": int(df["asset_id"].nunique()),
        "n_zones": int(df["zone"].nunique()),
        "t_start": None if pd.isna(tmin) else str(tmin),
        "t_end": None if pd.isna(tmax) else str(tmax),
        "duration_days": None
        if pd.isna(tmin) or pd.isna(tmax)
        else float((tmax - tmin) / pd.Timedelta(days=1)),
    }
    return out


def compute_sampling_by_asset(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for asset, g in df.sort_values("timestamp_utc").groupby("asset_id"):
        ts = g["timestamp_utc"].dropna().sort_values()
        if len(ts) < 2:
            rows.append(
                {
                    "asset_id": asset,
                    "n_rows": int(len(g)),
                    "t_start": str(ts.min()) if len(ts) else None,
                    "t_end": str(ts.max()) if len(ts) else None,
                    "duration_days": float((ts.max() - ts.min()) / pd.Timedelta(days=1))
                    if len(ts)
                    else None,
                    "median_dt_s": np.nan,
                    "p10_dt_s": np.nan,
                    "p90_dt_s": np.nan,
                    "min_dt_s": np.nan,
                    "max_dt_s": np.nan,
                    "gap_rate_gt_2x_median": np.nan,
                }
            )
            continue
        deltas = ts.diff().dropna().dt.total_seconds().astype(float)
        med = float(np.median(deltas))
        rows.append(
            {
                "asset_id": asset,
                "n_rows": int(len(g)),
                "t_start": str(ts.min()),
                "t_end": str(ts.max()),
                "duration_days": float((ts.max() - ts.min()) / pd.Timedelta(days=1)),
                "median_dt_s": med,
                "p10_dt_s": float(np.quantile(deltas, 0.1)),
                "p90_dt_s": float(np.quantile(deltas, 0.9)),
                "min_dt_s": float(np.min(deltas)),
                "max_dt_s": float(np.max(deltas)),
                "gap_rate_gt_2x_median": float(np.mean(deltas > 2 * med)) if med > 0 else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["median_dt_s", "asset_id"], na_position="last")


def plot_asset_timelines(asset_summary: pd.DataFrame):
    df = asset_summary.copy()
    df = df.dropna(subset=["t_start", "t_end"])
    df["t_start"] = pd.to_datetime(df["t_start"], utc=True)
    df["t_end"] = pd.to_datetime(df["t_end"], utc=True)
    df = df.sort_values("t_start")

    fig, ax = plt.subplots(figsize=(10, max(2.5, 0.35 * len(df))))
    y = np.arange(len(df))
    ax.hlines(y=y, xmin=df["t_start"], xmax=df["t_end"], color="#4C78A8", linewidth=3)
    ax.plot(df["t_start"], y, "|", color="#4C78A8")
    ax.plot(df["t_end"], y, "|", color="#4C78A8")
    ax.set_yticks(y)
    ax.set_yticklabels(df["asset_id"].astype(str))
    ax.set_xlabel("timestamp (UTC)")
    ax.set_title("Observation window by asset")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "observation_window_by_asset.png", dpi=200)
    plt.close(fig)


def plot_sampling_distribution(asset_summary: pd.DataFrame):
    df = asset_summary.copy()
    df = df[np.isfinite(df["median_dt_s"])].copy()
    if df.empty:
        return
    df["median_dt_min"] = df["median_dt_s"] / 60.0

    fig, ax = plt.subplots(figsize=(8, 4))
    sns.histplot(df["median_dt_min"], bins=30, ax=ax, color="#F58518")
    ax.set_xlabel("Median sampling interval by asset (minutes)")
    ax.set_ylabel("Asset count")
    ax.set_title("Implied sampling (median timestamp spacing)")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "sampling_interval_hist.png", dpi=200)
    plt.close(fig)


def plot_vibration_timeseries(df: pd.DataFrame, good_mask: pd.Series):
    # Keep only rows with vibration data
    d = df.loc[good_mask].dropna(subset=["vibration_rms_mm_s"]).copy()
    if d.empty:
        return

    # Downsample to hourly median per asset to reduce noise / size
    d = d.set_index("timestamp_utc")
    hourly = (
        d.groupby("asset_id")["vibration_rms_mm_s"]
        .resample("1h")
        .median()
        .reset_index()
        .dropna(subset=["vibration_rms_mm_s"])
    )

    # Rolling median over 24h (on the resampled series) to emphasize trend
    hourly = hourly.sort_values(["asset_id", "timestamp_utc"])
    hourly["vib_24h_roll_med"] = (
        hourly.groupby("asset_id")["vibration_rms_mm_s"]
        .transform(lambda s: s.rolling(24, min_periods=6).median())
    )

    g = sns.FacetGrid(hourly, col="asset_id", col_wrap=3, sharey=False, height=2.2, aspect=1.6)
    g.map_dataframe(sns.lineplot, x="timestamp_utc", y="vibration_rms_mm_s", color="#9ecae1", linewidth=0.8)
    g.map_dataframe(sns.lineplot, x="timestamp_utc", y="vib_24h_roll_med", color="#08519c", linewidth=1.4)
    g.set_axis_labels("", "vibration RMS (mm/s)")
    g.set_titles(col_template="asset {col_name}")
    for ax in g.axes.flatten():
        ax.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "vibration_rms_timeseries_by_asset.png", dpi=200)
    plt.close()


def plot_zone_comparison(df: pd.DataFrame, good_mask: pd.Series):
    d = df.loc[good_mask].dropna(subset=["vibration_rms_mm_s", "zone"]).copy()
    if d.empty:
        return

    # Use per-asset weekly median to avoid overweighting high-frequency assets
    d = d.set_index("timestamp_utc")
    weekly = (
        d.groupby(["asset_id", "zone"])["vibration_rms_mm_s"]
        .resample("7D")
        .median()
        .reset_index()
        .dropna(subset=["vibration_rms_mm_s"])
    )

    fig, ax = plt.subplots(figsize=(9, 4.5))
    order = (
        weekly.groupby("zone")["vibration_rms_mm_s"]
        .median()
        .sort_values(ascending=False)
        .index
        .tolist()
    )
    sns.boxplot(data=weekly, x="zone", y="vibration_rms_mm_s", order=order, ax=ax, color="#4C78A8")
    sns.stripplot(
        data=weekly,
        x="zone",
        y="vibration_rms_mm_s",
        order=order,
        ax=ax,
        color="black",
        alpha=0.25,
        size=2,
        jitter=0.25,
    )
    ax.set_xlabel("Zone")
    ax.set_ylabel("Weekly median vibration RMS (mm/s) per asset")
    ax.set_title("Vibration RMS distribution by zone (weekly medians)")
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "vibration_by_zone_weekly_box.png", dpi=200)
    plt.close(fig)


def _corr_group(g: pd.DataFrame, cols: list[str]) -> dict:
    out = {}
    gg = g[cols].dropna()
    if len(gg) < 20:
        # Too few points for stable estimates
        for a in cols:
            for b in cols:
                if a < b:
                    out[f"corr_{a}__{b}"] = np.nan
        out["n_complete"] = int(len(gg))
        return out
    c = gg.corr(numeric_only=True)
    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            out[f"corr_{a}__{b}"] = float(c.loc[a, b])
    out["n_complete"] = int(len(gg))
    return out


def compute_relationships(df: pd.DataFrame, good_mask: pd.Series) -> pd.DataFrame:
    cols = ["vibration_rms_mm_s", "peak_accel_g", "bearing_temp_c", "rpm", "load_pct"]
    base = df.loc[good_mask, ["asset_id"] + cols].copy()

    rows = []
    overall = {"asset_id": "__overall__"}
    overall.update(_corr_group(base, cols))
    rows.append(overall)

    for asset, g in base.groupby("asset_id"):
        row = {"asset_id": asset}
        row.update(_corr_group(g, cols))
        rows.append(row)
    return pd.DataFrame(rows)


def plot_relationship_scatter(df: pd.DataFrame, good_mask: pd.Series):
    d = df.loc[good_mask].copy()
    # focus on rows where vibration_rms exists
    d = d.dropna(subset=["vibration_rms_mm_s"])
    if d.empty:
        return

    # Create 3 scatter panels if data available
    pairs = [
        ("bearing_temp_c", "Bearing temperature (°C)"),
        ("rpm", "Speed (rpm)"),
        ("load_pct", "Load (%)"),
    ]

    available = [(x, lab) for x, lab in pairs if d[x].notna().sum() >= 30]
    if not available:
        return

    n = len(available)
    fig, axes = plt.subplots(1, n, figsize=(5.3 * n, 4.2), sharey=True)
    if n == 1:
        axes = [axes]

    # Downsample if huge
    if len(d) > 20000:
        d_plot = d.sample(20000, random_state=7)
    else:
        d_plot = d

    for ax, (x, xlab) in zip(axes, available):
        sns.scatterplot(
            data=d_plot,
            x=x,
            y="vibration_rms_mm_s",
            hue="asset_id",
            alpha=0.35,
            s=14,
            ax=ax,
            legend=False,
        )
        # add trend line (pooled)
        sns.regplot(
            data=d_plot[[x, "vibration_rms_mm_s"]].dropna(),
            x=x,
            y="vibration_rms_mm_s",
            scatter=False,
            color="black",
            ci=None,
            line_kws={"linewidth": 1.6, "alpha": 0.8},
            ax=ax,
        )
        ax.set_xlabel(xlab)
        ax.set_ylabel("Vibration RMS (mm/s)")
        ax.grid(True, alpha=0.25)

    fig.suptitle("Vibration vs operating conditions (good-quality rows)", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "vibration_vs_temp_rpm_load.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_multichannel_timeseries(df: pd.DataFrame, good_mask: pd.Series):
    # pick assets with good coverage for all channels
    cols = ["vibration_rms_mm_s", "bearing_temp_c", "rpm", "load_pct"]
    cov = (
        df.loc[good_mask]
        .groupby("asset_id")[cols]
        .apply(lambda g: g.notna().mean())
        .reset_index()
    )
    cov["min_cov"] = cov[cols].min(axis=1)
    top = cov.sort_values("min_cov", ascending=False).head(3)["asset_id"].tolist()

    d = df.loc[good_mask & df["asset_id"].isin(top)].copy()
    d = d.dropna(subset=["timestamp_utc"])
    if d.empty:
        return

    # hourly medians
    d = d.set_index("timestamp_utc")
    hourly = (
        d.groupby("asset_id")[cols]
        .resample("1h")
        .median()
        .reset_index()
    )

    # plot per asset (4 subplots)
    for asset, g in hourly.groupby("asset_id"):
        fig, axes = plt.subplots(4, 1, figsize=(10, 7.8), sharex=True)
        series = [
            ("vibration_rms_mm_s", "Vibration RMS (mm/s)", "#08519c"),
            ("bearing_temp_c", "Bearing temp (°C)", "#d7301f"),
            ("rpm", "Speed (rpm)", "#238b45"),
            ("load_pct", "Load (%)", "#6a51a3"),
        ]
        for ax, (col, ylab, color) in zip(axes, series):
            sns.lineplot(data=g, x="timestamp_utc", y=col, ax=ax, color=color, linewidth=1.2)
            ax.set_ylabel(ylab)
            ax.grid(True, alpha=0.25)
        axes[-1].set_xlabel("timestamp (UTC)")
        fig.suptitle(f"Multichannel telemetry (hourly medians): asset {asset}", y=0.98)
        fig.tight_layout(rect=[0, 0, 1, 0.97])
        fig.savefig(FIG_DIR / f"multichannel_timeseries_asset_{asset}.png", dpi=200)
        plt.close(fig)


def main():
    ensure_dirs()
    sns.set_theme(style="whitegrid")

    df = pd.read_csv(DATA_PATH)
    # Parse timestamps
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")

    good_mask = parse_quality_good(df)

    # Overview
    overview_all = robust_time_summary(df)
    overview_good = robust_time_summary(df.loc[good_mask])

    # Asset summaries / sampling
    asset_summary_all = compute_sampling_by_asset(df)
    asset_summary_good = compute_sampling_by_asset(df.loc[good_mask])

    # Missingness per asset
    measure_cols = [
        "vibration_rms_mm_s",
        "peak_accel_g",
        "bearing_temp_c",
        "rpm",
        "load_pct",
    ]
    missing_by_asset = (
        df.groupby(["asset_id", "zone"], dropna=False)[measure_cols]
        .apply(lambda g: g.notna().mean())
        .reset_index()
        .rename(columns={c: f"coverage_{c}" for c in measure_cols})
    )

    # Relationships/correlations
    corr = compute_relationships(df, good_mask)

    # Trend metrics: simple linear slope on hourly medians per asset
    d_v = df.loc[good_mask].dropna(subset=["timestamp_utc", "vibration_rms_mm_s"]).copy()
    trend_rows = []
    if not d_v.empty:
        h = (
            d_v.set_index("timestamp_utc")
            .groupby("asset_id")["vibration_rms_mm_s"]
            .resample("6h")
            .median()
            .reset_index()
            .dropna()
        )
        for asset, g in h.groupby("asset_id"):
            if len(g) < 10:
                continue
            # time in days from start
            t = (g["timestamp_utc"] - g["timestamp_utc"].min()) / pd.Timedelta(days=1)
            y = g["vibration_rms_mm_s"].astype(float)
            # Robust-ish: median absolute deviation outlier clip
            med = float(np.median(y))
            mad = float(np.median(np.abs(y - med)))
            if mad > 0:
                z = 0.6745 * (y - med) / mad
                keep = np.abs(z) <= 5
                t, y = t[keep], y[keep]
            if len(y) < 10:
                continue
            slope, intercept = np.polyfit(t, y, 1)
            trend_rows.append(
                {
                    "asset_id": asset,
                    "n_points_6h": int(len(y)),
                    "slope_mm_s_per_day": float(slope),
                    "start_mm_s": float(intercept),
                    "end_minus_start_mm_s": float(slope * float(t.max() - t.min())),
                    "median_mm_s": float(np.median(y)),
                }
            )
    trend = pd.DataFrame(trend_rows).sort_values("slope_mm_s_per_day", ascending=False)

    # Save tables
    (OUT_DIR / "overview_all.json").write_text(json.dumps(overview_all, indent=2))
    (OUT_DIR / "overview_good.json").write_text(json.dumps(overview_good, indent=2))
    asset_summary_all.to_csv(OUT_DIR / "asset_sampling_all.csv", index=False)
    asset_summary_good.to_csv(OUT_DIR / "asset_sampling_good.csv", index=False)
    missing_by_asset.to_csv(OUT_DIR / "coverage_by_asset_zone.csv", index=False)
    corr.to_csv(OUT_DIR / "correlations_good.csv", index=False)
    trend.to_csv(OUT_DIR / "vibration_trend_slopes_good.csv", index=False)

    # Figures
    plot_asset_timelines(asset_summary_all)
    plot_sampling_distribution(asset_summary_all)
    plot_vibration_timeseries(df, good_mask)
    plot_zone_comparison(df, good_mask)
    plot_relationship_scatter(df, good_mask)
    plot_multichannel_timeseries(df, good_mask)


if __name__ == "__main__":
    main()
