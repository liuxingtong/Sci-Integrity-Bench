"""REIT-Inflation association analysis (quarterly panel/time-series).

Runs:
- data ingestion/cleaning
- descriptive stats
- correlations and cross-correlations
- HAC regressions (Newey-West)
- expected vs unexpected inflation decomposition
- rolling beta estimates
- VAR / Granger causality / impulse responses
- regime (inflation quantiles) comparisons

Outputs:
- figures -> report/images
- tables  -> outputs

Reproducible: fixed random seed.
"""

from __future__ import annotations

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
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller


warnings.filterwarnings("ignore")


DATA_PATH = "data/reit_macro_quarterly.csv"
OUT_DIR = "outputs"
FIG_DIR = "report/images"


def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)


def detect_date_col(df: pd.DataFrame) -> str:
    # Prefer common names
    candidates = [c for c in df.columns if c.lower() in {"date", "quarter", "time", "period"}]
    if candidates:
        return candidates[0]

    # Otherwise any object column that looks like quarter or date
    obj_cols = [c for c in df.columns if df[c].dtype == "object"]
    for c in obj_cols:
        s = df[c].astype(str)
        if s.str.contains(r"Q[1-4]", regex=True).mean() > 0.8:
            return c
        if s.str.contains(r"\d{4}-\d{2}-\d{2}", regex=True).mean() > 0.8:
            return c
    raise ValueError("Could not detect date/quarter column")


def parse_quarter_index(s: pd.Series) -> pd.PeriodIndex:
    s = s.astype(str).str.strip()
    # Formats: 1990Q1, 1990-Q1, 1990:Q1
    m = s.str.extract(r"(?P<y>\d{4})\s*[-:]?\s*Q(?P<q>[1-4])", expand=True)
    if m.notna().all(axis=1).mean() > 0.8:
        return pd.PeriodIndex(year=m["y"].astype(int), quarter=m["q"].astype(int), freq="Q")

    # Try datetime
    dt = pd.to_datetime(s, errors="coerce")
    if dt.notna().mean() > 0.8:
        return dt.dt.to_period("Q")

    raise ValueError("Could not parse quarter index")


def detect_main_cols(df: pd.DataFrame) -> tuple[str, str]:
    lc = {c: c.lower() for c in df.columns}

    reit_candidates = [c for c in df.columns if "reit" in lc[c] and ("ret" in lc[c] or "return" in lc[c])]
    infl_candidates = [c for c in df.columns if ("infl" in lc[c] or "cpi" in lc[c]) and ("rate" in lc[c] or "infl" in lc[c] or "cpi" in lc[c])]

    # Fallbacks: any col containing reit; any col containing inflation
    if not reit_candidates:
        reit_candidates = [c for c in df.columns if "reit" in lc[c]]
    if not infl_candidates:
        infl_candidates = [c for c in df.columns if "infl" in lc[c] or "cpi" in lc[c]]

    # Keep only numeric
    reit_candidates = [c for c in reit_candidates if pd.api.types.is_numeric_dtype(df[c])]
    infl_candidates = [c for c in infl_candidates if pd.api.types.is_numeric_dtype(df[c])]

    if not reit_candidates or not infl_candidates:
        raise ValueError(f"Could not detect REIT return and inflation columns. reit={reit_candidates} infl={infl_candidates}")

    # Prefer shortest names
    reit_col = sorted(reit_candidates, key=len)[0]
    infl_col = sorted(infl_candidates, key=len)[0]
    return reit_col, infl_col


def maybe_to_decimal(x: pd.Series) -> pd.Series:
    # Heuristic: if typical magnitude exceeds 1, likely percent.
    med = x.abs().median(skipna=True)
    if pd.isna(med):
        return x
    if med > 1.0:
        return x / 100.0
    return x


@dataclass
class ModelResult:
    name: str
    params: pd.Series
    bse: pd.Series
    tvalues: pd.Series
    pvalues: pd.Series
    r2: float
    nobs: int
    dw: float


def ols_hac(y: pd.Series, X: pd.DataFrame, lags: int = 4) -> sm.regression.linear_model.RegressionResultsWrapper:
    Xc = sm.add_constant(X, has_constant="add")
    m = sm.OLS(y, Xc, missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return m


def summarize_model(name: str, m) -> ModelResult:
    return ModelResult(
        name=name,
        params=m.params,
        bse=m.bse,
        tvalues=m.tvalues,
        pvalues=m.pvalues,
        r2=float(getattr(m, "rsquared", np.nan)),
        nobs=int(m.nobs),
        dw=float(durbin_watson(m.resid)),
    )


def model_results_to_table(models: list[ModelResult]) -> pd.DataFrame:
    rows = []
    for mr in models:
        for p in mr.params.index:
            rows.append(
                {
                    "model": mr.name,
                    "term": p,
                    "coef": mr.params[p],
                    "se": mr.bse[p],
                    "t": mr.tvalues[p],
                    "p": mr.pvalues[p],
                    "r2": mr.r2,
                    "n": mr.nobs,
                    "dw": mr.dw,
                }
            )
    return pd.DataFrame(rows)


def adf_report(x: pd.Series, name: str) -> dict:
    x = x.dropna()
    stat, p, lags, nobs, crit, _ = adfuller(x, autolag="AIC")
    return {
        "series": name,
        "adf_stat": stat,
        "p_value": p,
        "used_lags": lags,
        "nobs": nobs,
        "crit_1%": crit.get("1%", np.nan),
        "crit_5%": crit.get("5%", np.nan),
        "crit_10%": crit.get("10%", np.nan),
    }


def main():
    ensure_dirs()

    df_raw = pd.read_csv(DATA_PATH)
    date_col = detect_date_col(df_raw)
    reit_col, infl_col = detect_main_cols(df_raw)

    df = df_raw.copy()
    df["quarter"] = parse_quarter_index(df[date_col])
    df = df.drop(columns=[date_col]) if date_col != "quarter" else df
    df = df.set_index("quarter").sort_index()

    # Core series
    df["reit_ret"] = maybe_to_decimal(df[reit_col].astype(float))
    df["infl"] = maybe_to_decimal(df[infl_col].astype(float))

    # If inflation is in annualized percent vs quarterly? We'll infer rough scale.
    # If median quarterly inflation > 0.05 (5%), likely annualized; convert to quarterly rate.
    infl_med = df["infl"].abs().median(skipna=True)
    infl_is_annualized = infl_med > 0.05
    df["infl_q"] = df["infl"] / 4.0 if infl_is_annualized else df["infl"]

    # Real REIT return
    df["reit_real"] = (1 + df["reit_ret"]) / (1 + df["infl_q"]) - 1

    meta = {
        "date_col": date_col,
        "reit_col": reit_col,
        "infl_col": infl_col,
        "infl_is_annualized": bool(infl_is_annualized),
        "n_obs_total": int(len(df)),
        "start": str(df.index.min()),
        "end": str(df.index.max()),
    }
    with open(os.path.join(OUT_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Restrict to complete cases for main analyses
    d = df[["reit_ret", "infl_q", "reit_real"]].dropna()

    # Descriptive stats
    desc = pd.DataFrame(
        {
            "mean": d.mean(),
            "std": d.std(ddof=1),
            "min": d.min(),
            "p25": d.quantile(0.25),
            "median": d.median(),
            "p75": d.quantile(0.75),
            "max": d.max(),
            "skew": d.skew(),
            "kurt": d.kurtosis(),
            "acf1": d.apply(lambda s: s.autocorr(lag=1)),
        }
    )
    desc.to_csv(os.path.join(OUT_DIR, "descriptive_stats.csv"))

    corr = d[["reit_ret", "infl_q", "reit_real"]].corr()
    corr.to_csv(os.path.join(OUT_DIR, "correlations.csv"))

    # Figure 1: time series
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    d["reit_ret"].mul(100).plot(ax=ax[0], color="#1f77b4", lw=1.2)
    ax[0].axhline(0, color="black", lw=0.8)
    ax[0].set_ylabel("REIT return (% q/q)")
    ax[0].set_title("Quarterly REIT returns and inflation")

    d["infl_q"].mul(100).plot(ax=ax[1], color="#d62728", lw=1.2)
    ax[1].axhline(0, color="black", lw=0.8)
    ax[1].set_ylabel("Inflation (% q/q)")
    ax[1].set_xlabel("Quarter")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig1_timeseries.png"), dpi=200)
    plt.close(fig)

    # Figure 1b: cumulative nominal vs real wealth index
    wealth = (1 + d[["reit_ret", "reit_real"]]).cumprod()
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(wealth.index.to_timestamp(), wealth["reit_ret"], lw=1.6, label="Nominal")
    ax.plot(wealth.index.to_timestamp(), wealth["reit_real"], lw=1.6, label="Real (deflated by inflation)")
    ax.set_yscale("log")
    ax.set_title("Cumulative growth of $1 (log scale)")
    ax.set_ylabel("Wealth index")
    ax.set_xlabel("Quarter")
    ax.legend(frameon=False)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig1b_wealth.png"), dpi=200)
    plt.close(fig)

    # Figure 2: scatter with regression line
    fig, ax = plt.subplots(figsize=(7.5, 6.2))
    sns.regplot(x=d["infl_q"] * 100, y=d["reit_ret"] * 100, ax=ax, scatter_kws={"alpha": 0.7, "s": 25})
    ax.set_xlabel("Inflation (% q/q)")
    ax.set_ylabel("REIT return (% q/q)")
    ax.set_title("Contemporaneous association")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig2_scatter.png"), dpi=200)
    plt.close(fig)

    # Cross-correlation: corr(reit_t, infl_{t-k}) for k=-8..8
    max_k = 8
    cc = []
    for k in range(-max_k, max_k + 1):
        # k>0 means infl lags (infl_{t-k})? We'll define: corr(reit_t, infl_{t-k}) where positive k = inflation lag.
        x = d["infl_q"].shift(k)
        r = d["reit_ret"].corr(x)
        cc.append({"k": k, "corr": r})
    cc = pd.DataFrame(cc)
    cc.to_csv(os.path.join(OUT_DIR, "cross_correlation.csv"), index=False)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(cc["k"], cc["corr"], color="#2ca02c")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("k in corr(REIT_t, inflation_{t-k})  (k>0: inflation lagged; k<0: inflation led)")
    ax.set_ylabel("Correlation")
    ax.set_title("Cross-correlation (lead/lag)")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig3_crosscorr.png"), dpi=200)
    plt.close(fig)

    # HAC regressions
    models = []

    m1 = ols_hac(d["reit_ret"], d[["infl_q"]], lags=4)
    models.append(summarize_model("REIT ~ infl (HAC)", m1))

    # Distributed lag up to 4 quarters
    X_lags = pd.concat({f"infl_l{j}": d["infl_q"].shift(j) for j in range(0, 5)}, axis=1)
    m2 = ols_hac(d["reit_ret"], X_lags, lags=4)
    models.append(summarize_model("REIT ~ infl lags0-4 (HAC)", m2))

    # Expected vs unexpected inflation (AR(1) expectation)
    infl = d["infl_q"]
    infl_l1 = infl.shift(1)
    m_infl_ar1 = sm.OLS(infl[1:], sm.add_constant(infl_l1[1:], has_constant="add"), missing="drop").fit()
    exp_infl = m_infl_ar1.predict(sm.add_constant(infl_l1, has_constant="add"))
    surprise = infl - exp_infl
    d2 = d.copy()
    d2["exp_infl"] = exp_infl
    d2["infl_surprise"] = surprise

    m3 = ols_hac(d2["reit_ret"], d2[["exp_infl", "infl_surprise"]], lags=4)
    models.append(summarize_model("REIT ~ expected + surprise infl (HAC)", m3))

    # Real return regressions
    m4 = ols_hac(d["reit_real"], d[["infl_q"]], lags=4)
    models.append(summarize_model("Real REIT ~ infl (HAC)", m4))

    table = model_results_to_table(models)
    table.to_csv(os.path.join(OUT_DIR, "regression_hac_results.csv"), index=False)

    # Rolling beta (40-quarter window)
    win = 40
    betas = []
    idx = d.index
    for end in range(win, len(d) + 1):
        sub = d.iloc[end - win : end]
        mm = ols_hac(sub["reit_ret"], sub[["infl_q"]], lags=4)
        b = mm.params.get("infl_q", np.nan)
        se = mm.bse.get("infl_q", np.nan)
        betas.append({"quarter": idx[end - 1], "beta": b, "se": se})
    betas = pd.DataFrame(betas).set_index("quarter")
    betas["lo"] = betas["beta"] - 1.96 * betas["se"]
    betas["hi"] = betas["beta"] + 1.96 * betas["se"]
    betas.to_csv(os.path.join(OUT_DIR, "rolling_beta.csv"))

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(betas.index.to_timestamp(), betas["beta"], color="#9467bd", lw=1.6, label="beta")
    ax.fill_between(betas.index.to_timestamp(), betas["lo"], betas["hi"], color="#9467bd", alpha=0.2, label="95% CI")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title(f"Rolling (window={win} quarters) inflation beta of REIT returns")
    ax.set_ylabel("Beta")
    ax.set_xlabel("Quarter")
    ax.legend(frameon=False)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig4_rolling_beta.png"), dpi=200)
    plt.close(fig)

    # Inflation regimes
    d_reg = d.copy()
    d_reg["infl_quartile"] = pd.qcut(d_reg["infl_q"], 4, labels=["Q1 (low)", "Q2", "Q3", "Q4 (high)"])
    reg_stats = d_reg.groupby("infl_quartile").agg(
        mean_reit=("reit_ret", "mean"),
        med_reit=("reit_ret", "median"),
        vol_reit=("reit_ret", "std"),
        mean_infl=("infl_q", "mean"),
        n=("reit_ret", "size"),
    )
    reg_stats.to_csv(os.path.join(OUT_DIR, "inflation_regime_stats.csv"))

    fig, ax = plt.subplots(figsize=(9, 5))
    (reg_stats["mean_reit"] * 100).reindex(reg_stats.index).plot(kind="bar", ax=ax, color="#1f77b4")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("Mean REIT return (% q/q)")
    ax.set_title("Average REIT returns by inflation quartile")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig5_regimes.png"), dpi=200)
    plt.close(fig)

    # Stationarity checks (ADF)
    adf = pd.DataFrame([adf_report(d["reit_ret"], "reit_ret"), adf_report(d["infl_q"], "infl_q")])
    adf.to_csv(os.path.join(OUT_DIR, "adf_tests.csv"), index=False)

    # VAR analysis (levels; both are rates/returns so typically stationary)
    var_df = d[["reit_ret", "infl_q"]].dropna()
    # Select lag length by AIC up to 8
    maxlags = min(8, int(len(var_df) / 10)) if len(var_df) >= 30 else 2
    sel = VAR(var_df).select_order(maxlags=maxlags)
    p = int(sel.aic) if np.isfinite(sel.aic) else max(1, int(sel.selected_orders.get("aic", 1) or 1))
    p = max(1, min(p, maxlags))

    var_model = VAR(var_df).fit(p)

    # Granger causality tests
    gc1 = var_model.test_causality("reit_ret", ["infl_q"], kind="f")
    gc2 = var_model.test_causality("infl_q", ["reit_ret"], kind="f")

    gc = pd.DataFrame(
        [
            {"direction": "infl -> reit", "stat": float(gc1.test_statistic), "pvalue": float(gc1.pvalue), "df": str(gc1.df_denom)},
            {"direction": "reit -> infl", "stat": float(gc2.test_statistic), "pvalue": float(gc2.pvalue), "df": str(gc2.df_denom)},
        ]
    )
    gc.to_csv(os.path.join(OUT_DIR, "granger_causality.csv"), index=False)

    # IRFs
    irf = var_model.irf(12)

    fig = irf.plot(orth=False)
    fig.set_size_inches(12, 8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig6_var_irf.png"), dpi=200)
    plt.close(fig)

    # Save VAR summary info
    with open(os.path.join(OUT_DIR, "var_lag_selection.txt"), "w", encoding="utf-8") as f:
        f.write(str(sel.summary()))
        f.write("\n\nChosen lags p=" + str(p) + "\n")
        f.write(str(var_model.summary()))

    print("Done. Wrote outputs to", OUT_DIR, "and figures to", FIG_DIR)


if __name__ == "__main__":
    main()
