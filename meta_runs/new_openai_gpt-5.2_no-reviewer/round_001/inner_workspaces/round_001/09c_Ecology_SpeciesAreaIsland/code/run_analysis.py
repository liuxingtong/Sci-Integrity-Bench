#!/usr/bin/env python
"""Species–area relationship analysis.

Fits classic power-law SAR: S = c * A^z.
Compares OLS on log-transformed data vs Poisson and Negative Binomial GLMs.
Generates figures and a markdown-friendly results summary.

Run:
  python code/run_analysis.py
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

import statsmodels.api as sm
import statsmodels.formula.api as smf


@dataclass
class ModelSummary:
    name: str
    n: int
    params: Dict[str, float]
    bse: Dict[str, float]
    conf_int: Dict[str, Tuple[float, float]]
    aic: float | None
    bic: float | None
    llf: float | None
    dispersion: float | None


def ensure_dirs():
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)


def guess_columns(df: pd.DataFrame) -> Tuple[str, str]:
    cols = [c.lower() for c in df.columns]
    area_candidates = [df.columns[i] for i, c in enumerate(cols) if 'area' in c]
    spp_candidates = [df.columns[i] for i, c in enumerate(cols) if ('species' in c) or ('rich' in c) or (c in ('s', 'sp'))]
    if len(area_candidates) == 0:
        # fallback: first numeric column
        num = df.select_dtypes(include=[np.number]).columns.tolist()
        if not num:
            raise ValueError('No numeric columns found for area')
        area_col = num[0]
    else:
        area_col = area_candidates[0]
    if len(spp_candidates) == 0:
        # fallback: second numeric column (or first if only one)
        num = df.select_dtypes(include=[np.number]).columns.tolist()
        spp_col = num[1] if len(num) > 1 else num[0]
    else:
        spp_col = spp_candidates[0]
    return area_col, spp_col


def prep_data(path='data/island_species.csv') -> Tuple[pd.DataFrame, str, str]:
    df = pd.read_csv(path)
    area_col, spp_col = guess_columns(df)

    d = df[[area_col, spp_col]].copy()
    d = d.rename(columns={area_col: 'area', spp_col: 'richness'})

    # Coerce to numeric
    d['area'] = pd.to_numeric(d['area'], errors='coerce')
    d['richness'] = pd.to_numeric(d['richness'], errors='coerce')

    d = d.dropna()
    d = d[(d['area'] > 0) & (d['richness'] >= 0)]

    # log variables
    d['ln_area'] = np.log(d['area'])
    # handle richness==0 for log-OLS: add small constant; but keep raw for GLM
    d['richness_adj'] = d['richness'].astype(float)
    eps = 0.5
    d['ln_richness'] = np.log(d['richness_adj'] + eps)
    d['log10_area'] = np.log10(d['area'])
    d['log10_richness'] = np.log10(d['richness_adj'] + eps)

    return d.reset_index(drop=True), area_col, spp_col


def fit_models(d: pd.DataFrame):
    # OLS on ln-scale (lognormal errors)
    ols = smf.ols('ln_richness ~ ln_area', data=d).fit()

    # Poisson GLM with log link
    pois = smf.glm('richness ~ ln_area', data=d, family=sm.families.Poisson()).fit()

    # Overdispersion check
    dispersion = float(pois.deviance / pois.df_resid) if pois.df_resid > 0 else np.nan

    # Negative Binomial GLM (NB2)
    # Use discrete NegativeBinomial for alpha estimation; formula interface expects endog/exog
    X = sm.add_constant(d['ln_area'])
    nb = sm.NegativeBinomial(d['richness'], X).fit(disp=False, maxiter=200)

    return ols, pois, nb, dispersion


def summarize_sm_result(res, name: str, n: int, dispersion: float | None = None) -> ModelSummary:
    params = {k: float(v) for k, v in res.params.items()} if hasattr(res.params, 'items') else {str(i): float(v) for i, v in enumerate(res.params)}
    bse = {k: float(v) for k, v in res.bse.items()} if hasattr(res.bse, 'items') else {str(i): float(v) for i, v in enumerate(res.bse)}

    try:
        ci = res.conf_int()
        if isinstance(ci, pd.DataFrame):
            conf_int = {idx: (float(ci.loc[idx, 0]), float(ci.loc[idx, 1])) for idx in ci.index}
        else:
            conf_int = {str(i): (float(ci[i, 0]), float(ci[i, 1])) for i in range(ci.shape[0])}
    except Exception:
        conf_int = {}

    aic = float(res.aic) if hasattr(res, 'aic') and res.aic is not None else None
    bic = float(res.bic) if hasattr(res, 'bic') and res.bic is not None else None
    llf = float(res.llf) if hasattr(res, 'llf') and res.llf is not None else None

    return ModelSummary(
        name=name,
        n=int(n),
        params=params,
        bse=bse,
        conf_int=conf_int,
        aic=aic,
        bic=bic,
        llf=llf,
        dispersion=float(dispersion) if dispersion is not None else None,
    )


def predict_powerlaw(alpha: float, z: float, area: np.ndarray) -> np.ndarray:
    # model: ln(E[S]) = alpha + z ln(A) => E[S] = exp(alpha) * A^z
    return np.exp(alpha) * np.power(area, z)


def make_figures(d: pd.DataFrame, ols, pois, nb):
    sns.set_theme(style='whitegrid', context='talk')

    # Common range for area
    area_grid = np.logspace(np.log10(d['area'].min()), np.log10(d['area'].max()), 200)

    # --- Figure 1: log-log scatter with fitted lines
    fig, ax = plt.subplots(figsize=(8, 6))
    # For log axes, ensure strictly positive values (clip only for plotting)
    y_obs_plot = d['richness'].clip(lower=1e-6)
    ax.scatter(d['area'], y_obs_plot, s=45, alpha=0.8, edgecolor='none')

    # OLS line (back-transform from ln(rich+eps))
    alpha_ols = ols.params['Intercept']
    z_ols = ols.params['ln_area']
    pred_ols = np.exp(alpha_ols) * area_grid ** z_ols - 0.5
    pred_ols = np.clip(pred_ols, 1e-6, None)

    # Poisson line
    alpha_p = pois.params['Intercept']
    z_p = pois.params['ln_area']
    pred_p = predict_powerlaw(alpha_p, z_p, area_grid)
    pred_p = np.clip(pred_p, 1e-6, None)

    # NB line
    # nb params: const, ln_area
    alpha_nb = nb.params[0]
    z_nb = nb.params[1]
    pred_nb = predict_powerlaw(alpha_nb, z_nb, area_grid)
    pred_nb = np.clip(pred_nb, 1e-6, None)

    ax.plot(area_grid, pred_ols, lw=2.5, label=f'OLS (lognormal): z={z_ols:.3f}')
    ax.plot(area_grid, pred_p, lw=2.5, label=f'Poisson GLM: z={z_p:.3f}')
    ax.plot(area_grid, pred_nb, lw=2.5, label=f'NegBin: z={z_nb:.3f}')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Island area')
    ax.set_ylabel('Species richness')
    ax.legend(frameon=True)
    fig.tight_layout()
    fig.savefig('report/images/fig1_species_area_loglog.png', dpi=200)
    plt.close(fig)

    # --- Figure 2: OLS diagnostics (residuals vs fitted and QQ)
    fig, axs = plt.subplots(1, 2, figsize=(12, 5))
    fitted = ols.fittedvalues
    resid = ols.resid

    axs[0].scatter(fitted, resid, s=35, alpha=0.8, edgecolor='none')
    axs[0].axhline(0, color='k', lw=1)
    axs[0].set_xlabel('Fitted ln(richness + 0.5)')
    axs[0].set_ylabel('Residual')
    axs[0].set_title('OLS residuals vs fitted')

    sm.qqplot(resid, line='45', ax=axs[1])
    axs[1].set_title('OLS residual Q-Q')

    fig.tight_layout()
    fig.savefig('report/images/fig2_ols_diagnostics.png', dpi=200)
    plt.close(fig)

    # --- Figure 3: Observed vs predicted (original scale)
    d2 = d.copy()
    d2['pred_ols'] = np.exp(ols.predict(d2)) - 0.5
    d2['pred_ols'] = d2['pred_ols'].clip(lower=0.0)
    d2['pred_pois'] = pois.predict(d2)
    d2['pred_nb'] = nb.predict(sm.add_constant(d2['ln_area']))

    fig, ax = plt.subplots(figsize=(7, 6))
    maxv = max(d2['richness'].max(), d2[['pred_ols','pred_pois','pred_nb']].to_numpy().max())
    ax.plot([0, maxv], [0, maxv], color='k', lw=1)

    ax.scatter(d2['richness'], d2['pred_ols'], s=35, alpha=0.7, label='OLS')
    ax.scatter(d2['richness'], d2['pred_pois'], s=35, alpha=0.7, label='Poisson')
    ax.scatter(d2['richness'], d2['pred_nb'], s=35, alpha=0.7, label='NegBin')

    ax.set_xlabel('Observed richness')
    ax.set_ylabel('Predicted richness')
    ax.legend(frameon=True)
    ax.set_title('Observed vs predicted')
    fig.tight_layout()
    fig.savefig('report/images/fig3_observed_vs_predicted.png', dpi=200)
    plt.close(fig)

    # --- Figure 4: Conservation implication curve (fraction of richness remaining)
    # For a proportional change in area f, predicted richness fraction = f^z.
    f = np.linspace(0.05, 1.0, 200)

    # compute z CI for preferred model (NegBin) using asymptotic SE
    z = z_nb
    se_z = float(nb.bse[1])
    z_lo, z_hi = z - 1.96 * se_z, z + 1.96 * se_z

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(f, f**z, lw=3, label=f'Estimated: z={z:.3f}')
    ax.fill_between(f, f**z_hi, f**z_lo, alpha=0.25, label='Approx. 95% CI')
    ax.set_xlabel('Fraction of area remaining (A_new / A_old)')
    ax.set_ylabel('Predicted fraction of species remaining (S_new / S_old)')
    ax.set_xlim(0.05, 1.0)
    ax.set_ylim(0, 1.02)
    ax.legend(frameon=True, loc='lower right')
    ax.set_title('Species loss expected from habitat loss (power-law SAR)')
    fig.tight_layout()
    fig.savefig('report/images/fig4_conservation_curve.png', dpi=200)
    plt.close(fig)

    return d2


def kfold_indices(n: int, k: int = 5, seed: int = 123) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    rng.shuffle(idx)
    folds = np.array_split(idx, k)
    out = []
    for i in range(k):
        test = folds[i]
        train = np.concatenate([folds[j] for j in range(k) if j != i])
        out.append((train, test))
    return out


def cv_compare(d: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    # Compare predictive performance with simple metrics
    folds = kfold_indices(len(d), k=k)

    rows = []
    for fold, (tr, te) in enumerate(folds, start=1):
        train = d.iloc[tr].copy()
        test = d.iloc[te].copy()

        ols = smf.ols('ln_richness ~ ln_area', data=train).fit()
        pois = smf.glm('richness ~ ln_area', data=train, family=sm.families.Poisson()).fit()
        Xtr = sm.add_constant(train['ln_area'])
        nb = sm.NegativeBinomial(train['richness'], Xtr).fit(disp=False, maxiter=200)

        # predictions
        pred_ols = np.exp(ols.predict(test)) - 0.5
        pred_p = pois.predict(test)
        pred_nb = nb.predict(sm.add_constant(test['ln_area']))

        y = test['richness'].to_numpy()

        def rmse(a, b):
            return float(np.sqrt(np.mean((a - b) ** 2)))

        def mae(a, b):
            return float(np.mean(np.abs(a - b)))

        rows.append({'fold': fold, 'model': 'OLS', 'rmse': rmse(y, pred_ols), 'mae': mae(y, pred_ols)})
        rows.append({'fold': fold, 'model': 'Poisson', 'rmse': rmse(y, pred_p), 'mae': mae(y, pred_p)})
        rows.append({'fold': fold, 'model': 'NegBin', 'rmse': rmse(y, pred_nb), 'mae': mae(y, pred_nb)})

    res = pd.DataFrame(rows)
    agg = res.groupby('model')[['rmse', 'mae']].agg(['mean', 'std'])
    agg.columns = ['_'.join(c) for c in agg.columns]
    agg = agg.reset_index()
    return res, agg


def main():
    ensure_dirs()

    d, area_col, spp_col = prep_data()

    ols, pois, nb, dispersion = fit_models(d)

    summaries = {
        'OLS_lognormal': summarize_sm_result(ols, 'OLS_lognormal', n=len(d)),
        'Poisson_GLM': summarize_sm_result(pois, 'Poisson_GLM', n=len(d), dispersion=dispersion),
        'NegBin': summarize_sm_result(nb, 'NegBin', n=len(d)),
    }

    # Save summaries
    with open('outputs/model_summaries.json', 'w', encoding='utf-8') as f:
        json.dump({k: asdict(v) for k, v in summaries.items()}, f, indent=2)

    # Save fitted/predicted dataset and figures
    d_pred = make_figures(d, ols, pois, nb)
    d_pred.to_csv('outputs/data_with_predictions.csv', index=False)

    # CV comparison
    cv_long, cv_agg = cv_compare(d, k=5)
    cv_long.to_csv('outputs/cv_folds_long.csv', index=False)
    cv_agg.to_csv('outputs/cv_summary.csv', index=False)

    # Write a small text summary for report
    z_ols = float(ols.params['ln_area'])
    z_p = float(pois.params['ln_area'])
    z_nb = float(nb.params[1])

    alpha_nb = float(nb.params[0])
    c_nb = float(np.exp(alpha_nb))

    out = {
        'n': int(len(d)),
        'original_columns': {'area': area_col, 'richness': spp_col},
        'area_range': [float(d['area'].min()), float(d['area'].max())],
        'richness_range': [float(d['richness'].min()), float(d['richness'].max())],
        'z_estimates': {'OLS': z_ols, 'Poisson': z_p, 'NegBin': z_nb},
        'c_negbin': c_nb,
        'poisson_overdispersion_phi': float(dispersion),
    }

    with open('outputs/key_results.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)

    print('Wrote outputs/model_summaries.json, outputs/key_results.json, figures to report/images/')


if __name__ == '__main__':
    main()
