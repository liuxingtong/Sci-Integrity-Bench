# -*- coding: utf-8 -*-
"""Air pollution and respiratory clinic visits: daily panel analysis.

This script:
- Loads data/daily_panel.csv
- Performs exploratory summaries
- Fits count regression models (Poisson GLM with robust SE; sensitivity NB)
- Evaluates lag structures for PM2.5
- Estimates policy-relevant impacts under counterfactual PM2.5 caps
- Produces figures in report/images and tables in outputs/

Designed to be reproducible and tolerant to modest schema changes.
"""

import os
import re
import json
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

import statsmodels.api as sm
import statsmodels.formula.api as smf
from patsy import dmatrix

warnings.filterwarnings("ignore", category=FutureWarning)


DATA_PATH = "data/daily_panel.csv"
OUT_DIR = "outputs"
FIG_DIR = "report/images"


@dataclass
class Schema:
    date_col: str
    outcome_col: str
    pm25_col: str
    panel_id_col: str | None
    flu_col: str | None
    holiday_col: str | None
    heating_covars: list
    meteo_covars: list


def _pick_date_col(df: pd.DataFrame) -> str:
    # Prefer explicit 'date'
    candidates = [c for c in df.columns if re.search(r"date", c, re.I)]
    if not candidates:
        candidates = [c for c in df.columns if re.search(r"day", c, re.I)]
    if not candidates:
        # last resort: try first object column
        obj = [c for c in df.columns if df[c].dtype == "object"]
        if obj:
            candidates = obj
        else:
            raise ValueError("No plausible date column found")
    # choose candidate with best parse success
    best = None
    best_na = 1.0
    for c in candidates:
        d = pd.to_datetime(df[c], errors="coerce")
        na = d.isna().mean()
        if na < best_na:
            best_na = na
            best = c
    if best is None or best_na > 0.5:
        raise ValueError("Unable to parse date column")
    return best


def _pick_pm25_col(df: pd.DataFrame) -> str:
    patterns = [r"pm\s*2\.?5", r"pm25", r"pm_?2_?5"]
    for pat in patterns:
        for c in df.columns:
            if re.search(pat, c, re.I):
                return c
    # fallback: any column starting with pm
    for c in df.columns:
        if re.match(r"pm", c, re.I):
            return c
    raise ValueError("No PM2.5 column found")


def _pick_outcome_col(df: pd.DataFrame) -> str:
    # common patterns
    pats = [r"resp.*visit", r"visit.*resp", r"resp", r"clinic.*visit", r"er.*resp", r"outpatient.*resp"]
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    for pat in pats:
        for c in df.columns:
            if c in numeric_cols and re.search(pat, c, re.I):
                return c
    # fallback: choose the integer-like count column with largest mean
    candidates = []
    for c in numeric_cols:
        s = df[c].dropna()
        if len(s) == 0:
            continue
        # count-ish: non-negative and close to integer
        if (s.min() >= 0) and (np.mean(np.isclose(s, np.round(s))) > 0.95):
            candidates.append((c, s.mean()))
    if not candidates:
        raise ValueError("No plausible outcome (count) column found")
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def _pick_panel_id(df: pd.DataFrame) -> str | None:
    for key in [r"clinic", r"site", r"facility", r"location", r"area", r"district", r"region", r"county", r"city", r"id$"]:
        cols = [c for c in df.columns if re.search(key, c, re.I)]
        for c in cols:
            if df[c].dtype == "object" or pd.api.types.is_integer_dtype(df[c]):
                if df[c].nunique(dropna=True) > 1 and df[c].nunique(dropna=True) < len(df) / 3:
                    return c
    return None


def _pick_optional_col(df: pd.DataFrame, patterns: list[str]) -> str | None:
    for pat in patterns:
        for c in df.columns:
            if re.search(pat, c, re.I):
                return c
    return None


def infer_schema(df: pd.DataFrame) -> Schema:
    date_col = _pick_date_col(df)
    pm25_col = _pick_pm25_col(df)
    outcome_col = _pick_outcome_col(df)
    panel_id = _pick_panel_id(df)

    flu_col = _pick_optional_col(df, [r"flu", r"influenza", r"ili", r"grippe"])
    holiday_col = _pick_optional_col(df, [r"holiday", r"school.*holiday", r"school_break", r"vacation"])

    heating_covars = [c for c in df.columns if re.search(r"heat|heating|hdd|degree_day|fuel|gas|coal|electric", c, re.I)]
    meteo_covars = [c for c in df.columns if re.search(r"temp|temperature|humid|dew|wind|rain|precip|pressure", c, re.I)]

    # remove overlaps and key vars
    for c in [date_col, pm25_col, outcome_col, panel_id, flu_col, holiday_col]:
        if c is None:
            continue
        heating_covars = [x for x in heating_covars if x != c]
        meteo_covars = [x for x in meteo_covars if x != c]

    return Schema(
        date_col=date_col,
        outcome_col=outcome_col,
        pm25_col=pm25_col,
        panel_id_col=panel_id,
        flu_col=flu_col,
        holiday_col=holiday_col,
        heating_covars=sorted(set(heating_covars)),
        meteo_covars=sorted(set(meteo_covars)),
    )


def prepare_df(df: pd.DataFrame, schema: Schema) -> pd.DataFrame:
    d = df.copy()
    d["date"] = pd.to_datetime(d[schema.date_col], errors="coerce")
    d = d.loc[~d["date"].isna()].copy()

    # Basic time features
    d = d.sort_values(["date"] + ([schema.panel_id_col] if schema.panel_id_col else []))
    d["dow"] = d["date"].dt.dayofweek.astype(int)
    d["month"] = d["date"].dt.month.astype(int)
    d["year"] = d["date"].dt.year.astype(int)
    d["doy"] = d["date"].dt.dayofyear.astype(int)

    # continuous time index for splines
    d["t"] = (d["date"] - d["date"].min()).dt.days.astype(int)

    # Standardize PM2.5 numeric
    d["pm25"] = pd.to_numeric(d[schema.pm25_col], errors="coerce")
    d["y"] = pd.to_numeric(d[schema.outcome_col], errors="coerce")

    # Ensure holiday is binary 0/1 if present
    if schema.holiday_col is not None:
        h = d[schema.holiday_col]
        if h.dtype == "object":
            d["holiday"] = h.astype(str).str.lower().isin(["1", "true", "yes", "y", "holiday"]).astype(int)
        else:
            d["holiday"] = (pd.to_numeric(h, errors="coerce").fillna(0) > 0).astype(int)
    else:
        d["holiday"] = 0

    # Flu index numeric if present
    if schema.flu_col is not None:
        d["flu"] = pd.to_numeric(d[schema.flu_col], errors="coerce")
    else:
        d["flu"] = np.nan

    # Coerce covariates to numeric
    covars = schema.heating_covars + schema.meteo_covars
    for c in covars:
        d[c] = pd.to_numeric(d[c], errors="coerce")

    # Lags (within panel if applicable)
    group_cols = [schema.panel_id_col] if schema.panel_id_col else []
    d["pm25_lag0"] = d["pm25"]
    for lag in [1, 2, 3]:
        d[f"pm25_lag{lag}"] = d.groupby(group_cols)["pm25"].shift(lag) if group_cols else d["pm25"].shift(lag)
    d["pm25_ma01"] = d[["pm25_lag0", "pm25_lag1"]].mean(axis=1)
    d["pm25_ma03"] = d[["pm25_lag0", "pm25_lag1", "pm25_lag2", "pm25_lag3"]].mean(axis=1)

    # Drop impossible outcomes
    d = d.loc[d["y"].notna() & (d["y"] >= 0)].copy()

    return d


def summarize_data(d: pd.DataFrame, schema: Schema) -> dict:
    summ = {}
    summ["n_rows"] = int(d.shape[0])
    summ["n_days"] = int(d["date"].nunique())
    summ["date_min"] = str(d["date"].min().date())
    summ["date_max"] = str(d["date"].max().date())
    if schema.panel_id_col:
        summ["n_panels"] = int(d[schema.panel_id_col].nunique())
    else:
        summ["n_panels"] = 1

    for k, col in [("pm25", "pm25"), ("outcome", "y")]:
        s = d[col]
        summ[f"{k}_mean"] = float(np.nanmean(s))
        summ[f"{k}_sd"] = float(np.nanstd(s))
        summ[f"{k}_p05"] = float(np.nanpercentile(s, 5))
        summ[f"{k}_p50"] = float(np.nanpercentile(s, 50))
        summ[f"{k}_p95"] = float(np.nanpercentile(s, 95))

    return summ


def build_formula(exposure_term: str, schema: Schema, d: pd.DataFrame, df_time_per_year: int = 8) -> tuple[str, dict]:
    """Return a patsy formula string and a dict of extra columns to attach."""

    extras = {}

    # long-term/seasonal trend spline on time index
    years = max(1, int(np.ceil((d["date"].max() - d["date"].min()).days / 365.25)))
    df_time = max(6, df_time_per_year * years)
    extras["bs_t"] = dmatrix(f"bs(t, df={df_time}, degree=3, include_intercept=False)", d, return_type='dataframe')

    # day-of-week and month fixed effects (simple)
    terms = [exposure_term, "C(dow)", "C(month)"]

    # flu and holiday
    if d["flu"].notna().mean() > 0.2:
        terms.append("flu")
    terms.append("holiday")

    # add meteorology / heating covariates
    covars = []
    for c in schema.meteo_covars:
        if d[c].notna().mean() > 0.5:
            covars.append(c)
    for c in schema.heating_covars:
        if d[c].notna().mean() > 0.5:
            covars.append(c)

    # Avoid perfect multicollinearity: keep up to top 6 covars by non-missing
    if len(covars) > 6:
        covars = sorted(covars, key=lambda x: d[x].notna().mean(), reverse=True)[:6]

    terms += covars

    if schema.panel_id_col:
        terms.append(f"C({schema.panel_id_col})")

    # Add spline basis columns explicitly
    # We'll attach bs_t dataframe columns with unique names
    bs_cols = list(extras["bs_t"].columns)
    for i, c in enumerate(bs_cols):
        new = f"bs_t_{i}"
        extras["bs_t"].rename(columns={c: new}, inplace=True)
    terms += list(extras["bs_t"].columns)

    formula = "y ~ " + " + ".join(terms)
    return formula, extras


def fit_poisson_robust(d: pd.DataFrame, formula: str, cluster_col: str | None = None):
    model = smf.glm(formula=formula, data=d, family=sm.families.Poisson())
    res = model.fit(cov_type="HC1" if cluster_col is None else "cluster", cov_kwds=None if cluster_col is None else {"groups": d[cluster_col]})
    return res


def fit_negbin(d: pd.DataFrame, formula: str, cluster_col: str | None = None):
    # statsmodels discrete NB2 via GLM NB family for stability
    model = smf.glm(formula=formula, data=d, family=sm.families.NegativeBinomial(alpha=1.0))
    res = model.fit(cov_type="HC1" if cluster_col is None else "cluster", cov_kwds=None if cluster_col is None else {"groups": d[cluster_col]})
    return res


def extract_effect(res, term: str, scale: float = 10.0) -> dict:
    b = float(res.params[term])
    se = float(res.bse[term])
    rr = np.exp(b * scale)
    lcl = np.exp((b - 1.96 * se) * scale)
    ucl = np.exp((b + 1.96 * se) * scale)
    return {
        "term": term,
        "beta": b,
        "se": se,
        "rr_per10": float(rr),
        "rr_per10_lcl": float(lcl),
        "rr_per10_ucl": float(ucl),
        "pct_change_per10": float((rr - 1) * 100),
        "pct_change_lcl": float((lcl - 1) * 100),
        "pct_change_ucl": float((ucl - 1) * 100),
        "aic": float(res.aic),
        "n": int(res.nobs),
    }


def make_figures(d: pd.DataFrame, schema: Schema, effects_df: pd.DataFrame, main_res, exposure_term: str):
    os.makedirs(FIG_DIR, exist_ok=True)
    sns.set_theme(style="whitegrid")

    # Aggregate to daily total if panel
    if schema.panel_id_col:
        daily = d.groupby("date", as_index=False).agg(y=("y", "sum"), pm25=("pm25", "mean"))
    else:
        daily = d[["date", "y", "pm25"]].groupby("date", as_index=False).mean()

    # Figure 1: time series
    fig, ax1 = plt.subplots(figsize=(10, 4.2))
    ax1.plot(daily["date"], daily["pm25"], color="#2C7FB8", linewidth=1.2, label="PM2.5")
    ax1.set_ylabel("PM2.5 (µg/m³)")
    ax1.set_xlabel("Date")
    ax2 = ax1.twinx()
    ax2.plot(daily["date"], daily["y"], color="#D95F0E", linewidth=1.2, alpha=0.8, label="Respiratory visits")
    ax2.set_ylabel("Respiratory visits")
    ax1.set_title("Daily PM2.5 and respiratory clinic visits")
    # combine legends
    lines, labels = [], []
    for ax in [ax1, ax2]:
        l, lab = ax.get_legend_handles_labels()
        lines += l
        labels += lab
    ax1.legend(lines, labels, loc="upper right", frameon=True)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig1_timeseries.png"), dpi=200)
    plt.close(fig)

    # Figure 2: scatter + LOWESS
    fig, ax = plt.subplots(figsize=(6.2, 4.8))
    sns.scatterplot(data=daily.sample(min(500, len(daily)), random_state=1), x="pm25", y="y", s=18, alpha=0.35, ax=ax)
    low = sm.nonparametric.lowess(daily["y"], daily["pm25"], frac=0.25, return_sorted=True)
    ax.plot(low[:, 0], low[:, 1], color="black", linewidth=2, label="LOWESS")
    ax.set_title("Unadjusted association (daily aggregates)")
    ax.set_xlabel("PM2.5 (µg/m³)")
    ax.set_ylabel("Respiratory visits")
    ax.legend(frameon=True)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig2_scatter_lowess.png"), dpi=200)
    plt.close(fig)

    # Figure 3: lag / exposure definition comparison
    lag_order = ["pm25_lag0", "pm25_lag1", "pm25_lag2", "pm25_lag3", "pm25_ma01", "pm25_ma03"]
    plotdf = effects_df.copy()
    plotdf["exposure"] = pd.Categorical(plotdf["exposure"], categories=lag_order, ordered=True)
    plotdf = plotdf.sort_values("exposure")

    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    ax.errorbar(
        plotdf["exposure"].astype(str),
        plotdf["pct_change_per10"],
        yerr=[plotdf["pct_change_per10"] - plotdf["pct_change_lcl"], plotdf["pct_change_ucl"] - plotdf["pct_change_per10"]],
        fmt="o",
        color="#1B9E77",
        ecolor="#1B9E77",
        elinewidth=2,
        capsize=4,
    )
    ax.axhline(0, color="gray", linewidth=1)
    ax.set_ylabel("% change in visits per 10 µg/m³ PM2.5")
    ax.set_xlabel("PM2.5 exposure definition")
    ax.set_title("Estimated PM2.5 effect across lags / moving averages")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig3_lag_effects.png"), dpi=200)
    plt.close(fig)

    # Figure 4: model fit (predicted vs observed daily totals)
    if schema.panel_id_col:
        # predict for each row then aggregate
        d = d.copy()
        d["pred"] = main_res.predict(d)
        daily_fit = d.groupby("date", as_index=False).agg(obs=("y", "sum"), pred=("pred", "sum"))
    else:
        d = d.copy()
        d["pred"] = main_res.predict(d)
        daily_fit = d.groupby("date", as_index=False).agg(obs=("y", "sum"), pred=("pred", "sum"))

    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(daily_fit["date"], daily_fit["obs"], color="#D95F0E", linewidth=1.2, label="Observed")
    ax.plot(daily_fit["date"], daily_fit["pred"], color="#7570B3", linewidth=1.2, label="Predicted")
    ax.set_title("Model fit: observed vs predicted respiratory visits (daily totals)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Visits")
    ax.legend(frameon=True)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig4_fit_observed_predicted.png"), dpi=200)
    plt.close(fig)

    # Figure 5: residual diagnostics (Pearson residuals vs fitted)
    resid = main_res.resid_pearson
    fitted = main_res.fittedvalues
    fig, ax = plt.subplots(figsize=(6.5, 4.4))
    sns.scatterplot(x=fitted, y=resid, s=14, alpha=0.35, ax=ax)
    ax.axhline(0, color="gray", linewidth=1)
    ax.set_title("Pearson residuals vs fitted")
    ax.set_xlabel("Fitted mean")
    ax.set_ylabel("Pearson residual")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig5_residuals.png"), dpi=200)
    plt.close(fig)


def policy_counterfactual(d: pd.DataFrame, res, exposure_col: str, cap: float) -> pd.DataFrame:
    dd = d.copy()
    dd["pred_obs"] = res.predict(dd)
    # counterfactual: replace exposure with min(exposure, cap)
    dd[exposure_col + "_cf"] = np.minimum(dd[exposure_col], cap)
    # In the fitted model, exposure term is named exactly exposure_col
    # We'll construct a copy with exposure replaced
    dcf = dd.copy()
    dcf[exposure_col] = dcf[exposure_col + "_cf"]
    dd["pred_cf"] = res.predict(dcf)
    dd["averted"] = dd["pred_obs"] - dd["pred_cf"]
    return dd


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    schema = infer_schema(df)
    d = prepare_df(df, schema)

    # Drop missing key vars for modelling
    d_model = d.copy()

    # Choose exposure definitions to compare
    exposures = ["pm25_lag0", "pm25_lag1", "pm25_lag2", "pm25_lag3", "pm25_ma01", "pm25_ma03"]

    # cluster by panel if present, else by date (serial correlation) using date clusters
    cluster = schema.panel_id_col if schema.panel_id_col else "date"

    # Fit models for each exposure definition
    effects = []
    models = {}
    formulas = {}

    for ex in exposures:
        dd = d_model.loc[d_model[ex].notna()].copy()
        # attach exposure column with stable name for formula
        dd["exposure"] = dd[ex]

        formula, extras = build_formula("exposure", schema, dd)
        for k, v in extras.items():
            if isinstance(v, pd.DataFrame):
                dd = pd.concat([dd.reset_index(drop=True), v.reset_index(drop=True)], axis=1)

        # Remove rows with missing covars in formula
        # patsy will drop automatically; ensure consistent n
        res = fit_poisson_robust(dd, formula, cluster_col=cluster)

        models[ex] = (res, dd)
        formulas[ex] = formula

        eff = extract_effect(res, term="exposure", scale=10.0)
        eff["exposure"] = ex
        eff["formula"] = formula
        eff["cluster"] = cluster
        effects.append(eff)

    effects_df = pd.DataFrame(effects)
    effects_df.to_csv(os.path.join(OUT_DIR, "pm25_effects_lags.csv"), index=False)

    # Choose main exposure definition: lowest AIC among MA03 and lag0 as pragmatic; else overall min
    candidate = effects_df.loc[effects_df["exposure"].isin(["pm25_ma03", "pm25_ma01", "pm25_lag0"])].copy()
    if len(candidate) > 0:
        main_ex = candidate.sort_values("aic").iloc[0]["exposure"]
    else:
        main_ex = effects_df.sort_values("aic").iloc[0]["exposure"]

    main_res, main_dd = models[main_ex]

    # Sensitivity: negative binomial
    nb_res = fit_negbin(main_dd, formulas[main_ex], cluster_col=cluster)
    nb_eff = extract_effect(nb_res, term="exposure", scale=10.0)
    nb_eff["exposure"] = main_ex

    # Policy counterfactuals
    # WHO 2021 daily PM2.5 guideline is 15 µg/m3; also show 25 and 35 as common standards
    caps = [15.0, 25.0, 35.0]
    policy_rows = []
    for cap in caps:
        dd_policy = policy_counterfactual(main_dd, main_res, exposure_col="exposure", cap=cap)
        if schema.panel_id_col:
            daily = dd_policy.groupby("date", as_index=False).agg(
                pred_obs=("pred_obs", "sum"),
                pred_cf=("pred_cf", "sum"),
                averted=("averted", "sum"),
                pm25_mean=("pm25", "mean"),
            )
        else:
            daily = dd_policy.groupby("date", as_index=False).agg(
                pred_obs=("pred_obs", "sum"),
                pred_cf=("pred_cf", "sum"),
                averted=("averted", "sum"),
                pm25_mean=("pm25", "mean"),
            )
        total_averted = daily["averted"].sum()
        total_pred = daily["pred_obs"].sum()
        policy_rows.append({
            "cap_pm25": cap,
            "total_pred_visits": float(total_pred),
            "total_averted_visits": float(total_averted),
            "pct_reduction": float(100 * total_averted / total_pred) if total_pred > 0 else np.nan,
            "n_days": int(daily.shape[0]),
        })
        daily.to_csv(os.path.join(OUT_DIR, f"counterfactual_daily_cap{int(cap)}.csv"), index=False)

    policy_df = pd.DataFrame(policy_rows)
    policy_df.to_csv(os.path.join(OUT_DIR, "policy_counterfactual_summary.csv"), index=False)

    # Policy figure: averted visits under alternative caps
    import matplotlib.ticker as mtick
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    plot = policy_df.sort_values('cap_pm25')
    ax.bar(plot['cap_pm25'].astype(str), plot['total_averted_visits'], color='#4C78A8')
    ax.set_xlabel('Daily PM2.5 cap (µg/m³)')
    ax.set_ylabel('Total averted visits (model-predicted)')
    ax.set_title('Estimated reduction in respiratory visits under PM2.5 caps')
    for i, r in plot.reset_index(drop=True).iterrows():
        ax.text(i, r['total_averted_visits'], f"{r['pct_reduction']:.1f}%", ha='center', va='bottom', fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig6_policy_averted_bar.png'), dpi=200)
    plt.close(fig)

    # Exposure distribution and exceedances
    if schema.panel_id_col:
        daily_pm = d_model.groupby('date', as_index=False).agg(pm25=('pm25','mean'))
    else:
        daily_pm = d_model.groupby('date', as_index=False).agg(pm25=('pm25','mean'))
    thresh = [15, 25, 35]
    exceed = {f'exceed_{t}': float((daily_pm['pm25']>t).mean()) for t in thresh}
    pd.DataFrame([exceed]).to_csv(os.path.join(OUT_DIR,'pm25_exceedance_rates.csv'), index=False)

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    sns.histplot(daily_pm['pm25'].dropna(), bins=30, color='#2C7FB8', edgecolor='white', ax=ax)
    for t in thresh:
        ax.axvline(t, color='black', linestyle='--', linewidth=1)
        ax.text(t, ax.get_ylim()[1]*0.95, f"{t}", ha='center', va='top', fontsize=9)
    ax.set_title('Distribution of daily mean PM2.5 with policy thresholds')
    ax.set_xlabel('PM2.5 (µg/m³)')
    ax.set_ylabel('Days')
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig7_pm25_distribution.png'), dpi=200)
    plt.close(fig)

    # Save dataset summary and model metadata
    summary = summarize_data(d, schema)
    meta = {
        "schema": schema.__dict__,
        "data_summary": summary,
        "main_exposure": main_ex,
        "main_formula": formulas[main_ex],
        "main_aic": float(main_res.aic),
        "main_deviance": float(main_res.deviance),
        "main_df_resid": float(main_res.df_resid),
        "main_overdispersion_phi": float(main_res.deviance / max(1.0, main_res.df_resid)),
        "nb_aic": float(nb_res.aic),
    }
    with open(os.path.join(OUT_DIR, "analysis_metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    # Save coefficient tables
    coef = pd.DataFrame({
        "term": main_res.params.index,
        "coef": main_res.params.values,
        "se": main_res.bse.values,
        "z": main_res.tvalues.values,
        "p": main_res.pvalues.values,
    })
    coef.to_csv(os.path.join(OUT_DIR, "main_model_coefficients.csv"), index=False)

    nb_coef = pd.DataFrame({
        "term": nb_res.params.index,
        "coef": nb_res.params.values,
        "se": nb_res.bse.values,
        "z": nb_res.tvalues.values,
        "p": nb_res.pvalues.values,
    })
    nb_coef.to_csv(os.path.join(OUT_DIR, "nb_sensitivity_coefficients.csv"), index=False)

    # Figures
    make_figures(d_model, schema, effects_df, main_res, exposure_term=main_ex)

    # Write a small text summary for the report
    main_eff = effects_df.loc[effects_df["exposure"] == main_ex].iloc[0].to_dict()
    out = {
        "main_effect_poisson": main_eff,
        "main_effect_negbin": nb_eff,
        "policy": policy_rows,
    }
    with open(os.path.join(OUT_DIR, "key_results.json"), "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
