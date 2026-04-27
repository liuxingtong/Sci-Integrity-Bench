#!/usr/bin/env python3
"""Flame speed vs. chamber pressure analysis.

Reads data/flame_pressure_series.csv and fits candidate regression models.
Produces figures in report/images and model comparison tables in outputs.

Reproducible: deterministic, no randomness beyond fixed ordering.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import statsmodels.api as sm
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "flame_pressure_series.csv"
OUT_DIR = ROOT / "outputs"
IMG_DIR = ROOT / "report" / "images"


def rmse(y_true, y_pred) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


@dataclass
class FitResult:
    name: str
    model: object
    yhat: np.ndarray
    residuals: np.ndarray
    metrics: dict


class BaseModel:
    name: str

    def fit(self, df: pd.DataFrame):
        raise NotImplementedError

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError

    def fittedvalues(self) -> np.ndarray:
        raise NotImplementedError

    def resid(self) -> np.ndarray:
        raise NotImplementedError


class OLSModel(BaseModel):
    def __init__(self, name: str, design_fn):
        self.name = name
        self.design_fn = design_fn
        self.res = None

    def fit(self, df: pd.DataFrame):
        X = self.design_fn(df)
        y = df["flame_speed_cm_s"].to_numpy()
        self.res = sm.OLS(y, X).fit()
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        X = self.design_fn(df)
        return self.res.predict(X)

    def fittedvalues(self) -> np.ndarray:
        return np.asarray(self.res.fittedvalues)

    def resid(self) -> np.ndarray:
        return np.asarray(self.res.resid)


class PowerLawLogModel(BaseModel):
    """Power-law model: y = a * P^b with log-normal errors.

    Fit on log scale: ln(y) = ln(a) + b ln(P).
    For prediction on original scale, uses bias correction:
        E[y|P] = exp(mu_log + 0.5*sigma_log^2)
    where sigma_log^2 is MSE of log residuals.
    """

    name = "power_law"

    def __init__(self):
        self.res = None

    def _design(self, df: pd.DataFrame):
        lnP = np.log(df["pressure_kPa"].to_numpy())
        return sm.add_constant(lnP)

    def fit(self, df: pd.DataFrame):
        if (df["pressure_kPa"] <= 0).any() or (df["flame_speed_cm_s"] <= 0).any():
            raise ValueError("PowerLawLogModel requires positive pressure and flame speed")
        X = self._design(df)
        y = np.log(df["flame_speed_cm_s"].to_numpy())
        self.res = sm.OLS(y, X).fit()
        return self

    @property
    def sigma2_log(self) -> float:
        # mean squared error of residuals on log scale
        return float(np.mean(np.square(self.res.resid)))

    def predict(self, df: pd.DataFrame, bias_correct: bool = True) -> np.ndarray:
        X = self._design(df)
        mu = self.res.predict(X)
        if bias_correct:
            return np.exp(mu + 0.5 * self.sigma2_log)
        return np.exp(mu)

    def fittedvalues(self) -> np.ndarray:
        # fitted mean on original scale with bias correction
        return self.predict(pd.DataFrame({"pressure_kPa": self._P_train}), bias_correct=True)

    def resid(self) -> np.ndarray:
        # residuals on original scale (y - E[y])
        y = self._y_train
        yhat = self.predict(pd.DataFrame({"pressure_kPa": self._P_train}), bias_correct=True)
        return y - yhat

    def store_training_data(self, df: pd.DataFrame):
        self._P_train = df["pressure_kPa"].to_numpy()
        self._y_train = df["flame_speed_cm_s"].to_numpy()


def design_linear(df: pd.DataFrame):
    return sm.add_constant(df[["pressure_kPa"]].to_numpy())


def design_quadratic(df: pd.DataFrame):
    P = df["pressure_kPa"].to_numpy()
    X = np.column_stack([P, P ** 2])
    return sm.add_constant(X)


def loocv_predictions(model_ctor, df: pd.DataFrame) -> np.ndarray:
    loo = LeaveOneOut()
    preds = np.zeros(len(df), dtype=float)
    for train_idx, test_idx in loo.split(df):
        dtrain = df.iloc[train_idx]
        dtest = df.iloc[test_idx]
        model = model_ctor()
        model.fit(dtrain)
        if isinstance(model, PowerLawLogModel):
            model.store_training_data(dtrain)
        preds[test_idx[0]] = float(model.predict(dtest)[0])
    return preds


def fit_and_score(model_name: str, model_ctor, df: pd.DataFrame) -> FitResult:
    model = model_ctor()
    model.fit(df)
    if isinstance(model, PowerLawLogModel):
        model.store_training_data(df)

    y = df["flame_speed_cm_s"].to_numpy()
    yhat = model.predict(df)
    resid = y - yhat

    # LOOCV for robust model comparison
    yhat_cv = loocv_predictions(model_ctor, df)

    metrics = {
        "n": int(len(df)),
        "r2_in_sample": float(r2_score(y, yhat)),
        "rmse_in_sample": rmse(y, yhat),
        "mae_in_sample": float(mean_absolute_error(y, yhat)),
        "rmse_loocv": rmse(y, yhat_cv),
        "mae_loocv": float(mean_absolute_error(y, yhat_cv)),
    }

    # Add AIC/BIC where available/meaningful
    if hasattr(model, "res") and model.res is not None:
        try:
            metrics["aic"] = float(model.res.aic)
            metrics["bic"] = float(model.res.bic)
        except Exception:
            pass

    return FitResult(name=model_name, model=model, yhat=yhat, residuals=resid, metrics=metrics)


def make_pressure_grid(df: pd.DataFrame, n: int = 200) -> pd.DataFrame:
    Pmin, Pmax = float(df.pressure_kPa.min()), float(df.pressure_kPa.max())
    grid = np.linspace(Pmin, Pmax, n)
    return pd.DataFrame({"pressure_kPa": grid})


def prediction_band_ols(ols_model: OLSModel, grid_df: pd.DataFrame, alpha: float = 0.05):
    Xg = ols_model.design_fn(grid_df)
    pred = ols_model.res.get_prediction(Xg)
    sf = pred.summary_frame(alpha=alpha)
    # columns: mean, mean_se, mean_ci_lower, mean_ci_upper, obs_ci_lower, obs_ci_upper
    out = grid_df.copy()
    out["mean"] = sf["mean"].to_numpy()
    out["mean_ci_lower"] = sf["mean_ci_lower"].to_numpy()
    out["mean_ci_upper"] = sf["mean_ci_upper"].to_numpy()
    out["obs_ci_lower"] = sf["obs_ci_lower"].to_numpy()
    out["obs_ci_upper"] = sf["obs_ci_upper"].to_numpy()
    return out


def prediction_band_powerlaw(pl_model: PowerLawLogModel, grid_df: pd.DataFrame, alpha: float = 0.05):
    Xg = pl_model._design(grid_df)
    pred = pl_model.res.get_prediction(Xg)
    sf = pred.summary_frame(alpha=alpha)
    # Work on log scale and transform. Bias correction applied to mean; CI shown for mean on log scale.
    out = grid_df.copy()
    mu = sf["mean"].to_numpy()
    out["mean"] = np.exp(mu + 0.5 * pl_model.sigma2_log)
    out["mean_ci_lower"] = np.exp(sf["mean_ci_lower"].to_numpy())
    out["mean_ci_upper"] = np.exp(sf["mean_ci_upper"].to_numpy())

    # Approximate prediction interval on original scale (lognormal): exp(mu ± z*sqrt(var_pred + sigma^2))
    # sf provides obs_ci on log scale for future obs (includes residual variance), so exponentiate.
    if "obs_ci_lower" in sf.columns:
        out["obs_ci_lower"] = np.exp(sf["obs_ci_lower"].to_numpy())
        out["obs_ci_upper"] = np.exp(sf["obs_ci_upper"].to_numpy())
    else:
        out["obs_ci_lower"] = np.nan
        out["obs_ci_upper"] = np.nan
    return out


def plot_main_fit(df: pd.DataFrame, fit: FitResult, band_df: pd.DataFrame, outpath: Path):
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(6.4, 4.4))

    ax.scatter(df.pressure_kPa, df.flame_speed_cm_s, s=35, alpha=0.9, label="Observed")

    ax.plot(band_df.pressure_kPa, band_df["mean"], color="C1", lw=2.2, label=f"Fit: {fit.name}")
    ax.fill_between(
        band_df.pressure_kPa,
        band_df["mean_ci_lower"],
        band_df["mean_ci_upper"],
        color="C1",
        alpha=0.25,
        label="95% CI (mean)",
        linewidth=0,
    )

    # Lighter prediction interval where available
    if band_df[["obs_ci_lower", "obs_ci_upper"]].notna().all(axis=None):
        ax.fill_between(
            band_df.pressure_kPa,
            band_df["obs_ci_lower"],
            band_df["obs_ci_upper"],
            color="C1",
            alpha=0.12,
            label="95% PI (obs)",
            linewidth=0,
        )

    ax.set_xlabel("Chamber pressure (kPa)")
    ax.set_ylabel("Flame speed (cm/s)")
    ax.set_title("Flame speed vs. chamber pressure")
    ax.legend(frameon=True, fontsize=9)

    fig.tight_layout()
    fig.savefig(outpath, dpi=200)
    plt.close(fig)


def plot_residual_diagnostics(df: pd.DataFrame, fit: FitResult, outpath: Path):
    sns.set_theme(style="whitegrid")
    resid = fit.residuals
    fitted = fit.yhat

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))

    ax = axes[0]
    ax.scatter(fitted, resid, s=32, alpha=0.9)
    ax.axhline(0, color="k", lw=1)
    ax.set_xlabel("Fitted flame speed (cm/s)")
    ax.set_ylabel("Residual (cm/s)")
    ax.set_title("Residuals vs fitted")

    ax = axes[1]
    sm.qqplot(resid, line="45", ax=ax, markerfacecolor="C0", markeredgecolor="C0", alpha=0.8)
    ax.set_title("Normal Q-Q of residuals")

    fig.suptitle(f"Diagnostics: {fit.name}", y=1.02)
    fig.tight_layout()
    fig.savefig(outpath, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_loglog(df: pd.DataFrame, outpath: Path):
    sns.set_theme(style="whitegrid")
    d = df.copy()
    d = d[(d.pressure_kPa > 0) & (d.flame_speed_cm_s > 0)].copy()

    model = PowerLawLogModel().fit(d)
    model.store_training_data(d)

    grid = make_pressure_grid(d, n=200)
    band = prediction_band_powerlaw(model, grid)

    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.scatter(d.pressure_kPa, d.flame_speed_cm_s, s=35, alpha=0.9, label="Observed")
    ax.plot(band.pressure_kPa, band["mean"], color="C2", lw=2.2, label="Power-law fit")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Chamber pressure (kPa, log scale)")
    ax.set_ylabel("Flame speed (cm/s, log scale)")
    ax.set_title("Log-log view (power-law trend)")
    ax.legend(frameon=True, fontsize=9)

    fig.tight_layout()
    fig.savefig(outpath, dpi=200)
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)

    # Basic validation/cleaning
    expected = {"pressure_kPa", "flame_speed_cm_s"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.copy()
    df = df.dropna(subset=["pressure_kPa", "flame_speed_cm_s"])

    # Ensure numeric
    df["pressure_kPa"] = pd.to_numeric(df["pressure_kPa"], errors="coerce")
    df["flame_speed_cm_s"] = pd.to_numeric(df["flame_speed_cm_s"], errors="coerce")
    df = df.dropna(subset=["pressure_kPa", "flame_speed_cm_s"]).reset_index(drop=True)

    # Sort for nice plotting
    df = df.sort_values("pressure_kPa").reset_index(drop=True)

    (OUT_DIR / "cleaned_data.csv").write_text(df.to_csv(index=False))

    # Candidate models
    candidates = [
        ("linear", lambda: OLSModel("linear", design_linear)),
        ("quadratic", lambda: OLSModel("quadratic", design_quadratic)),
        ("power_law", lambda: PowerLawLogModel()),
    ]

    fits: list[FitResult] = []
    for name, ctor in candidates:
        fits.append(fit_and_score(name, ctor, df))

    comp = pd.DataFrame([f.metrics | {"model": f.name} for f in fits]).set_index("model")
    comp = comp.sort_values("rmse_loocv")
    comp.to_csv(OUT_DIR / "model_comparison.csv")

    best_name = comp.index[0]
    best_fit = next(f for f in fits if f.name == best_name)

    # Save parameter table / summary
    params = {}
    if hasattr(best_fit.model, "res") and best_fit.model.res is not None:
        res = best_fit.model.res
        params["params"] = {str(k): float(v) for k, v in zip(res.params.index if hasattr(res.params, 'index') else range(len(res.params)), np.asarray(res.params))}
        params["bse"] = [float(x) for x in np.asarray(res.bse)]
        params["pvalues"] = [float(x) for x in np.asarray(res.pvalues)]
        try:
            params["conf_int_95"] = [[float(a), float(b)] for a, b in np.asarray(res.conf_int(alpha=0.05))]
        except Exception:
            pass
        # Store a text summary too
        (OUT_DIR / f"best_model_summary_{best_name}.txt").write_text(res.summary().as_text())

    (OUT_DIR / "best_model.json").write_text(json.dumps({"best_model": best_name, "comparison": comp.reset_index().to_dict(orient="records"), "params": params}, indent=2))

    # Main fit plot with band
    grid = make_pressure_grid(df)
    if isinstance(best_fit.model, OLSModel):
        band = prediction_band_ols(best_fit.model, grid)
    else:
        band = prediction_band_powerlaw(best_fit.model, grid)
    band.to_csv(OUT_DIR / "best_model_band.csv", index=False)

    plot_main_fit(df, best_fit, band, IMG_DIR / "fig1_flame_speed_vs_pressure.png")
    plot_residual_diagnostics(df, best_fit, IMG_DIR / "fig2_residual_diagnostics.png")
    plot_loglog(df, IMG_DIR / "fig3_loglog_powerlaw.png")

    # Additional plot: observed vs predicted (in-sample and LOOCV)
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(5.6, 5.0))

    # LOOCV predictions for best model
    best_ctor = next(ctor for nm, ctor in candidates if nm == best_name)
    yhat_cv = loocv_predictions(best_ctor, df)

    ax.scatter(df.flame_speed_cm_s, best_fit.yhat, s=30, alpha=0.85, label="In-sample")
    ax.scatter(df.flame_speed_cm_s, yhat_cv, s=30, alpha=0.85, label="LOOCV")
    lims = [
        float(min(df.flame_speed_cm_s.min(), best_fit.yhat.min(), yhat_cv.min())),
        float(max(df.flame_speed_cm_s.max(), best_fit.yhat.max(), yhat_cv.max())),
    ]
    ax.plot(lims, lims, color="k", lw=1, ls="--")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("Observed flame speed (cm/s)")
    ax.set_ylabel("Predicted flame speed (cm/s)")
    ax.set_title(f"Observed vs predicted ({best_name})")
    ax.legend(frameon=True, fontsize=9)

    fig.tight_layout()
    fig.savefig(IMG_DIR / "fig4_observed_vs_predicted.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
