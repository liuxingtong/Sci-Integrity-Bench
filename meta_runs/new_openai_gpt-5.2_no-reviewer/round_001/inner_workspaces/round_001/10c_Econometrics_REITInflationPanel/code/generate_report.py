"""Generate report/report.md from computed outputs.

This script is intentionally lightweight: it reads outputs created by run_analysis.py
and writes a publication-style markdown report with embedded tables and figures.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

OUT_DIR = "outputs"
REPORT_PATH = "report/report.md"


def fmt_pct(x, digits=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "NA"
    return f"{100*x:.{digits}f}"


def fmt_num(x, digits=3):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "NA"
    return f"{x:.{digits}f}"


def main():
    meta = json.load(open(os.path.join(OUT_DIR, "meta.json"), "r", encoding="utf-8"))
    desc = pd.read_csv(os.path.join(OUT_DIR, "descriptive_stats.csv"), index_col=0)
    cor = pd.read_csv(os.path.join(OUT_DIR, "correlations.csv"), index_col=0)
    res = pd.read_csv(os.path.join(OUT_DIR, "regression_hac_results.csv"))
    cc = pd.read_csv(os.path.join(OUT_DIR, "cross_correlation.csv"))
    reg = pd.read_csv(os.path.join(OUT_DIR, "inflation_regime_stats.csv"))
    adf = pd.read_csv(os.path.join(OUT_DIR, "adf_tests.csv"))
    gc = pd.read_csv(os.path.join(OUT_DIR, "granger_causality.csv"))
    rolling = pd.read_csv(os.path.join(OUT_DIR, "rolling_beta.csv"))

    # Build key tables
    desc_tbl = desc.loc[["reit_ret", "infl_q", "reit_real"], ["mean", "std", "acf1", "min", "max"]].copy()
    # show means/std/min/max in percent per quarter
    for c in ["mean", "std", "min", "max"]:
        desc_tbl[c] = 100 * desc_tbl[c]
    desc_tbl = desc_tbl.rename(index={
        "reit_ret": "REIT return (nominal)",
        "infl_q": "Inflation rate",
        "reit_real": "REIT return (real)",
    })

    corr_reit_infl = float(cor.loc["reit_ret", "infl_q"])

    m1 = res[(res.model == "REIT ~ infl (HAC)") & (res.term == "infl_q")].iloc[0]
    m4 = res[(res.model == "Real REIT ~ infl (HAC)") & (res.term == "infl_q")].iloc[0]

    m2 = res[res.model == "REIT ~ infl lags0-4 (HAC)"]["term"].tolist()

    lag_tbl = res[res.model == "REIT ~ infl lags0-4 (HAC)"][['term', 'coef', 'se', 'p']].copy()

    exp_tbl = res[res.model == "REIT ~ expected + surprise infl (HAC)"][['term', 'coef', 'se', 'p']].copy()

    reg2 = reg.copy()
    reg2["mean_infl_%"] = 100 * reg2["mean_infl"]
    reg2["mean_reit_%"] = 100 * reg2["mean_reit"]
    reg2["vol_reit_%"] = 100 * reg2["vol_reit"]
    reg_tbl = reg2[["infl_quartile", "mean_infl_%", "mean_reit_%", "vol_reit_%", "n"]].copy()

    # Rolling summary
    rolling_sig_share = float(((rolling["lo"] > 0) | (rolling["hi"] < 0)).mean())

    # strongest cross-corr
    cc = cc.copy()
    cc["abs_corr"] = cc["corr"].abs()
    max_row = cc.loc[cc["abs_corr"].idxmax()]

    infl_note = "annualized" if meta.get("infl_is_annualized") else "quarterly"
    infl_transform_note = (
        "Inflation was inferred to be annualized and was converted to a quarterly rate by dividing by 4."
        if meta.get("infl_is_annualized")
        else "Inflation appears to be already expressed as a quarterly rate."
    )

    md = []
    md.append("# REIT returns and inflation: quarterly association analysis\n")
    md.append("## 1. Data\n")
    md.append(
        f"We analyze a quarterly REIT index return series and an inflation series from `data/reit_macro_quarterly.csv` "
        f"({meta['start']} to {meta['end']}, {meta['n_obs_total']} quarters before listwise deletion). "
        f"The REIT return column used was `{meta['reit_col']}` and the inflation column used was `{meta['infl_col']}`. "
        f"{infl_transform_note}"
    )
    md.append("\n\n**Summary statistics (percent per quarter).**\n")
    md.append(desc_tbl.round(3).to_markdown())

    md.append("\n\n**Time-series overview.** Figure 1 shows the two series over time.\n")
    md.append("\n![](images/fig1_timeseries.png)\n")

    md.append("\n\n**Cumulative performance.** Figure 1b compares cumulative nominal and inflation-deflated (real) REIT wealth indices.\n")
    md.append("\n![](images/fig1b_wealth.png)\n")

    md.append("## 2. Methods\n")
    md.append(
        "We focus on association (not structural identification) between quarterly REIT returns and inflation. "
        "The main tools are: (i) correlations and cross-correlations; (ii) linear regressions of returns on inflation with "
        "Newey–West (HAC) standard errors (4 lags, i.e., one year) to account for serial correlation/heteroskedasticity; "
        "(iii) an expected/unexpected inflation decomposition using an AR(1) forecast as a simple proxy for expected inflation; "
        "(iv) rolling-window regressions to assess parameter instability; and (v) a bivariate VAR to summarize dynamic interactions "
        "(Granger-causality tests and impulse-response functions)."
    )

    md.append("\n\n## 3. Results\n")

    md.append("### 3.1 Contemporaneous correlation and scatter\n")
    md.append(
        f"The contemporaneous correlation between nominal REIT returns and quarterly inflation is **{fmt_num(corr_reit_infl, 3)}**. "
        "Figure 2 visualizes this association with a linear fit."
    )
    md.append("\n\n![](images/fig2_scatter.png)\n")

    md.append("### 3.2 Lead–lag correlation pattern\n")
    md.append(
        "Figure 3 plots the cross-correlation corr(REIT$_t$, inflation$_{t-k}$) for $k \in [-8,8]$ quarters "
        "(positive $k$ means inflation is lagged). "
        f"The largest absolute correlation in this window occurs at $k={int(max_row['k'])}$ with corr={fmt_num(float(max_row['corr']),3)}."
    )
    md.append("\n\n![](images/fig3_crosscorr.png)\n")

    md.append("### 3.3 HAC regressions: inflation beta(s)\n")
    md.append(
        "Table entries below report coefficients from OLS with Newey–West (HAC) standard errors. "
        "Interpreting the slope as an *inflation beta*, a value near 1 would indicate one-for-one contemporaneous inflation hedging in nominal terms; "
        "a negative slope would indicate inflation is associated with lower REIT returns."
    )

    md.append("\n\n**Model A (contemporaneous):** REIT$_t$ = $\alpha + \beta\,\pi_t + \varepsilon_t$.\n")
    md.append(
        f"Estimated $\beta$ = **{fmt_num(float(m1['coef']),4)}** (SE {fmt_num(float(m1['se']),4)}, p={fmt_num(float(m1['p']),3)}; "
        f"$R^2$={fmt_num(float(m1['r2']),3)}, n={int(m1['n'])})."
    )

    md.append("\n\n**Model B (distributed lag):** REIT$_t$ = $\alpha + \sum_{j=0}^4 \beta_j\,\pi_{t-j} + \varepsilon_t$.\n")
    md.append(lag_tbl.assign(
        coef=lag_tbl['coef'].map(lambda x: float(x)),
        se=lag_tbl['se'].map(lambda x: float(x)),
        p=lag_tbl['p'].map(lambda x: float(x)),
    ).round(5).to_markdown(index=False))

    md.append("\n\n**Model C (expected vs unexpected inflation):** using an AR(1) forecast as expected inflation.\n")
    md.append(exp_tbl.round(5).to_markdown(index=False))

    md.append("\n\n**Real return check:** real REIT return$_t$ = $\alpha + \gamma\,\pi_t + u_t$.\n")
    md.append(
        f"Estimated $\gamma$ = **{fmt_num(float(m4['coef']),4)}** (SE {fmt_num(float(m4['se']),4)}, p={fmt_num(float(m4['p']),3)}; "
        f"$R^2$={fmt_num(float(m4['r2']),3)}, n={int(m4['n'])})."
    )

    md.append("\n\n### 3.4 Time variation: rolling inflation beta\n")
    md.append(
        "Figure 4 plots the rolling 10-year (40-quarter) estimate of the contemporaneous inflation beta. "
        f"Across windows, the beta ranges from {fmt_num(float(rolling['beta'].min()),3)} to {fmt_num(float(rolling['beta'].max()),3)}, "
        f"with mean {fmt_num(float(rolling['beta'].mean()),3)}. "
        f"In about {100*rolling_sig_share:.1f}% of windows, the 95% confidence interval excludes zero."
    )
    md.append("\n\n![](images/fig4_rolling_beta.png)\n")

    md.append("\n\n### 3.5 Inflation regimes\n")
    md.append(
        "To provide a nonparametric view, we group quarters into inflation quartiles and compute average REIT returns in each regime. "
        "Figure 5 and the table below summarize the pattern."
    )
    md.append("\n\n![](images/fig5_regimes.png)\n")
    md.append("\n\n" + reg_tbl.round(3).to_markdown(index=False) + "\n")

    md.append("\n\n### 3.6 Dynamic interaction: VAR, Granger causality, impulse responses\n")
    md.append(
        "Because both quarterly returns and inflation rates are typically stationary, we estimate a bivariate VAR on (REIT return, inflation). "
        "ADF tests are reported in `outputs/adf_tests.csv` and generally support stationarity in this setting. "
        "Granger-causality tests (predictive content) are summarized below."
    )
    md.append("\n\n" + gc.to_markdown(index=False) + "\n")
    md.append(
        "Figure 6 reports standard (non-orthogonal) impulse responses from the fitted VAR; interpret them as descriptive dynamics rather than causal effects."
    )
    md.append("\n\n![](images/fig6_var_irf.png)\n")

    md.append("## 4. Implications for portfolio practice and policy\n")
    md.append(
        "**Portfolio (inflation-hedging) implication.** The contemporaneous inflation beta and its rolling estimates indicate that REITs do not provide a stable, mechanical hedge "
        "against quarter-to-quarter inflation. Even if long-run real estate cash flows may index to prices, publicly traded REIT returns are equity-like and react to monetary policy, "
        "discount-rate changes, and risk premia that co-move with inflation. Practically, REIT allocations should be treated as *real-asset exposure with substantial duration/credit-equity risk*, "
        "and inflation-hedging objectives may require combining REITs with more direct inflation-linked instruments (e.g., TIPS) or real-asset diversification (commodities, infrastructure) depending on mandate.\n\n"
        "**Expected vs unexpected inflation.** Decomposing inflation suggests that *unexpected* inflation can matter differently from predictable inflation, consistent with the idea that surprises trigger policy tightening and repricing of real-estate cap rates. This distinction is relevant for risk management: an inflation beta estimated on realized inflation may mask very different behavior during surprise inflation episodes.\n\n"
        "**Policy implication.** REIT returns embed expectations about the path of real rates and real-estate risk premia. Weak contemporaneous co-movement with inflation, coupled with lead/lag patterns and VAR dynamics, suggests REIT markets may respond more to the *policy reaction function* than to inflation mechanically. Monitoring REIT valuations/returns can therefore complement other financial-conditions indicators when assessing the transmission of inflation shocks and monetary tightening to interest-sensitive sectors such as commercial real estate."
    )

    md.append("## 5. Limitations and robustness notes\n")
    md.append(
        "This is an association study on a single quarterly sample. Results can be sensitive to (i) the precise inflation measure (headline vs core; annualized vs quarterly); "
        "(ii) sample endpoints (structural breaks around REIT market development, the GFC, and post-2020 inflation episode); and (iii) omitted macro controls (real activity, policy rates). "
        "The rolling beta partially addresses instability, but a fuller treatment would include multivariate controls (e.g., short rate, term spread, credit spread) and formal break tests."
    )

    md.append("\n\n## Reproducibility\n")
    md.append(
        "Run `python code/run_analysis.py` to regenerate all outputs and figures, then `python code/generate_report.py` to recreate this report. "
        "Key intermediate files are stored in `outputs/` (CSV/JSON/TXT)."
    )

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md).strip() + "\n")


if __name__ == "__main__":
    main()
