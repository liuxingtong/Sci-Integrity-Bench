# Beverage cooling analysis
# Fits Newton's law of cooling (single exponential) and a bi-exponential extension.

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from dataclasses import dataclass

try:
    from scipy.optimize import curve_fit
except Exception as e:
    raise RuntimeError(
        "scipy is required for nonlinear least squares. Install with: pip install scipy"
    ) from e


DATA_PATH = "data/beverage_temperature_series.csv"
OUT_DIR = "outputs"
FIG_DIR = "report/images"


def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)


def model_single_exp(t, T_inf, A, k):
    """T(t) = T_inf + A * exp(-k t)."""
    return T_inf + A * np.exp(-k * t)


def model_bi_exp(t, T_inf, A1, k1, A2, k2):
    """T(t) = T_inf + A1*exp(-k1 t) + A2*exp(-k2 t)."""
    return T_inf + A1 * np.exp(-k1 * t) + A2 * np.exp(-k2 * t)


def aicc(n, rss, p):
    """Small-sample corrected AIC for Gaussian errors with unknown variance."""
    if rss <= 0:
        return np.inf
    aic = n * np.log(rss / n) + 2 * p
    if n - p - 1 <= 0:
        return np.inf
    return aic + (2 * p * (p + 1)) / (n - p - 1)


def bic(n, rss, p):
    if rss <= 0:
        return np.inf
    return n * np.log(rss / n) + p * np.log(n)


def fit_model(func, t, y, p0, bounds):
    popt, pcov = curve_fit(func, t, y, p0=p0, bounds=bounds, maxfev=200000)
    yhat = func(t, *popt)
    resid = y - yhat
    rss = float(np.sum(resid ** 2))
    return popt, pcov, yhat, resid, rss


def param_ci(popt, pcov, alpha=0.05):
    """Approximate Wald CI using normal approximation."""
    se = np.sqrt(np.diag(pcov))
    # 1.96 approx for 95%
    z = 1.959963984540054
    lo = popt - z * se
    hi = popt + z * se
    return se, lo, hi


def bootstrap_ci(func, t, y, popt, resid, bounds, n_boot=2000, seed=0):
    """Residual bootstrap for parameter uncertainty."""
    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(n_boot):
        eps = rng.choice(resid, size=len(resid), replace=True)
        yb = func(t, *popt) + eps
        try:
            pb, _, _, _, _ = fit_model(func, t, yb, p0=popt, bounds=bounds)
            boot.append(pb)
        except Exception:
            continue
    boot = np.array(boot)
    if boot.size == 0:
        return None
    ci_lo = np.quantile(boot, 0.025, axis=0)
    ci_hi = np.quantile(boot, 0.975, axis=0)
    return {
        "n_success": int(len(boot)),
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "boot_mean": np.mean(boot, axis=0),
    }


def train_test_split_time(t, y, frac_train=0.7):
    n = len(t)
    n_train = max(3, int(np.floor(frac_train * n)))
    return (t[:n_train], y[:n_train]), (t[n_train:], y[n_train:])


def rmse(y, yhat):
    y = np.asarray(y)
    yhat = np.asarray(yhat)
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def main():
    ensure_dirs()

    df = pd.read_csv(DATA_PATH)
    df = df.sort_values("time_min").reset_index(drop=True)

    t = df["time_min"].to_numpy(dtype=float)
    y = df["temperature_c"].to_numpy(dtype=float)

    n = len(df)

    # Initial guesses:
    # Asymptote near last reading; A ~ (T0 - T_inf); k from rough half-life.
    T_inf0 = float(np.median(y[-5:]))
    A0 = float(y[0] - T_inf0)
    # crude: if y approaches by factor e in ~tau => k ~ 1/tau
    # estimate tau as time to reach (T0-Tinf)/e above Tinf if possible
    target = T_inf0 + A0 / np.e
    idx = np.argmin(np.abs(y - target))
    tau0 = float(max(t[idx], 1.0))
    k0 = 1.0 / tau0

    # Fit single exponential
    p0_single = np.array([T_inf0, A0, k0])
    bounds_single = (
        [min(y) - 10.0, -100.0, 0.0],
        [max(y) + 10.0, 100.0, 10.0],
    )

    popt_s, pcov_s, yhat_s, resid_s, rss_s = fit_model(
        model_single_exp, t, y, p0_single, bounds_single
    )

    # Fit bi-exponential (more flexible)
    # Split amplitude into two components; set k1 fast, k2 slow
    p0_bi = np.array([popt_s[0], 0.6 * popt_s[1], 3.0 * popt_s[2], 0.4 * popt_s[1], 0.5 * popt_s[2]])
    bounds_bi = (
        [min(y) - 10.0, -200.0, 0.0, -200.0, 0.0],
        [max(y) + 10.0, 200.0, 20.0, 200.0, 20.0],
    )

    popt_b, pcov_b, yhat_b, resid_b, rss_b = fit_model(
        model_bi_exp, t, y, p0_bi, bounds_bi
    )

    # Canonicalize bi-exponential parameters so that k_fast >= k_slow
    Tinf_b, A1, k1, A2, k2 = popt_b
    if k2 > k1:
        perm = [0, 3, 4, 1, 2]
        popt_b = np.array([Tinf_b, A2, k2, A1, k1], dtype=float)
        pcov_b = pcov_b[np.ix_(perm, perm)]
        yhat_b = model_bi_exp(t, *popt_b)
        resid_b = y - yhat_b
        rss_b = float(np.sum(resid_b ** 2))

    # Information criteria
    p_s = 3
    p_b = 5
    metrics = {
        "single": {
            "params": popt_s.tolist(),
            "rss": rss_s,
            "rmse": float(np.sqrt(rss_s / n)),
            "aicc": float(aicc(n, rss_s, p_s)),
            "bic": float(bic(n, rss_s, p_s)),
        },
        "bi": {
            "params": popt_b.tolist(),
            "rss": rss_b,
            "rmse": float(np.sqrt(rss_b / n)),
            "aicc": float(aicc(n, rss_b, p_b)),
            "bic": float(bic(n, rss_b, p_b)),
        },
    }

    # Simple out-of-sample evaluation: fit on early times, test on later times
    (t_tr, y_tr), (t_te, y_te) = train_test_split_time(t, y, frac_train=0.7)
    if len(t_te) >= 2:
        # Reuse full-data fits as initial guesses to stabilize training fits
        popt_s_tr, _, _, _, _ = fit_model(model_single_exp, t_tr, y_tr, p0=popt_s, bounds=bounds_single)
        popt_b_tr, _, _, _, _ = fit_model(model_bi_exp, t_tr, y_tr, p0=popt_b, bounds=bounds_bi)
        metrics["single"]["rmse_test"] = rmse(y_te, model_single_exp(t_te, *popt_s_tr))
        metrics["bi"]["rmse_test"] = rmse(y_te, model_bi_exp(t_te, *popt_b_tr))
        metrics["cv"] = {
            "train_frac": 0.7,
            "n_train": int(len(t_tr)),
            "n_test": int(len(t_te)),
        }

    # Parameter uncertainty
    se_s, lo_s, hi_s = param_ci(popt_s, pcov_s)
    se_b, lo_b, hi_b = param_ci(popt_b, pcov_b)

    metrics["single"]["se"] = se_s.tolist()
    metrics["single"]["ci95_lo"] = lo_s.tolist()
    metrics["single"]["ci95_hi"] = hi_s.tolist()

    metrics["bi"]["se"] = se_b.tolist()
    metrics["bi"]["ci95_lo"] = lo_b.tolist()
    metrics["bi"]["ci95_hi"] = hi_b.tolist()

    # Bootstrap for robustness (especially for bi-exponential)
    boot_s = bootstrap_ci(model_single_exp, t, y, popt_s, resid_s, bounds_single, n_boot=2000, seed=1)
    boot_b = bootstrap_ci(model_bi_exp, t, y, popt_b, resid_b, bounds_bi, n_boot=2000, seed=2)
    metrics["single"]["bootstrap"] = boot_s
    metrics["bi"]["bootstrap"] = boot_b

    # Save metrics
    with open(os.path.join(OUT_DIR, "fit_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    # Create plots
    tt = np.linspace(t.min(), t.max(), 400)

    # Figure 1: data with fitted curves
    plt.figure(figsize=(7.2, 4.6))
    plt.plot(t, y, "o", ms=3.5, label="Data")
    plt.plot(tt, model_single_exp(tt, *popt_s), "-", lw=2, label="Single exponential")
    plt.plot(tt, model_bi_exp(tt, *popt_b), "--", lw=2, label="Bi-exponential")
    plt.xlabel("Time (min)")
    plt.ylabel("Temperature (°C)")
    plt.title("Beverage cooling: model fits")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fit_curves.png"), dpi=250)
    plt.close()

    # Figure 2: residuals vs time
    plt.figure(figsize=(7.2, 4.6))
    plt.axhline(0, color="k", lw=1)
    plt.plot(t, resid_s, "o-", ms=3, label="Single exp residual")
    plt.plot(t, resid_b, "s-", ms=3, label="Bi-exp residual", alpha=0.85)
    plt.xlabel("Time (min)")
    plt.ylabel("Residual (°C)")
    plt.title("Residual diagnostics")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "residuals_vs_time.png"), dpi=250)
    plt.close()

    # Figure 3: semi-log linearization using best-fit T_inf (single exp)
    # Plot ln(T - T_inf) vs t to assess single-exponential adequacy.
    Tinf_s = popt_s[0]
    diff = y - Tinf_s
    mask = diff > 0
    plt.figure(figsize=(7.2, 4.6))
    plt.plot(t[mask], np.log(diff[mask]), "o", ms=3.5)
    # Overlay fitted line log(A) - k t
    A_s, k_s = popt_s[1], popt_s[2]
    plt.plot(tt, np.log(max(abs(A_s), 1e-12)) - k_s * tt, "-", lw=2)
    plt.xlabel("Time (min)")
    plt.ylabel(r"$\log(T - T_\infty)$")
    plt.title("Semi-log check for single-exponential cooling")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "semilog_check.png"), dpi=250)
    plt.close()

    # Figure 4: observed vs predicted
    plt.figure(figsize=(6.3, 6.0))
    plt.plot(y, yhat_s, "o", ms=3.5, label="Single exp")
    plt.plot(y, yhat_b, "s", ms=3.5, label="Bi-exp", alpha=0.85)
    lims = [min(y.min(), yhat_s.min(), yhat_b.min()), max(y.max(), yhat_s.max(), yhat_b.max())]
    plt.plot(lims, lims, "k--", lw=1)
    plt.xlabel("Observed (°C)")
    plt.ylabel("Predicted (°C)")
    plt.title("Calibration plot")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "observed_vs_predicted.png"), dpi=250)
    plt.close()

    # Figure 5: residual distribution and normal QQ (single exponential)
    from scipy import stats

    fig, ax = plt.subplots(1, 2, figsize=(9.2, 4.2))
    ax[0].hist(resid_s, bins=16, density=True, alpha=0.75, color="#4C72B0")
    xs = np.linspace(resid_s.min(), resid_s.max(), 200)
    mu, sig = np.mean(resid_s), np.std(resid_s, ddof=1)
    ax[0].plot(xs, stats.norm.pdf(xs, loc=mu, scale=sig), 'k-', lw=2, label='Normal fit')
    ax[0].set_xlabel('Residual (°C)')
    ax[0].set_ylabel('Density')
    ax[0].set_title('Residual histogram')
    ax[0].legend(frameon=False)

    stats.probplot(resid_s, dist="norm", plot=ax[1])
    ax[1].set_title('Normal Q-Q (single exp)')

    fig.suptitle('Residual distribution diagnostics', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "residual_distribution.png"), dpi=250, bbox_inches='tight')
    plt.close(fig)

    # Additional derived quantities for interpretation
    # time constant tau = 1/k, half-life t1/2 = ln(2)/k (single exp)
    tau = 1.0 / popt_s[2]
    thalf = np.log(2) / popt_s[2]
    metrics["single"]["tau_min"] = float(tau)
    metrics["single"]["half_life_min"] = float(thalf)

    # For bi-exponential, compute relative contributions at t=0 and effective time constants
    A1, k1, A2, k2 = popt_b[1], popt_b[2], popt_b[3], popt_b[4]
    metrics["bi"]["tau1_min"] = float(1.0 / k1) if k1 > 0 else None
    metrics["bi"]["tau2_min"] = float(1.0 / k2) if k2 > 0 else None
    metrics["bi"]["fraction_fast_at_t0"] = float(A1 / (A1 + A2)) if (A1 + A2) != 0 else None

    with open(os.path.join(OUT_DIR, "fit_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    # Save fitted series
    out_df = df.copy()
    out_df["pred_single"] = yhat_s
    out_df["pred_bi"] = yhat_b
    out_df["resid_single"] = resid_s
    out_df["resid_bi"] = resid_b
    out_df.to_csv(os.path.join(OUT_DIR, "data_with_predictions.csv"), index=False)

    print("Wrote outputs/fit_metrics.json and outputs/data_with_predictions.csv")
    print("Saved figures to report/images/")


if __name__ == "__main__":
    main()
