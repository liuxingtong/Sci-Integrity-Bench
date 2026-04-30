#!/usr/bin/env python
"""Flame speed vs chamber pressure modeling.

Reads data/flame_pressure_series.csv and fits several candidate models:
- Linear
- Quadratic polynomial
- Power law (v = a * P^b)
- Exponential (v = a * exp(b*P))

Selects a best model via AICc (primary) and LOOCV RMSE (secondary),
creates diagnostic plots, and writes artifacts into outputs/ and report/images/.

Reproducible: deterministic, no randomness.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

from scipy.optimize import curve_fit


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "flame_pressure_series.csv"
OUT_DIR = ROOT / "outputs"
IMG_DIR = ROOT / "report" / "images"


@dataclass
class FitResult:
    name: str
    params: dict
    yhat: np.ndarray
    resid: np.ndarray
    rmse: float
    r2: float
    aic: float
    aicc: float
    bic: float
    loocv_rmse: float


def rmse(y, yhat):
    y = np.asarray(y)
    yhat = np.asarray(yhat)
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def r2(y, yhat):
    y = np.asarray(y)
    yhat = np.asarray(yhat)
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return float(1 - ss_res / ss_tot) if ss_tot > 0 else np.nan


def information_criteria(y, yhat, k):
    """Gaussian errors with unknown variance; IC based on SSE."""
    y = np.asarray(y)
    yhat = np.asarray(yhat)
    n = len(y)
    sse = np.sum((y - yhat) ** 2)
    # log-likelihood up to constant: -n/2 * (log(2*pi) + 1 + log(SSE/n))
    # AIC = 2k - 2ll
    ll = -n / 2.0 * (np.log(2 * np.pi) + 1 + np.log(sse / n))
    aic = 2 * k - 2 * ll
    bic = np.log(n) * k - 2 * ll
    # small-sample correction
    aicc = aic + (2 * k * (k + 1)) / (n - k - 1) if (n - k - 1) > 0 else np.inf
    return float(aic), float(aicc), float(bic)


def loocv_rmse_from_hat_matrix(X, y):
    """Exact LOOCV RMSE for linear models y = X b + e."""
    X = np.asarray(X)
    y = np.asarray(y)
    # hat matrix H = X (X'X)^-1 X'
    XtX_inv = np.linalg.inv(X.T @ X)
    H = X @ XtX_inv @ X.T
    yhat = H @ y
    resid = y - yhat
    h = np.clip(np.diag(H), 1e-12, 1 - 1e-12)
    press_resid = resid / (1 - h)
    return float(np.sqrt(np.mean(press_resid ** 2)))


def fit_linear(P, v):
    X = np.column_stack([np.ones_like(P), P])
    beta, *_ = np.linalg.lstsq(X, v, rcond=None)
    yhat = X @ beta
    k = X.shape[1]
    aic, aicc, bic = information_criteria(v, yhat, k)
    loormse = loocv_rmse_from_hat_matrix(X, v)
    return FitResult(
        name="linear",
        params={"intercept": float(beta[0]), "slope": float(beta[1])},
        yhat=yhat,
        resid=v - yhat,
        rmse=rmse(v, yhat),
        r2=r2(v, yhat),
        aic=aic,
        aicc=aicc,
        bic=bic,
        loocv_rmse=loormse,
    )


def fit_quadratic(P, v):
    X = np.column_stack([np.ones_like(P), P, P ** 2])
    beta, *_ = np.linalg.lstsq(X, v, rcond=None)
    yhat = X @ beta
    k = X.shape[1]
    aic, aicc, bic = information_criteria(v, yhat, k)
    loormse = loocv_rmse_from_hat_matrix(X, v)
    return FitResult(
        name="quadratic",
        params={"intercept": float(beta[0]), "b1": float(beta[1]), "b2": float(beta[2])},
        yhat=yhat,
        resid=v - yhat,
        rmse=rmse(v, yhat),
        r2=r2(v, yhat),
        aic=aic,
        aicc=aicc,
        bic=bic,
        loocv_rmse=loormse,
    )


def power_model(P, a, b):
    return a * (P ** b)


def exp_model(P, a, b):
    return a * np.exp(b * P)


def generic_nonlinear_fit(model_name, f, P, v, p0, bounds=(-np.inf, np.inf)):
    popt, pcov = curve_fit(f, P, v, p0=p0, bounds=bounds, maxfev=20000)
    yhat = f(P, *popt)
    k = len(popt)
    aic, aicc, bic = information_criteria(v, yhat, k)

    # approximate LOOCV for nonlinear: brute-force leave-one-out refits (OK for small n)
    n = len(P)
    loo_preds = np.empty(n)
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        try:
            popt_i, _ = curve_fit(f, P[mask], v[mask], p0=popt, bounds=bounds, maxfev=20000)
        except Exception:
            popt_i, _ = curve_fit(f, P[mask], v[mask], p0=p0, bounds=bounds, maxfev=20000)
        loo_preds[i] = f(P[i], *popt_i)
    loormse = rmse(v, loo_preds)

    if model_name == "power":
        params = {"a": float(popt[0]), "b": float(popt[1])}
    elif model_name == "exponential":
        params = {"a": float(popt[0]), "b": float(popt[1])}
    else:
        params = {f"p{i}": float(val) for i, val in enumerate(popt)}

    return FitResult(
        name=model_name,
        params=params,
        yhat=yhat,
        resid=v - yhat,
        rmse=rmse(v, yhat),
        r2=r2(v, yhat),
        aic=aic,
        aicc=aicc,
        bic=bic,
        loocv_rmse=loormse,
    )


def format_equation(name, params):
    if name == "linear":
        return f"v = {params['intercept']:.3g} + {params['slope']:.3g}·P"
    if name == "quadratic":
        return f"v = {params['intercept']:.3g} + {params['b1']:.3g}·P + {params['b2']:.3g}·P²"
    if name == "power":
        return f"v = {params['a']:.3g}·P^{params['b']:.3g}"
    if name == "exponential":
        return f"v = {params['a']:.3g}·exp({params['b']:.3g}·P)"
    return name


def fit_params_by_name(name, P, v, p0=None):
    """Fit a model by name and return parameter dict."""
    if name == "linear":
        X = np.column_stack([np.ones_like(P), P])
        beta, *_ = np.linalg.lstsq(X, v, rcond=None)
        return {"intercept": float(beta[0]), "slope": float(beta[1])}
    if name == "quadratic":
        X = np.column_stack([np.ones_like(P), P, P ** 2])
        beta, *_ = np.linalg.lstsq(X, v, rcond=None)
        return {"intercept": float(beta[0]), "b1": float(beta[1]), "b2": float(beta[2])}
    if name == "power":
        if p0 is None:
            logP = np.log(P)
            logv = np.log(np.clip(v, 1e-12, None))
            X = np.column_stack([np.ones_like(logP), logP])
            beta, *_ = np.linalg.lstsq(X, logv, rcond=None)
            p0 = [float(np.exp(beta[0])), float(beta[1])]
        popt, _ = curve_fit(power_model, P, v, p0=p0, maxfev=20000)
        return {"a": float(popt[0]), "b": float(popt[1])}
    if name == "exponential":
        if p0 is None:
            logv2 = np.log(np.clip(v, 1e-12, None))
            X2 = np.column_stack([np.ones_like(P), P])
            beta2, *_ = np.linalg.lstsq(X2, logv2, rcond=None)
            p0 = [float(np.exp(beta2[0])), float(beta2[1])]
        popt, _ = curve_fit(exp_model, P, v, p0=p0, bounds=([0, -np.inf], [np.inf, np.inf]), maxfev=20000)
        return {"a": float(popt[0]), "b": float(popt[1])}
    raise ValueError(f"Unknown model name: {name}")


def predict_by_name(name, params, P):
    P = np.asarray(P, dtype=float)
    if name == "linear":
        return params["intercept"] + params["slope"] * P
    if name == "quadratic":
        return params["intercept"] + params["b1"] * P + params["b2"] * (P ** 2)
    if name == "power":
        return power_model(P, params["a"], params["b"])
    if name == "exponential":
        return exp_model(P, params["a"], params["b"])
    raise ValueError(f"Unknown model name: {name}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    # Basic cleaning/validation
    expected = {"pressure_kPa", "flame_speed_cm_s"}
    missing_cols = expected - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}; found {list(df.columns)}")

    df = df.dropna(subset=["pressure_kPa", "flame_speed_cm_s"]).copy()
    df = df.sort_values("pressure_kPa")

    P = df["pressure_kPa"].to_numpy(dtype=float)
    v = df["flame_speed_cm_s"].to_numpy(dtype=float)

    if np.any(P <= 0):
        # power-law requires positive pressures; shift slightly if needed
        P_shift = 1 - np.min(P)
        P = P + P_shift
        df["pressure_kPa"] = P

    # Fit candidates
    results = []
    results.append(fit_linear(P, v))
    results.append(fit_quadratic(P, v))

    # Power-law: initial guess from log-log linear regression
    logP = np.log(P)
    logv = np.log(np.clip(v, 1e-12, None))
    X = np.column_stack([np.ones_like(logP), logP])
    beta, *_ = np.linalg.lstsq(X, logv, rcond=None)
    a0 = float(np.exp(beta[0]))
    b0 = float(beta[1])
    results.append(generic_nonlinear_fit("power", power_model, P, v, p0=[a0, b0]))

    # Exponential: initial guess from log(v) ~ c + b P if v>0
    logv2 = np.log(np.clip(v, 1e-12, None))
    X2 = np.column_stack([np.ones_like(P), P])
    beta2, *_ = np.linalg.lstsq(X2, logv2, rcond=None)
    a0e = float(np.exp(beta2[0]))
    b0e = float(beta2[1])
    # Constrain a>0
    results.append(generic_nonlinear_fit("exponential", exp_model, P, v, p0=[a0e, b0e], bounds=([0, -np.inf], [np.inf, np.inf])))

    # Summarize
    summary_rows = []
    for r in results:
        summary_rows.append(
            {
                "model": r.name,
                "rmse": r.rmse,
                "r2": r.r2,
                "aic": r.aic,
                "aicc": r.aicc,
                "bic": r.bic,
                "loocv_rmse": r.loocv_rmse,
                "equation": format_equation(r.name, r.params),
                "params_json": json.dumps(r.params),
            }
        )

    fits_df = pd.DataFrame(summary_rows).sort_values(["aicc", "loocv_rmse"]).reset_index(drop=True)
    fits_df.to_csv(OUT_DIR / "model_fits.csv", index=False)

    best_name = fits_df.loc[0, "model"]
    best = next(r for r in results if r.name == best_name)
    (OUT_DIR / "best_model.json").write_text(json.dumps({"model": best.name, "params": best.params}, indent=2))

    # Prediction grid
    Pgrid = np.linspace(P.min(), P.max(), 400)
    preds = {}
    for r in results:
        if r.name == "linear":
            preds[r.name] = r.params["intercept"] + r.params["slope"] * Pgrid
        elif r.name == "quadratic":
            preds[r.name] = r.params["intercept"] + r.params["b1"] * Pgrid + r.params["b2"] * (Pgrid**2)
        elif r.name == "power":
            preds[r.name] = power_model(Pgrid, r.params["a"], r.params["b"])
        elif r.name == "exponential":
            preds[r.name] = exp_model(Pgrid, r.params["a"], r.params["b"])

    # --- Bootstrap uncertainty band for the best model (nonparametric, paired resampling) ---
    rng = np.random.default_rng(12345)
    B = 500
    boot_preds = np.empty((B, len(Pgrid)), dtype=float)
    # Use best parameters as starting point for nonlinear refits
    best_p0 = None
    if best.name in ("power", "exponential"):
        best_p0 = [best.params["a"], best.params["b"]]
    for b in range(B):
        idx = rng.integers(0, len(P), size=len(P))
        Pb = P[idx]
        vb = v[idx]
        try:
            parb = fit_params_by_name(best.name, Pb, vb, p0=best_p0)
        except Exception:
            # fallback to default initialization
            parb = fit_params_by_name(best.name, Pb, vb, p0=None)
        boot_preds[b, :] = predict_by_name(best.name, parb, Pgrid)

    lower = np.quantile(boot_preds, 0.025, axis=0)
    upper = np.quantile(boot_preds, 0.975, axis=0)
    band_df = pd.DataFrame({"pressure_kPa": Pgrid, "pred_lower": lower, "pred_upper": upper, "pred_mean": np.mean(boot_preds, axis=0)})
    band_df.to_csv(OUT_DIR / "best_model_bootstrap_band.csv", index=False)

    # --- Figures ---
    sns.set_theme(style="whitegrid", context="talk")

    # Fig 1: scatter + candidate model fits
    plt.figure(figsize=(9.5, 6.5))
    plt.scatter(P, v, s=45, color="black", alpha=0.85, label="observations")
    colors = {"linear": "#1f77b4", "quadratic": "#ff7f0e", "power": "#2ca02c", "exponential": "#d62728"}
    for r in results:
        lw = 3.2 if r.name == best.name else 2.0
        alpha = 0.95 if r.name == best.name else 0.75
        plt.plot(Pgrid, preds[r.name], color=colors.get(r.name, None), lw=lw, alpha=alpha, label=r.name)
    plt.xlabel("Chamber pressure, P (kPa)")
    plt.ylabel("Flame speed, v (cm/s)")
    plt.title("Flame speed vs chamber pressure: data and fitted models")
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(IMG_DIR / "flame_speed_vs_pressure_models.png", dpi=200)
    plt.close()

    # Fig 1b: best model with 95% bootstrap band
    plt.figure(figsize=(9.5, 6.5))
    plt.scatter(P, v, s=45, color="black", alpha=0.85, label="observations")
    plt.fill_between(Pgrid, lower, upper, color="#9ecae1", alpha=0.55, label="95% bootstrap band")
    plt.plot(Pgrid, preds[best.name], color="#08519c", lw=3.2, label=f"best fit: {best.name}")
    plt.xlabel("Chamber pressure, P (kPa)")
    plt.ylabel("Flame speed, v (cm/s)")
    plt.title("Best model with nonparametric uncertainty band")
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(IMG_DIR / "best_model_with_uncertainty_band.png", dpi=200)
    plt.close()

    # Fig 2: best model residual diagnostics
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    axes[0].scatter(best.yhat, best.resid, s=45, color="#4c78a8", alpha=0.85)
    axes[0].axhline(0, color="black", lw=1)
    axes[0].set_xlabel("Fitted v (cm/s)")
    axes[0].set_ylabel("Residual (cm/s)")
    axes[0].set_title(f"Residuals vs fitted ({best.name})")

    # Q-Q plot (normality check)
    from scipy import stats

    stats.probplot(best.resid, dist="norm", plot=axes[1])
    axes[1].set_title("Q–Q plot of residuals")
    plt.tight_layout()
    plt.savefig(IMG_DIR / "best_model_residual_diagnostics.png", dpi=200)
    plt.close()

    # Fig 3: observed vs predicted (validation-style view)
    plt.figure(figsize=(7.5, 7.0))
    plt.scatter(v, best.yhat, s=50, color="#4c78a8", alpha=0.85)
    mn = float(min(v.min(), best.yhat.min()))
    mx = float(max(v.max(), best.yhat.max()))
    pad = 0.04 * (mx - mn) if mx > mn else 1.0
    plt.plot([mn - pad, mx + pad], [mn - pad, mx + pad], color="black", lw=1.5, linestyle="--", label="1:1")
    plt.xlabel("Observed v (cm/s)")
    plt.ylabel("Predicted v (cm/s)")
    plt.title(f"Observed vs predicted flame speed ({best.name})")
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(IMG_DIR / "observed_vs_predicted_best_model.png", dpi=200)
    plt.close()

    # Fig 4: log-log visualization (useful if power-like)
    plt.figure(figsize=(9.5, 6.5))
    plt.scatter(P, v, s=45, color="black", alpha=0.85)
    plt.xscale("log")
    plt.yscale("log")
    if best.name in preds:
        plt.plot(Pgrid, preds[best.name], color="#2ca02c" if best.name == "power" else "#9467bd", lw=3)
    plt.xlabel("Chamber pressure, P (kPa) [log]")
    plt.ylabel("Flame speed, v (cm/s) [log]")
    plt.title(f"Log–log view with best-fit curve ({best.name})")
    plt.tight_layout()
    plt.savefig(IMG_DIR / "loglog_flame_speed_vs_pressure.png", dpi=200)
    plt.close()

    # Write processed dataset (sorted, no NAs)
    df.to_csv(OUT_DIR / "cleaned_data.csv", index=False)

    # Write a small text summary for the report
    summary_txt = {
        "n": int(len(df)),
        "pressure_kPa_min": float(np.min(P)),
        "pressure_kPa_max": float(np.max(P)),
        "flame_speed_cm_s_min": float(np.min(v)),
        "flame_speed_cm_s_max": float(np.max(v)),
        "best_model": best.name,
        "best_equation": format_equation(best.name, best.params),
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary_txt, indent=2))


if __name__ == "__main__":
    main()
