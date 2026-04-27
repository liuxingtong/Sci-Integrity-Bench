# -*- coding: utf-8 -*-
"""Annual load forecast + reliability-oriented analytics for 15-min load series.

This script:
- loads and cleans 15-minute load data
- derives daily/annual metrics (energy, peak)
- fits calendar-only regression models for daily energy and daily peak
- backtests on the last full year (if available)
- produces next-year (annual) forecast distribution via residual bootstrap
- generates figures and writes summary tables

Run:
  python code/run_analysis.py
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

try:
    import statsmodels.api as sm
except Exception as e:
    sm = None


DATA_PATH = os.path.join("data", "load_15min.csv")
OUT_DIR = "outputs"
FIG_DIR = os.path.join("report", "images")

RANDOM_SEED = 7
np.random.seed(RANDOM_SEED)


@dataclass
class ColumnGuess:
    dt_col: str
    load_col: str


def guess_columns(df: pd.DataFrame) -> ColumnGuess:
    # datetime column
    dt_candidates = [c for c in df.columns if any(k in c.lower() for k in ["time", "date", "timestamp", "datetime"]) ]
    dt_col = dt_candidates[0] if dt_candidates else df.columns[0]

    # load column: first numeric column that is not datetime
    load_col = None
    for c in df.columns:
        if c == dt_col:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            load_col = c
            break
    if load_col is None:
        # try convert
        for c in df.columns:
            if c == dt_col:
                continue
            x = pd.to_numeric(df[c], errors="coerce")
            if x.notna().mean() > 0.95:
                df[c] = x
                load_col = c
                break
    if load_col is None:
        raise ValueError("Could not identify numeric load column")

    return ColumnGuess(dt_col=dt_col, load_col=load_col)


def load_and_clean(path: str) -> tuple[pd.DataFrame, ColumnGuess, dict]:
    df0 = pd.read_csv(path)
    cg = guess_columns(df0)

    df = df0.copy()
    df[cg.dt_col] = pd.to_datetime(df[cg.dt_col], errors="coerce")
    df[cg.load_col] = pd.to_numeric(df[cg.load_col], errors="coerce")

    df = df.dropna(subset=[cg.dt_col, cg.load_col]).sort_values(cg.dt_col)

    # drop duplicate timestamps by averaging
    df = df.groupby(cg.dt_col, as_index=False)[cg.load_col].mean()
    df = df.set_index(cg.dt_col).sort_index()

    # infer interval
    diffs = df.index.to_series().diff().dropna()
    median_diff = diffs.median()

    # reindex to complete 15-min grid between min and max
    full_index = pd.date_range(df.index.min(), df.index.max(), freq="15min")
    s = df[cg.load_col].reindex(full_index)

    missing_rate = s.isna().mean()

    # fill short gaps (<= 1 hour) using time interpolation; longer gaps left as NA then forward/back fill
    s_interp = s.interpolate(method="time", limit=4, limit_direction="both")
    # for any remaining missing, use seasonal (same time-of-week) median as fallback
    if s_interp.isna().any():
        tmp = s_interp.copy()
        dow = tmp.index.dayofweek
        hod = tmp.index.hour
        qtr = (tmp.index.minute // 15)
        key = pd.MultiIndex.from_arrays([dow, hod, qtr], names=["dow", "hour", "qtr"])
        med = tmp.groupby(key).transform("median")
        tmp = tmp.fillna(med)
        s_interp = tmp

    # any remaining NAs -> forward/back fill
    s_interp = s_interp.ffill().bfill()

    info = {
        "n_raw": len(df0),
        "n_clean": len(df),
        "start": df.index.min(),
        "end": df.index.max(),
        "median_interval": median_diff,
        "missing_rate_reindexed": float(missing_rate),
    }

    out = pd.DataFrame({"load": s_interp})
    out.index.name = "timestamp"
    return out, cg, info


def add_calendar_features(day_index: pd.DatetimeIndex, start_date: pd.Timestamp, K: int = 3) -> pd.DataFrame:
    """Calendar-only features for daily modeling."""
    df = pd.DataFrame(index=day_index)
    df["t_days"] = (df.index - start_date).days.astype(float)
    df["t_years"] = df["t_days"] / 365.25

    df["dow"] = df.index.dayofweek
    # One-hot (drop Monday=0 baseline)
    for d in range(1, 7):
        df[f"dow_{d}"] = (df["dow"] == d).astype(int)

    # annual seasonality via Fourier terms
    doy = df.index.dayofyear.values.astype(float)
    year_len = 365.25
    for k in range(1, K + 1):
        df[f"sin{k}"] = np.sin(2 * np.pi * k * doy / year_len)
        df[f"cos{k}"] = np.cos(2 * np.pi * k * doy / year_len)

    return df.drop(columns=["dow"])  # keep only dummies


def fit_ols(y: pd.Series, X: pd.DataFrame):
    if sm is None:
        raise RuntimeError("statsmodels is required but could not be imported")
    Xc = sm.add_constant(X, has_constant="add")
    model = sm.OLS(y.values, Xc.values)
    res = model.fit()
    res.X_design_info = {"columns": ["const"] + list(X.columns)}
    return res


def predict_ols(res, X: pd.DataFrame) -> np.ndarray:
    cols = res.X_design_info["columns"]
    Xc = sm.add_constant(X, has_constant="add")
    # align to expected columns
    if list(Xc.columns) != cols:
        Xc = Xc.reindex(columns=cols, fill_value=0.0)
    return np.asarray(Xc.values @ res.params)


def bootstrap_annual(yhat_daily: pd.Series, resid: pd.Series, n_boot: int = 2000, clip_min: float | None = 0.0) -> pd.DataFrame:
    """Residual bootstrap on daily series; returns bootstrapped annual totals and peaks."""
    rng = np.random.default_rng(RANDOM_SEED)
    resid = resid.dropna().values
    n = len(yhat_daily)

    totals = np.empty(n_boot)
    peaks = np.empty(n_boot)

    for b in range(n_boot):
        eps = rng.choice(resid, size=n, replace=True)
        sim = yhat_daily.values + eps
        if clip_min is not None:
            sim = np.maximum(sim, clip_min)
        totals[b] = sim.sum()
        peaks[b] = sim.max()

    return pd.DataFrame({"annual_total": totals, "annual_peak": peaks})


def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)


def mape(y_true, y_pred) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    denom = np.maximum(np.abs(y_true), 1e-6)
    return float(np.mean(np.abs(y_true - y_pred) / denom)) * 100


def main():
    warnings.filterwarnings("ignore")
    ensure_dirs()

    load15, cg, info = load_and_clean(DATA_PATH)

    # derive basic stats
    ts = load15["load"]
    years = sorted(ts.index.year.unique())

    # 15-min energy conversion: assume load in MW => energy per interval (MWh) = MW * 0.25
    interval_hours = 0.25

    # daily aggregation
    daily = pd.DataFrame({
        "mean_mw": ts.resample("D").mean(),
        "peak_mw": ts.resample("D").max(),
        "energy_mwh": (ts * interval_hours).resample("D").sum(),
    }).dropna()

    # annual metrics
    annual = daily.resample("YE").agg({
        "mean_mw": "mean",
        "peak_mw": "max",
        "energy_mwh": "sum",
    })
    annual.index = annual.index.year
    annual = annual.rename_axis("year")

    # Reliability-oriented metrics: ramp rates
    ramp_mw_per_15min = ts.diff()
    ramp_mw_per_hr = ramp_mw_per_15min * 4
    ramp_abs = ramp_mw_per_hr.abs()

    reliability = {
        "peak_mw_overall": float(ts.max()),
        "p99_load_mw": float(ts.quantile(0.99)),
        "p01_load_mw": float(ts.quantile(0.01)),
        "min_load_mw": float(ts.min()),
        "mean_load_mw": float(ts.mean()),
        "load_factor": float(ts.mean() / ts.max()),
        "p99_abs_ramp_mw_per_hr": float(ramp_abs.quantile(0.99)),
        "max_abs_ramp_mw_per_hr": float(ramp_abs.max()),
    }

    # Identify top events for ops review context
    top_load = ts.sort_values(ascending=False).head(20).to_frame("load_mw")
    top_load["rank"] = np.arange(1, len(top_load) + 1)

    top_ramp = ramp_mw_per_hr.dropna().abs().sort_values(ascending=False).head(20).to_frame("abs_ramp_mw_per_hr")
    top_ramp["rank"] = np.arange(1, len(top_ramp) + 1)

    # ------------------- Calendar-only daily models -------------------
    start_date = daily.index.min()

    X = add_calendar_features(daily.index, start_date=start_date, K=3)

    res_energy = fit_ols(daily["energy_mwh"], X)
    res_peak = fit_ols(daily["peak_mw"], X)

    daily["energy_hat"] = predict_ols(res_energy, X)
    daily["peak_hat"] = predict_ols(res_peak, X)

    daily["energy_resid"] = daily["energy_mwh"] - daily["energy_hat"]
    daily["peak_resid"] = daily["peak_mw"] - daily["peak_hat"]

    # ------------------- Backtest: last full year if possible -------------------
    backtest = {}
    last_year = int(daily.index.max().year)
    last_year_start = pd.Timestamp(year=last_year, month=1, day=1)
    last_year_end = pd.Timestamp(year=last_year, month=12, day=31)

    has_full_last_year = (daily.index.min() <= last_year_start) and (daily.index.max() >= last_year_end)

    if has_full_last_year and len(years) >= 2:
        train = daily.loc[: last_year_start - pd.Timedelta(days=1)].copy()
        test = daily.loc[last_year_start:last_year_end].copy()

        Xtr = add_calendar_features(train.index, start_date=start_date, K=3)
        Xte = add_calendar_features(test.index, start_date=start_date, K=3)

        res_e_bt = fit_ols(train["energy_mwh"], Xtr)
        res_p_bt = fit_ols(train["peak_mw"], Xtr)

        test["energy_hat"] = predict_ols(res_e_bt, Xte)
        test["peak_hat"] = predict_ols(res_p_bt, Xte)

        backtest = {
            "energy_mae": float(np.mean(np.abs(test["energy_mwh"] - test["energy_hat"]))),
            "energy_mape_pct": float(mape(test["energy_mwh"], test["energy_hat"])) ,
            "peak_mae": float(np.mean(np.abs(test["peak_mw"] - test["peak_hat"]))),
            "peak_mape_pct": float(mape(test["peak_mw"], test["peak_hat"])) ,
        }

        # Plot backtest (weekly smoothed to focus on seasonal fit)
        fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
        test_sm = test.rolling(7, center=True, min_periods=1).mean()
        axes[0].plot(test.index, test["energy_mwh"], color="C0", alpha=0.25, lw=1, label="Actual")
        axes[0].plot(test_sm.index, test_sm["energy_mwh"], color="C0", lw=2, label="Actual (7d avg)")
        axes[0].plot(test_sm.index, test_sm["energy_hat"], color="C1", lw=2, label="Predicted (7d avg)")
        axes[0].set_ylabel("Daily energy (MWh)")
        axes[0].legend(ncol=3, fontsize=9)
        axes[0].set_title(f"Backtest on last full year ({last_year}) – calendar-only regression")

        axes[1].plot(test.index, test["peak_mw"], color="C2", alpha=0.25, lw=1, label="Actual")
        axes[1].plot(test_sm.index, test_sm["peak_mw"], color="C2", lw=2, label="Actual (7d avg)")
        axes[1].plot(test_sm.index, test_sm["peak_hat"], color="C3", lw=2, label="Predicted (7d avg)")
        axes[1].set_ylabel("Daily peak (MW)")
        axes[1].legend(ncol=3, fontsize=9)
        axes[1].grid(True, alpha=0.3)

        for ax in axes:
            ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(FIG_DIR, "fig3_backtest_daily_models.png"), dpi=200)
        plt.close(fig)

    else:
        # Always create a validation-style plot, even if a strict last-year backtest isn't possible.
        # Show in-sample fitted vs actual for the most recent 365 days (or all data if shorter).
        end_date = daily.index.max()
        start_plot = max(daily.index.min(), end_date - pd.Timedelta(days=365))
        view = daily.loc[start_plot:end_date].copy()
        view_sm = view.rolling(7, center=True, min_periods=1).mean()

        fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
        axes[0].plot(view.index, view["energy_mwh"], color="C0", alpha=0.25, lw=1, label="Actual")
        axes[0].plot(view_sm.index, view_sm["energy_mwh"], color="C0", lw=2, label="Actual (7d avg)")
        axes[0].plot(view_sm.index, view_sm["energy_hat"], color="C1", lw=2, label="Fitted (7d avg)")
        axes[0].set_ylabel("Daily energy (MWh)")
        axes[0].legend(ncol=3, fontsize=9)
        axes[0].set_title("Model fit view (in-sample; most recent ~12 months)")

        axes[1].plot(view.index, view["peak_mw"], color="C2", alpha=0.25, lw=1, label="Actual")
        axes[1].plot(view_sm.index, view_sm["peak_mw"], color="C2", lw=2, label="Actual (7d avg)")
        axes[1].plot(view_sm.index, view_sm["peak_hat"], color="C3", lw=2, label="Fitted (7d avg)")
        axes[1].set_ylabel("Daily peak (MW)")
        axes[1].legend(ncol=3, fontsize=9)
        axes[1].grid(True, alpha=0.3)

        for ax in axes:
            ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(FIG_DIR, "fig3_backtest_daily_models.png"), dpi=200)
        plt.close(fig)

    # ------------------- Forecast next year (full calendar year) -------------------
    forecast_year = int(daily.index.max().year) + 1
    f_start = pd.Timestamp(year=forecast_year, month=1, day=1)
    f_end = pd.Timestamp(year=forecast_year, month=12, day=31)
    f_days = pd.date_range(f_start, f_end, freq="D")
    Xf = add_calendar_features(f_days, start_date=start_date, K=3)

    energy_hat = pd.Series(predict_ols(res_energy, Xf), index=f_days, name="energy_hat_mwh")
    peak_hat = pd.Series(predict_ols(res_peak, Xf), index=f_days, name="peak_hat_mw")

    # Bootstrap annual energy and peak distributions from daily residuals
    boot_energy = bootstrap_annual(energy_hat, daily["energy_resid"], n_boot=2000, clip_min=0.0)
    boot_peak = bootstrap_annual(peak_hat, daily["peak_resid"], n_boot=2000, clip_min=0.0)

    # Note: bootstrap_annual returns both total and peak; but inputs differ; keep separate labeling
    energy_total_dist = boot_energy["annual_total"]
    peak_dist = boot_peak["annual_peak"]

    def qstats(x: pd.Series | np.ndarray):
        x = np.asarray(x)
        return {
            "p10": float(np.quantile(x, 0.10)),
            "p50": float(np.quantile(x, 0.50)),
            "p90": float(np.quantile(x, 0.90)),
            "mean": float(np.mean(x)),
        }

    annual_forecast = {
        "forecast_year": forecast_year,
        "annual_energy_mwh": qstats(energy_total_dist),
        "annual_peak_mw": qstats(peak_dist),
    }

    # Monthly forecast profile (P50)
    monthly_fc = pd.DataFrame({
        "energy_mwh_p50": energy_hat,
        "peak_mw_p50": peak_hat,
    })
    monthly_fc = monthly_fc.resample("ME").agg({"energy_mwh_p50": "sum", "peak_mw_p50": "max"})
    monthly_fc.index = monthly_fc.index.to_period("M").astype(str)

    # ------------------- Figures -------------------
    sns.set_theme(style="whitegrid")

    # Fig 1: daily mean time series
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(daily.index, daily["mean_mw"], lw=0.6, color="C0")
    ax.set_title("Daily mean load (15-min series aggregated to daily)")
    ax.set_ylabel("MW")
    ax.set_xlabel("Date")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig1_daily_mean_timeseries.png"), dpi=200)
    plt.close(fig)

    # Fig 2: annual energy + annual peak
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    axes[0].bar(annual.index.astype(str), annual["energy_mwh"] / 1e6, color="C0", alpha=0.85)
    axes[0].set_ylabel("Annual energy (TWh)")
    axes[0].set_title("Historical annual energy and peak")

    axes[1].bar(annual.index.astype(str), annual["peak_mw"], color="C3", alpha=0.85)
    axes[1].set_ylabel("Annual peak (MW)")
    axes[1].set_xlabel("Year")

    for ax in axes:
        ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig2_annual_energy_and_peak.png"), dpi=200)
    plt.close(fig)

    # Fig 4: forecast distributions
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    sns.histplot(energy_total_dist / 1e6, kde=True, ax=axes[0], color="C0")
    axes[0].set_title(f"Forecast {forecast_year} annual energy")
    axes[0].set_xlabel("TWh")
    for q, lab in [(0.1, "P10"), (0.5, "P50"), (0.9, "P90")]:
        v = np.quantile(energy_total_dist / 1e6, q)
        axes[0].axvline(v, color="k", ls="--", lw=1)
        axes[0].text(v, axes[0].get_ylim()[1]*0.9, lab, rotation=90, va="top", ha="right", fontsize=9)

    sns.histplot(peak_dist, kde=True, ax=axes[1], color="C3")
    axes[1].set_title(f"Forecast {forecast_year} annual peak")
    axes[1].set_xlabel("MW")
    for q, lab in [(0.1, "P10"), (0.5, "P50"), (0.9, "P90")]:
        v = np.quantile(peak_dist, q)
        axes[1].axvline(v, color="k", ls="--", lw=1)
        axes[1].text(v, axes[1].get_ylim()[1]*0.9, lab, rotation=90, va="top", ha="right", fontsize=9)

    for ax in axes:
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig4_forecast_distributions.png"), dpi=200)
    plt.close(fig)

    # Fig 7: historical vs forecast (P10-P90) for annual energy and peak
    # Use historical annual metrics + add forecast point with uncertainty.
    e_q = {
        "p10": float(np.quantile(energy_total_dist, 0.10)),
        "p50": float(np.quantile(energy_total_dist, 0.50)),
        "p90": float(np.quantile(energy_total_dist, 0.90)),
    }
    p_q = {
        "p10": float(np.quantile(peak_dist, 0.10)),
        "p50": float(np.quantile(peak_dist, 0.50)),
        "p90": float(np.quantile(peak_dist, 0.90)),
    }

    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    years_hist = annual.index.values.astype(int)

    # Energy (TWh)
    axes[0].plot(years_hist, annual["energy_mwh"].values / 1e6, marker="o", color="C0", lw=2, label="Historical")
    axes[0].errorbar(
        [forecast_year],
        [e_q["p50"] / 1e6],
        yerr=[[ (e_q["p50"]-e_q["p10"]) / 1e6 ], [ (e_q["p90"]-e_q["p50"]) / 1e6 ]],
        fmt="o",
        color="k",
        capsize=4,
        label=f"Forecast {forecast_year} (P10–P90)",
    )
    axes[0].set_ylabel("Annual energy (TWh)")
    axes[0].set_title("Historical annual metrics with next-year forecast uncertainty")
    axes[0].legend(fontsize=9)

    # Peak (MW)
    axes[1].plot(years_hist, annual["peak_mw"].values, marker="o", color="C3", lw=2, label="Historical")
    axes[1].errorbar(
        [forecast_year],
        [p_q["p50"]],
        yerr=[[ (p_q["p50"]-p_q["p10"]) ], [ (p_q["p90"]-p_q["p50"]) ]],
        fmt="o",
        color="k",
        capsize=4,
        label=f"Forecast {forecast_year} (P10–P90)",
    )
    axes[1].set_ylabel("Annual peak (MW)")
    axes[1].set_xlabel("Year")
    axes[1].legend(fontsize=9)

    for ax in axes:
        ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig7_historical_vs_forecast.png"), dpi=200)
    plt.close(fig)

    # Fig 5: load duration curve (last full year if available, else all data) + ramp distribution
    if has_full_last_year:
        ts_ref = ts.loc[last_year_start:last_year_end]
        label = f"{last_year}"
    else:
        ts_ref = ts
        label = f"{years[0]}-{years[-1]}"

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    x = np.linspace(0, 100, len(ts_ref))
    y_sorted = np.sort(ts_ref.values)[::-1]
    axes[0].plot(x, y_sorted, color="C0", lw=2)
    axes[0].set_title(f"Load duration curve ({label})")
    axes[0].set_xlabel("Percent of intervals exceeded (%)")
    axes[0].set_ylabel("MW")

    sns.histplot(ramp_abs.dropna(), ax=axes[1], bins=60, color="C2")
    axes[1].set_title("Absolute ramp distribution (MW/h, 15-min differences)")
    axes[1].set_xlabel("|Ramp| (MW/h)")
    axes[1].set_ylabel("Count")

    for ax in axes:
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig5_duration_curve_and_ramps.png"), dpi=200)
    plt.close(fig)

    # Fig 6: seasonal heatmap (avg by month x hour-of-day) for last year or latest 12 months
    # Use last 12 months window if no full last year.
    if has_full_last_year:
        window = load15.loc[last_year_start:last_year_end]
        title = f"Typical diurnal shape by month ({last_year})"
    else:
        end = load15.index.max()
        start = end - pd.Timedelta(days=365)
        window = load15.loc[start:end]
        title = f"Typical diurnal shape by month (last ~12 months)"

    tmp = window.copy()
    tmp["month"] = tmp.index.month
    tmp["hour"] = tmp.index.hour + tmp.index.minute/60.0
    # average to hourly first to reduce noise
    hourly = tmp["load"].resample("H").mean().to_frame("load")
    hourly["month"] = hourly.index.month
    hourly["hour"] = hourly.index.hour
    pivot = hourly.pivot_table(index="month", columns="hour", values="load", aggfunc="mean")

    fig, ax = plt.subplots(figsize=(11, 4))
    sns.heatmap(pivot, ax=ax, cmap="viridis")
    ax.set_title(title)
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Month")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig6_month_hour_heatmap.png"), dpi=200)
    plt.close(fig)

    # ------------------- Write outputs -------------------
    annual.to_csv(os.path.join(OUT_DIR, "historical_annual_metrics.csv"))
    daily.to_csv(os.path.join(OUT_DIR, "daily_metrics_with_fit.csv"))

    pd.DataFrame([info]).to_csv(os.path.join(OUT_DIR, "data_overview.csv"), index=False)
    pd.DataFrame([reliability]).to_csv(os.path.join(OUT_DIR, "reliability_metrics.csv"), index=False)

    top_load.to_csv(os.path.join(OUT_DIR, "top_20_load_intervals.csv"))
    top_ramp.to_csv(os.path.join(OUT_DIR, "top_20_ramp_events.csv"))

    # forecast summary table
    forecast_rows = [
        {"metric": "Annual energy (MWh)", **annual_forecast["annual_energy_mwh"]},
        {"metric": "Annual peak (MW)", **annual_forecast["annual_peak_mw"]},
    ]
    fc_tbl = pd.DataFrame(forecast_rows)
    fc_tbl.insert(0, "forecast_year", forecast_year)
    fc_tbl.to_csv(os.path.join(OUT_DIR, "forecast_summary.csv"), index=False)

    monthly_fc.to_csv(os.path.join(OUT_DIR, "forecast_monthly_p50.csv"))

    # model diagnostics text
    with open(os.path.join(OUT_DIR, "model_summaries.txt"), "w", encoding="utf-8") as f:
        f.write("=== OLS: Daily energy (MWh/day) ===\n")
        f.write(str(res_energy.summary()))
        f.write("\n\n=== OLS: Daily peak (MW) ===\n")
        f.write(str(res_peak.summary()))
        if backtest:
            f.write("\n\n=== Backtest (last full year) ===\n")
            for k, v in backtest.items():
                f.write(f"{k}: {v}\n")

    print("Data overview:", info)
    print("Reliability metrics:", reliability)
    print("Forecast year:", forecast_year)
    print("Annual forecast (P10/P50/P90):")
    print(fc_tbl)
    if backtest:
        print("Backtest metrics:", backtest)


if __name__ == "__main__":
    main()
