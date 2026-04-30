#!/usr/bin/env python
"""Model flame speed as a function of chamber pressure.

Reads:  data/flame_pressure_series.csv
Writes: outputs/model_comparison.csv
        outputs/best_model_params.json
        report/images/*.png

The script fits several candidate relationships and compares them using
cross-validated RMSE and AIC (Gaussian errors on original y-scale).

Author: autonomous research agent
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

from scipy.optimize import curve_fit


DATA_PATH = Path("data/flame_pressure_series.csv")
OUT_DIR = Path("outputs")
FIG_DIR = Path("report/images")


@dataclass
class FitResult:
    model: str
    n: int
    k: int
    rss: float
    rmse: float
    aic: float
    cv_rmse: float
    params: dict


def aic_from_rss(rss: float, n: int, k: int) -> float:
    """AIC for Gaussian errors with MLE sigma^2 = RSS/n."""
    rss = max(rss, 1e-12)
    return n * np.log(rss / n) + 2 * k


def rmse(y_true, y_pred) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def loocv_rmse(x: np.ndarray, y: np.ndarray, fit_predict_func) -> float:
    """Leave-one-out CV RMSE; fit_predict_func(x_train,y_train,x_test)->y_hat."""
    n = len(y)
    preds = np.empty(n)
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        preds[i] = fit_predict_func(x[mask], y[mask], x[i])
    return rmse(y, preds)


# --- candidate model forms (original scale) ---

def f_linear(p, a, b):
    return a + b * p


def f_quadratic(p, a, b, c):
    return a + b * p + c * p**2


def f_power(p, a, b):
    # a * p^b, a>0
    return a * np.power(p, b)


def f_exponential(p, a, b):
    # a * exp(b*p)
    return a * np.exp(b * p)


def robust_curve_fit(func, x, y, p0=None, bounds=(-np.inf, np.inf)):
    """curve_fit with mild robustness: retries with heuristics."""
    try:
        popt, pcov = curve_fit(func, x, y, p0=p0, bounds=bounds, maxfev=200000)
        return popt, pcov
    except Exception:
        # basic fallback initializations
        if func is f_linear:
            p0 = (np.median(y), 0.0)
        elif func is f_quadratic:
            p0 = (np.median(y), 0.0, 0.0)
        elif func is f_power:
            # log-log slope
            eps = 1e-9
            lx = np.log(np.maximum(x, eps))
            ly = np.log(np.maximum(y, eps))
            b = np.polyfit(lx, ly, 1)[0]
            a = np.exp(np.mean(ly - b * lx))
            p0 = (max(a, eps), b)
        elif func is f_exponential:
            eps = 1e-9
            # log(y)=log(a)+b*p
            b = np.polyfit(x, np.log(np.maximum(y, eps)), 1)[0]
            a = np.exp(np.mean(np.log(np.maximum(y, eps)) - b * x))
            p0 = (max(a, eps), b)
        popt, pcov = curve_fit(func, x, y, p0=p0, bounds=bounds, maxfev=200000)
        return popt, pcov


def fit_and_score_models(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    x = df["pressure_kPa"].to_numpy(dtype=float)
    y = df["flame_speed_cm_s"].to_numpy(dtype=float)
    n = len(df)

    results: list[FitResult] = []

    # linear
    popt, pcov = robust_curve_fit(f_linear, x, y)
    yhat = f_linear(x, *popt)
    rss = float(np.sum((y - yhat) ** 2))
    k = 2

    def pred_linear(xtr, ytr, xtest):
        p, _ = robust_curve_fit(f_linear, xtr, ytr)
        return float(f_linear(xtest, *p))

    results.append(
        FitResult(
            model="linear",
            n=n,
            k=k,
            rss=rss,
            rmse=rmse(y, yhat),
            aic=aic_from_rss(rss, n, k),
            cv_rmse=loocv_rmse(x, y, pred_linear),
            params={"a": float(popt[0]), "b": float(popt[1])},
        )
    )

    # quadratic
    popt, pcov = robust_curve_fit(f_quadratic, x, y)
    yhat = f_quadratic(x, *popt)
    rss = float(np.sum((y - yhat) ** 2))
    k = 3

    def pred_quad(xtr, ytr, xtest):
        p, _ = robust_curve_fit(f_quadratic, xtr, ytr)
        return float(f_quadratic(xtest, *p))

    results.append(
        FitResult(
            model="quadratic",
            n=n,
            k=k,
            rss=rss,
            rmse=rmse(y, yhat),
            aic=aic_from_rss(rss, n, k),
            cv_rmse=loocv_rmse(x, y, pred_quad),
            params={"a": float(popt[0]), "b": float(popt[1]), "c": float(popt[2])},
        )
    )

    # power law (restrict a>0)
    # p must be positive; if not, shift? Here we drop non-positive pressures.
    if np.any(x <= 0):
        mask = x > 0
        x_pos, y_pos = x[mask], y[mask]
    else:
        x_pos, y_pos = x, y

    popt, pcov = robust_curve_fit(f_power, x_pos, y_pos, bounds=([0, -np.inf], [np.inf, np.inf]))
    yhat = f_power(x, *popt)
    rss = float(np.sum((y - yhat) ** 2))
    k = 2

    def pred_power(xtr, ytr, xtest):
        # require positive pressures
        mask = xtr > 0
        p, _ = robust_curve_fit(
            f_power,
            xtr[mask],
            ytr[mask],
            bounds=([0, -np.inf], [np.inf, np.inf]),
        )
        return float(f_power(xtest, *p))

    results.append(
        FitResult(
            model="power",
            n=n,
            k=k,
            rss=rss,
            rmse=rmse(y, yhat),
            aic=aic_from_rss(rss, n, k),
            cv_rmse=loocv_rmse(x, y, pred_power),
            params={"a": float(popt[0]), "b": float(popt[1])},
        )
    )

    # exponential (a>0)
    popt, pcov = robust_curve_fit(f_exponential, x, y, bounds=([0, -np.inf], [np.inf, np.inf]))
    yhat = f_exponential(x, *popt)
    rss = float(np.sum((y - yhat) ** 2))
    k = 2

    def pred_exp(xtr, ytr, xtest):
        p, _ = robust_curve_fit(f_exponential, xtr, ytr, bounds=([0, -np.inf], [np.inf, np.inf]))
        return float(f_exponential(xtest, *p))

    results.append(
        FitResult(
            model="exponential",
            n=n,
            k=k,
            rss=rss,
            rmse=rmse(y, yhat),
            aic=aic_from_rss(rss, n, k),
            cv_rmse=loocv_rmse(x, y, pred_exp),
            params={"a": float(popt[0]), "b": float(popt[1])},
        )
    )

    res_df = pd.DataFrame([asdict(r) for r in results]).sort_values(["cv_rmse", "aic"], ascending=[True, True])

    best_model = res_df.iloc[0]["model"]
    best_params = res_df.iloc[0]["params"]

    return res_df, {"best_model": best_model, "best_params": best_params}


def predict(model: str, p: np.ndarray, params: dict) -> np.ndarray:
    if model == "linear":
        return f_linear(p, params["a"], params["b"])
    if model == "quadratic":
        return f_quadratic(p, params["a"], params["b"], params["c"])
    if model == "power":
        return f_power(p, params["a"], params["b"])
    if model == "exponential":
        return f_exponential(p, params["a"], params["b"])
    raise ValueError(f"Unknown model: {model}")


def bootstrap_ci(df: pd.DataFrame, model: str, n_boot: int = 2000, seed: int = 0) -> dict:
    """Nonparametric bootstrap for parameters and prediction band."""
    rng = np.random.default_rng(seed)
    x = df["pressure_kPa"].to_numpy(float)
    y = df["flame_speed_cm_s"].to_numpy(float)
    n = len(df)

    p_grid = np.linspace(x.min(), x.max(), 200)

    # choose function and bounds
    if model == "linear":
        func = f_linear
        bounds = (-np.inf, np.inf)
        k = 2
        p0 = None
        param_names = ["a", "b"]
    elif model == "quadratic":
        func = f_quadratic
        bounds = (-np.inf, np.inf)
        k = 3
        p0 = None
        param_names = ["a", "b", "c"]
    elif model == "power":
        func = f_power
        bounds = ([0, -np.inf], [np.inf, np.inf])
        k = 2
        p0 = None
        param_names = ["a", "b"]
    elif model == "exponential":
        func = f_exponential
        bounds = ([0, -np.inf], [np.inf, np.inf])
        k = 2
        p0 = None
        param_names = ["a", "b"]
    else:
        raise ValueError(model)

    params_boot = []
    preds_boot = []

    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        xb = x[idx]
        yb = y[idx]
        try:
            popt, _ = robust_curve_fit(func, xb, yb, p0=p0, bounds=bounds)
            params_boot.append(popt)
            preds_boot.append(func(p_grid, *popt))
        except Exception:
            continue

    params_boot = np.asarray(params_boot)
    preds_boot = np.asarray(preds_boot)

    ci = {}
    for j, name in enumerate(param_names):
        ci[name] = {
            "median": float(np.median(params_boot[:, j])),
            "ci95_low": float(np.quantile(params_boot[:, j], 0.025)),
            "ci95_high": float(np.quantile(params_boot[:, j], 0.975)),
        }

    pred_ci = {
        "p_grid": p_grid.tolist(),
        "pred_median": np.median(preds_boot, axis=0).tolist(),
        "pred_ci95_low": np.quantile(preds_boot, 0.025, axis=0).tolist(),
        "pred_ci95_high": np.quantile(preds_boot, 0.975, axis=0).tolist(),
    }

    return {"param_ci": ci, "pred_ci": pred_ci}


def make_figures(df: pd.DataFrame, model_comp: pd.DataFrame, best: dict, boot: dict):
    sns.set_theme(style="whitegrid", context="talk")
    x = df["pressure_kPa"].to_numpy(float)
    y = df["flame_speed_cm_s"].to_numpy(float)

    # Figure 1: scatter with best-fit curve + bootstrap band
    p_grid = np.array(boot["pred_ci"]["p_grid"], dtype=float)
    y_med = np.array(boot["pred_ci"]["pred_median"], dtype=float)
    y_lo = np.array(boot["pred_ci"]["pred_ci95_low"], dtype=float)
    y_hi = np.array(boot["pred_ci"]["pred_ci95_high"], dtype=float)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(x, y, s=55, alpha=0.85, label="observations")
    ax.plot(p_grid, y_med, color="C1", lw=2.5, label=f"{best['best_model']} fit (bootstrap median)")
    ax.fill_between(p_grid, y_lo, y_hi, color="C1", alpha=0.25, label="95% bootstrap band")
    ax.set_xlabel("Chamber pressure (kPa)")
    ax.set_ylabel("Flame speed (cm/s)")
    ax.set_title("Flame speed vs chamber pressure")
    ax.legend(frameon=True)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "flame_speed_vs_pressure_bestfit.png", dpi=200)
    plt.close(fig)

    # Figure 2: model comparison (CV RMSE + AIC)
    comp = model_comp.copy()
    comp["cv_rmse"] = comp["cv_rmse"].astype(float)
    comp["aic"] = comp["aic"].astype(float)

    fig, ax1 = plt.subplots(figsize=(10, 6))
    order = comp.sort_values("cv_rmse")["model"].tolist()
    sns.barplot(data=comp, x="model", y="cv_rmse", order=order, ax=ax1, color="C0")
    ax1.set_ylabel("LOOCV RMSE (cm/s)")
    ax1.set_xlabel("Model")
    ax1.set_title("Model comparison")

    ax2 = ax1.twinx()
    ax2.plot(order, comp.set_index("model").loc[order, "aic"], color="C3", marker="o", lw=2)
    ax2.set_ylabel("AIC (lower is better)")

    fig.tight_layout()
    fig.savefig(FIG_DIR / "model_comparison.png", dpi=200)
    plt.close(fig)

    # Figure 3: residuals vs fitted for best model
    yhat = predict(best["best_model"], x, best["best_params"])
    resid = y - yhat

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(yhat, resid, s=55, alpha=0.85)
    ax.axhline(0, color="k", lw=1)
    ax.set_xlabel("Fitted flame speed (cm/s)")
    ax.set_ylabel("Residual (observed - fitted) (cm/s)")
    ax.set_title(f"Residual diagnostic: {best['best_model']} model")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "residuals_best_model.png", dpi=200)
    plt.close(fig)

    # Figure 4: distribution / qq-plot like check (hist + kde)
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.histplot(resid, kde=True, ax=ax, color="0.3")
    ax.set_xlabel("Residual (cm/s)")
    ax.set_ylabel("Count")
    ax.set_title("Residual distribution")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "residual_distribution.png", dpi=200)
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)

    # basic validation
    required = {"pressure_kPa", "flame_speed_cm_s"}
    missing_cols = required - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    # coerce numeric and drop NaN
    df = df.copy()
    df["pressure_kPa"] = pd.to_numeric(df["pressure_kPa"], errors="coerce")
    df["flame_speed_cm_s"] = pd.to_numeric(df["flame_speed_cm_s"], errors="coerce")
    df = df.dropna().sort_values("pressure_kPa").reset_index(drop=True)

    model_comp, best = fit_and_score_models(df)

    # bootstrap uncertainty for best model
    boot = bootstrap_ci(df, best["best_model"], n_boot=3000, seed=42)

    model_comp.to_csv(OUT_DIR / "model_comparison.csv", index=False)
    with open(OUT_DIR / "best_model_params.json", "w") as f:
        json.dump({"best": best, "bootstrap": boot["param_ci"]}, f, indent=2)

    # make figures
    make_figures(df, model_comp, best, boot)

    # save a compact data overview
    overview = {
        "n": int(len(df)),
        "pressure_kPa": {
            "min": float(df["pressure_kPa"].min()),
            "max": float(df["pressure_kPa"].max()),
            "mean": float(df["pressure_kPa"].mean()),
        },
        "flame_speed_cm_s": {
            "min": float(df["flame_speed_cm_s"].min()),
            "max": float(df["flame_speed_cm_s"].max()),
            "mean": float(df["flame_speed_cm_s"].mean()),
        },
    }
    with open(OUT_DIR / "data_overview.json", "w") as f:
        json.dump(overview, f, indent=2)


if __name__ == "__main__":
    main()
