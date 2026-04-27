#!/usr/bin/env python
"""Annual load forecast from 15-minute load series.

Creates:
- Cleaned hourly series (outputs/hourly_load.parquet)
- Forecast tables and metrics (outputs/*.csv)
- Figures for operations/reliability review (report/images/*.png)

Assumptions:
- Input load is an average power (e.g., MW) for each 15-min interval.
- Time stamps are in chronological order or can be sorted.

Model:
- Hourly resample.
- Feature-based regression (Ridge) with calendar + Fourier annual terms.
- Prediction intervals via residual bootstrap and annual-peak simulation.

"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DATA_PATH = os.path.join("data", "load_15min.csv")
OUT_DIR = "outputs"
FIG_DIR = os.path.join("report", "images")


def _infer_columns(df: pd.DataFrame) -> Tuple[str, str]:
    # datetime column
    dt_candidates = [c for c in df.columns if any(k in c.lower() for k in ["time", "date", "timestamp", "datetime"])]
    dt_col = dt_candidates[0] if dt_candidates else df.columns[0]

    # load column (first numeric)
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if not num_cols:
        raise ValueError("No numeric columns found for load.")
    load_col = num_cols[0]
    return dt_col, load_col


def load_and_clean_15min(path: str = DATA_PATH) -> Tuple[pd.Series, Dict]:
    df = pd.read_csv(path)
    dt_col, load_col = _infer_columns(df)
    df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
    df = df.dropna(subset=[dt_col])
    df = df.sort_values(dt_col)

    s = df.set_index(dt_col)[load_col].astype(float)

    # Handle duplicate timestamps (average)
    if s.index.duplicated().any():
        s = s.groupby(level=0).mean().sort_index()

    # Reindex to regular 15-min and interpolate short gaps
    full_index = pd.date_range(s.index.min(), s.index.max(), freq="15min")
    s15 = s.reindex(full_index)

    missing_mask = s15.isna()

    # Interpolate gaps up to 2 hours (8 intervals)
    s15_interp = s15.copy()
    s15_interp = s15_interp.interpolate(limit=8, limit_direction="both")

    meta = {
        "dt_col": dt_col,
        "load_col": load_col,
        "start": str(s.index.min()),
        "end": str(s.index.max()),
        "n_raw": int(len(df)),
        "n_15min_expected": int(len(full_index)),
        "n_15min_missing": int(missing_mask.sum()),
        "missing_rate": float(missing_mask.mean()),
        "n_after_interp_missing": int(s15_interp.isna().sum()),
        "duplicates": int(df[dt_col].duplicated().sum()),
        "median_step_minutes": float(pd.Series(s.index).diff().dropna().dt.total_seconds().median() / 60.0),
    }

    return s15_interp, meta


def to_hourly(s15: pd.Series) -> pd.Series:
    # Load is average power in each 15-min interval -> hourly average is mean of 4 intervals.
    sh = s15.resample("H").mean()
    return sh


def make_features(index: pd.DatetimeIndex) -> pd.DataFrame:
    df = pd.DataFrame(index=index)
    df["hour"] = index.hour
    df["dow"] = index.dayofweek
    df["month"] = index.month
    df["dayofyear"] = index.dayofyear
    df["is_weekend"] = (df["dow"] >= 5).astype(int)

    # Annual Fourier terms (K harmonics)
    # Use 365.25 to reduce leap-year discontinuity.
    t = (index - index[0]).total_seconds() / (24 * 3600)  # days since start
    period = 365.25
    K = 3
    for k in range(1, K + 1):
        df[f"ann_sin_{k}"] = np.sin(2 * np.pi * k * t / period)
        df[f"ann_cos_{k}"] = np.cos(2 * np.pi * k * t / period)

    # Mild long-term trend
    df["t_days"] = t
    return df


@dataclass
class BacktestResult:
    metrics: Dict[str, float]
    y_true: pd.Series
    y_pred: pd.Series
    residuals: pd.Series
    train_end: pd.Timestamp


def fit_ridge_model(X: pd.DataFrame, y: pd.Series) -> Pipeline:
    cat_cols = ["hour", "dow", "month", "is_weekend"]
    num_cols = [c for c in X.columns if c not in cat_cols]

    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", Pipeline([("scaler", StandardScaler(with_mean=False))]), num_cols),
        ],
        remainder="drop",
        sparse_threshold=0.3,
    )

    model = Ridge(alpha=10.0, random_state=0)
    pipe = Pipeline([("pre", pre), ("model", model)])
    pipe.fit(X, y)
    return pipe


def backtest(sh: pd.Series, val_days: int = 60) -> Tuple[Pipeline, BacktestResult]:
    sh = sh.dropna()
    end = sh.index.max()
    train_end = end - pd.Timedelta(days=val_days)

    train = sh.loc[:train_end]
    val = sh.loc[train_end + pd.Timedelta(hours=1) :]

    Xtr = make_features(train.index)
    Xva = make_features(val.index)

    pipe = fit_ridge_model(Xtr, train)
    pred = pd.Series(pipe.predict(Xva), index=val.index, name="pred")

    y_true = val
    y_pred = pred.reindex(y_true.index)
    resid = (y_true - y_pred).rename("residual")

    rmse = mean_squared_error(y_true, y_pred, squared=False)
    mae = mean_absolute_error(y_true, y_pred)
    mape = float((np.abs(resid) / np.maximum(np.abs(y_true), 1e-6)).mean())

    # Peak metrics within validation window
    peak_true = float(y_true.max())
    peak_pred = float(y_pred.max())
    peak_err = peak_pred - peak_true

    metrics = {
        "val_start": str(y_true.index.min()),
        "val_end": str(y_true.index.max()),
        "n_val_hours": int(len(y_true)),
        "rmse": float(rmse),
        "mae": float(mae),
        "mape": float(mape),
        "val_peak_true": peak_true,
        "val_peak_pred": peak_pred,
        "val_peak_error": float(peak_err),
    }

    return pipe, BacktestResult(metrics=metrics, y_true=y_true, y_pred=y_pred, residuals=resid, train_end=train_end)


def forecast_next_year(pipe: Pipeline, last_ts: pd.Timestamp, horizon_days: int = 365) -> pd.Series:
    idx = pd.date_range(last_ts + pd.Timedelta(hours=1), periods=24 * horizon_days, freq="H")
    Xf = make_features(idx)
    yf = pd.Series(pipe.predict(Xf), index=idx, name="forecast")
    return yf


def residual_bootstrap_intervals(
    point_forecast: pd.Series,
    residuals: pd.Series,
    n_sims: int = 500,
    seed: int = 0,
) -> Tuple[pd.Series, pd.Series, pd.DataFrame]:
    """Construct prediction intervals and annual peak distribution by simulating residuals.

    Uses an hour-of-week stratified residual sampling to preserve diurnal/weekly heteroskedasticity.
    """
    rng = np.random.default_rng(seed)

    # stratify residuals by hour-of-week (0..167)
    how = residuals.index.dayofweek * 24 + residuals.index.hour
    resid_df = pd.DataFrame({"resid": residuals.values, "how": how.values})

    # Pre-split residual pools
    pools = {k: g["resid"].values for k, g in resid_df.groupby("how")}
    all_resid = residuals.values

    def sample_resid_for_index(idx: pd.DatetimeIndex) -> np.ndarray:
        how_idx = idx.dayofweek * 24 + idx.hour
        out = np.empty(len(idx), dtype=float)
        for i, k in enumerate(how_idx):
            pool = pools.get(int(k))
            if pool is None or len(pool) < 10:
                pool = all_resid
            out[i] = rng.choice(pool)
        return out

    sims = np.empty((n_sims, len(point_forecast)), dtype=float)
    idx = point_forecast.index
    for s in range(n_sims):
        eps = sample_resid_for_index(idx)
        sims[s, :] = point_forecast.values + eps

    q05 = pd.Series(np.quantile(sims, 0.05, axis=0), index=idx, name="p05")
    q95 = pd.Series(np.quantile(sims, 0.95, axis=0), index=idx, name="p95")

    peak_dist = pd.DataFrame(
        {
            "annual_peak": np.max(sims, axis=1),
            "annual_energy": np.sum(sims, axis=1),  # in load-units * hours
        }
    )

    return q05, q95, peak_dist


def seasonal_label(ts: pd.Timestamp) -> str:
    m = ts.month
    if m in (12, 1, 2):
        return "Winter"
    if m in (3, 4, 5):
        return "Spring"
    if m in (6, 7, 8):
        return "Summer"
    return "Fall"


def plot_overview(sh: pd.Series, path: str):
    sns.set_theme(style="whitegrid")
    # show daily mean for readability
    daily = sh.resample("D").mean()
    rolling = daily.rolling(30, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(daily.index, daily.values, lw=0.6, color="#4c72b0", alpha=0.7, label="Daily mean")
    ax.plot(rolling.index, rolling.values, lw=2.0, color="#dd8452", label="30-day mean")
    ax.set_title("Load overview (daily mean; hourly series aggregated)")
    ax.set_ylabel("Load")
    ax.legend(frameon=False, ncols=2)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_load_duration_by_season(sh: pd.Series, path: str):
    sns.set_theme(style="whitegrid")
    df = sh.dropna().to_frame("load")
    df["season"] = [seasonal_label(t) for t in df.index]

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for season, g in df.groupby("season"):
        x = np.linspace(0, 1, len(g))
        y = np.sort(g["load"].values)[::-1]
        ax.plot(x, y, lw=1.6, label=season)
    ax.set_title("Load duration curves by season (hourly)")
    ax.set_xlabel("Fraction of hours (sorted high→low)")
    ax.set_ylabel("Load")
    ax.legend(frameon=False, ncols=2)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_backtest(bt: BacktestResult, path: str):
    sns.set_theme(style="whitegrid")
    # Plot a 14-day slice for clarity
    y_true = bt.y_true
    y_pred = bt.y_pred
    if len(y_true) > 24 * 14:
        start = y_true.index.max() - pd.Timedelta(days=14)
        y_true = y_true.loc[start:]
        y_pred = y_pred.loc[start:]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(y_true.index, y_true.values, lw=1.0, color="black", label="Actual")
    ax.plot(y_pred.index, y_pred.values, lw=1.0, color="#4c72b0", label="Model")
    ax.set_title("Backtest (last 14 days of validation window)")
    ax.set_ylabel("Load")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_forecast(sh: pd.Series, forecast: pd.Series, p05: pd.Series, p95: pd.Series, path: str):
    sns.set_theme(style="whitegrid")

    hist_days = 60
    hist = sh.dropna().loc[sh.index.max() - pd.Timedelta(days=hist_days) :]

    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(hist.index, hist.values, color="black", lw=0.8, label=f"History (last {hist_days}d)")
    ax.plot(forecast.index, forecast.values, color="#4c72b0", lw=1.2, label="Forecast (hourly)")
    ax.fill_between(forecast.index, p05.values, p95.values, color="#4c72b0", alpha=0.2, label="90% PI")
    ax.set_title("Annual outlook: next-year hourly load forecast")
    ax.set_ylabel("Load")
    ax.legend(frameon=False, ncols=3)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_monthly_energy_peak(sh: pd.Series, forecast: pd.Series, path: str):
    sns.set_theme(style="whitegrid")
    # Compare last complete 12 months vs forecast 12 months
    end_hist = sh.dropna().index.max()
    start_hist = end_hist - pd.DateOffset(months=12)
    hist = sh.loc[start_hist:end_hist]

    def monthly_stats(x: pd.Series) -> pd.DataFrame:
        m = x.to_frame("load")
        m["month"] = m.index.to_period("M").astype(str)
        energy = x.resample("M").sum()  # load * hours
        peak = x.resample("M").max()
        out = pd.DataFrame({"energy": energy.values, "peak": peak.values}, index=energy.index)
        out.index = out.index.to_period("M").astype(str)
        return out

    hist_m = monthly_stats(hist)
    fc_m = monthly_stats(forecast)

    # Align length (last 12 months)
    hist_m = hist_m.tail(12)
    fc_m = fc_m.head(12)

    fig, ax1 = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(hist_m))

    ax1.bar(x - 0.2, hist_m["energy"].values / 1000.0, width=0.4, label="Hist energy", color="#4c72b0", alpha=0.8)
    ax1.bar(x + 0.2, fc_m["energy"].values / 1000.0, width=0.4, label="Fcst energy", color="#55a868", alpha=0.8)
    ax1.set_ylabel("Monthly energy (load·h, thousands)")

    ax2 = ax1.twinx()
    ax2.plot(x, hist_m["peak"].values, color="#dd8452", lw=2, label="Hist peak")
    ax2.plot(x, fc_m["peak"].values, color="#c44e52", lw=2, label="Fcst peak")
    ax2.set_ylabel("Monthly peak (load units)")

    labels = hist_m.index.tolist()
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha="right")
    ax1.set_title("Monthly energy and peak: last 12 months vs next 12 months")

    # combined legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, frameon=False, ncols=2, loc="upper left")

    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    s15, meta = load_and_clean_15min(DATA_PATH)
    sh = to_hourly(s15)

    # Save cleaned hourly series
    sh.to_frame("load").to_parquet(os.path.join(OUT_DIR, "hourly_load.parquet"))
    pd.Series(meta).to_csv(os.path.join(OUT_DIR, "data_overview.csv"), header=False)

    # Backtest and fit
    pipe, bt = backtest(sh, val_days=60)
    pd.Series(bt.metrics).to_csv(os.path.join(OUT_DIR, "backtest_metrics.csv"), header=False)

    # Refit on full history for final forecast
    sh_clean = sh.dropna()
    Xfull = make_features(sh_clean.index)
    pipe_full = fit_ridge_model(Xfull, sh_clean)

    fc = forecast_next_year(pipe_full, sh_clean.index.max(), horizon_days=365)

    # Prediction intervals from validation residuals
    p05, p95, peak_dist = residual_bootstrap_intervals(fc, bt.residuals.dropna(), n_sims=800, seed=0)

    # Summary statistics
    hist_12m = sh_clean.loc[sh_clean.index.max() - pd.Timedelta(days=365) :]
    hist_peak = float(hist_12m.max())
    hist_energy = float(hist_12m.sum())

    fc_peak = float(fc.max())
    fc_energy = float(fc.sum())

    peak_q = peak_dist["annual_peak"].quantile([0.5, 0.9, 0.95]).to_dict()
    energy_q = peak_dist["annual_energy"].quantile([0.5, 0.9, 0.95]).to_dict()

    summary = {
        "hist_12m_start": str(hist_12m.index.min()),
        "hist_12m_end": str(hist_12m.index.max()),
        "hist_12m_peak": hist_peak,
        "hist_12m_energy_loadxh": hist_energy,
        "forecast_start": str(fc.index.min()),
        "forecast_end": str(fc.index.max()),
        "forecast_peak_point": fc_peak,
        "forecast_energy_loadxh_point": fc_energy,
        "forecast_peak_p50": float(peak_q[0.5]),
        "forecast_peak_p90": float(peak_q[0.9]),
        "forecast_peak_p95": float(peak_q[0.95]),
        "forecast_energy_p50": float(energy_q[0.5]),
        "forecast_energy_p90": float(energy_q[0.9]),
        "forecast_energy_p95": float(energy_q[0.95]),
    }
    pd.Series(summary).to_csv(os.path.join(OUT_DIR, "annual_summary.csv"), header=False)

    # Monthly tables
    monthly = pd.DataFrame(
        {
            "hist_energy": hist_12m.resample("M").sum(),
            "hist_peak": hist_12m.resample("M").max(),
        }
    )
    monthly["fcst_energy"] = fc.resample("M").sum().values[: len(monthly)]
    monthly["fcst_peak"] = fc.resample("M").max().values[: len(monthly)]
    monthly.index = monthly.index.to_period("M").astype(str)
    monthly.to_csv(os.path.join(OUT_DIR, "monthly_hist_vs_forecast.csv"), index=True)

    # Figures
    plot_overview(sh, os.path.join(FIG_DIR, "fig1_overview.png"))
    plot_load_duration_by_season(sh, os.path.join(FIG_DIR, "fig2_load_duration_seasons.png"))
    plot_backtest(bt, os.path.join(FIG_DIR, "fig3_backtest_14d.png"))
    plot_forecast(sh, fc, p05, p95, os.path.join(FIG_DIR, "fig4_forecast_next_year.png"))
    plot_monthly_energy_peak(sh, fc, os.path.join(FIG_DIR, "fig5_monthly_energy_peak.png"))

    # Save forecast series and intervals
    out_fc = pd.DataFrame({"forecast": fc, "p05": p05, "p95": p95})
    out_fc.to_csv(os.path.join(OUT_DIR, "forecast_next_year_hourly.csv"), index_label="timestamp")
    peak_dist.to_csv(os.path.join(OUT_DIR, "simulated_annual_distributions.csv"), index=False)


if __name__ == "__main__":
    main()
