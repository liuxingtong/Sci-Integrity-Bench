"""Association analysis: quarterly REIT returns and inflation.

Outputs:
- cleaned panel in outputs/clean_panel.parquet
- summary stats and regression tables in outputs/
- figures in report/images/

Run:
  python code/run_analysis.py
"""

from __future__ import annotations

import os
import re
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.api import VAR


ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(ROOT, "data", "reit_macro_quarterly.csv")
OUT_DIR = os.path.join(ROOT, "outputs")
FIG_DIR = os.path.join(ROOT, "report", "images")


def ensure_dirs() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)


def parse_quarter_to_timestamp(x: str) -> pd.Timestamp:
    """Parse common quarter formats into quarter-end timestamp.

    Supports: '1990Q1', '1990-Q1', '1990:Q1', 'Q1 1990', '1990 Q1'.
    """
    if pd.isna(x):
        return pd.NaT
    s = str(x).strip()

    # 1990Q1 / 1990-Q1 / 1990:Q1
    m = re.match(r"^(\d{4})\s*[-:]?\s*Q([1-4])$", s, flags=re.IGNORECASE)
    if m:
        y, q = int(m.group(1)), int(m.group(2))
        return pd.Period(f"{y}Q{q}", freq="Q").to_timestamp(how="end")

    # Q1 1990 / Q1-1990
    m = re.match(r"^Q([1-4])\s*[- ]\s*(\d{4})$", s, flags=re.IGNORECASE)
    if m:
        q, y = int(m.group(1)), int(m.group(2))
        return pd.Period(f"{y}Q{q}", freq="Q").to_timestamp(how="end")

    # 1990-03-31, etc.
    try:
        ts = pd.to_datetime(s)
        return ts
    except Exception:
        return pd.NaT


def infer_and_parse_date(df: pd.DataFrame) -> pd.DataFrame:
    """Infer and construct a time index.

    The provided dataset may use a true quarter label (e.g., 1990Q1) or
    a simple integer quarter counter (0,1,2,...). We support both.
    """
    candidates = [c for c in df.columns if any(k in c.lower() for k in ["date", "quarter", "time", "period"])]
    if not candidates:
        raise ValueError("No obvious date/quarter column found.")

    # If a candidate is an integer sequence, use it as the index directly.
    for date_col in candidates:
        s = pd.to_numeric(df[date_col], errors="coerce")
        if s.notna().all():
            # integer-like and (weakly) increasing
            s_int = s.astype(int)
            diffs = s_int.diff().dropna()
            if (diffs >= 0).all() and (diffs.isin([0, 1]).mean() > 0.95):
                out = df.copy()
                out = out.drop(columns=[date_col])
                out.index = s_int.values
                out.index.name = "quarter_index"
                return out.sort_index()

    # Otherwise, attempt to parse actual quarter/date strings.
    best = None
    best_rate = 1.0
    for date_col in candidates:
        parsed = df[date_col].apply(parse_quarter_to_timestamp)
        nat_rate = parsed.isna().mean()
        if nat_rate > 0.5:
            parsed2 = pd.to_datetime(df[date_col], errors="coerce")
            nat_rate2 = parsed2.isna().mean()
            if nat_rate2 < nat_rate:
                parsed, nat_rate = parsed2, nat_rate2
        if nat_rate < best_rate:
            best = (date_col, parsed)
            best_rate = nat_rate

    if best is None or best_rate > 0.5:
        raise ValueError(f"Could not parse a usable date column among {candidates} (best NaT rate={best_rate:.2f})")

    date_col, parsed = best
    out = df.copy()
    out["date"] = parsed
    out = out.drop(columns=[date_col])
    out = out.sort_values("date").set_index("date")
    return out


def pick_series(df: pd.DataFrame) -> dict:
    """Heuristics to identify a REIT return series and an inflation series.

    The dataset schema may vary; we score columns by keyword matches.
    """
    cols = list(df.columns)

    def score_col(c: str, pos_keys: list[str], neg_keys: list[str] | None = None) -> int:
        cl = c.lower()
        s = sum(k in cl for k in pos_keys)
        if neg_keys:
            s -= sum(k in cl for k in neg_keys)
        return s

    # Candidate REIT series: must contain 'reit' or known providers.
    reit_scores = []
    for c in cols:
        cl = c.lower()
        if any(k in cl for k in ["reit", "nareit", "ftse", "ncreif"]):
            reit_scores.append((score_col(c, ["reit", "return", "ret", "total"], ["index", "level"]) , c))
    reit_scores.sort(reverse=True)
    reit = reit_scores[0][1] if reit_scores and reit_scores[0][0] > 0 else (reit_scores[0][1] if reit_scores else None)

    # Candidate inflation series: 'infl', 'inflation', or price index change (cpi/pce).
    infl_scores = []
    for c in cols:
        cl = c.lower()
        if any(k in cl for k in ["infl", "inflation", "cpi", "pce", "price"]):
            infl_scores.append((score_col(c, ["infl", "inflation", "cpi", "pce", "price", "change", "pct", "yoy", "qoq"]), c))
    infl_scores.sort(reverse=True)
    infl = infl_scores[0][1] if infl_scores and infl_scores[0][0] > 0 else (infl_scores[0][1] if infl_scores else None)

    if reit is None or infl is None:
        raise ValueError(f"Could not infer reit ({reit}) or inflation ({infl}) column from: {cols}")

    return {"reit": reit, "infl": infl}


def to_decimal_return(x: pd.Series) -> pd.Series:
    """Convert percent-like series to decimals if values look like percent."""
    s = pd.to_numeric(x, errors="coerce")
    # Heuristic: if typical magnitude > 1, treat as percent
    med = np.nanmedian(np.abs(s.values))
    if np.isfinite(med) and med > 1.0:
        return s / 100.0
    return s


def summarize(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = pd.DataFrame(index=cols)
    for c in cols:
        s = df[c].dropna()
        out.loc[c, "n"] = s.shape[0]
        out.loc[c, "mean"] = s.mean()
        out.loc[c, "std"] = s.std(ddof=1)
        out.loc[c, "min"] = s.min()
        out.loc[c, "p25"] = s.quantile(0.25)
        out.loc[c, "median"] = s.median()
        out.loc[c, "p75"] = s.quantile(0.75)
        out.loc[c, "max"] = s.max()
        out.loc[c, "skew"] = s.skew()
        out.loc[c, "kurtosis"] = s.kurtosis()
    return out


def ols_hac(y: pd.Series, X: pd.DataFrame, lags: int = 4):
    Xc = sm.add_constant(X, has_constant="add")
    model = sm.OLS(y, Xc, missing="drop")
    res = model.fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return res


def fmt_reg_table(res, title: str) -> pd.DataFrame:
    params = res.params
    se = res.bse
    t = res.tvalues
    p = res.pvalues
    tab = pd.DataFrame({
        "coef": params,
        "se(HAC)": se,
        "t": t,
        "p": p,
    })
    tab.index.name = "term"
    tab["model"] = title
    tab["n"] = int(res.nobs)
    tab["r2"] = res.rsquared
    return tab


def main():
    ensure_dirs()
    warnings.filterwarnings("ignore")
    sns.set_theme(style="whitegrid", context="talk")

    raw = pd.read_csv(DATA_PATH)
    df = infer_and_parse_date(raw)

    series = pick_series(df)
    reit_col, infl_col = series["reit"], series["infl"]

    # Canonical names
    df = df.rename(columns={reit_col: "reit_ret_raw", infl_col: "infl_raw"})

    # Convert to numeric
    df["reit_ret_raw"] = pd.to_numeric(df["reit_ret_raw"], errors="coerce")
    df["infl_raw"] = pd.to_numeric(df["infl_raw"], errors="coerce")

    # Heuristic: if the series looks like an index level, convert to returns/inflation rates.
    # Otherwise interpret as return/rate (possibly in percent) and convert to decimals.
    def maybe_level_to_return(s: pd.Series) -> pd.Series:
        x = s.dropna()
        if x.empty:
            return s
        med = float(np.nanmedian(np.abs(x.values)))
        mn = float(np.nanmin(x.values))
        mx = float(np.nanmax(x.values))
        # Index levels tend to be strictly positive and far larger than typical quarterly rates.
        looks_like_level = (mn > 0) and (mx > 10) and (med > 5)
        if looks_like_level:
            return s.pct_change()
        return to_decimal_return(s)

    df["reit_ret"] = maybe_level_to_return(df["reit_ret_raw"])
    df["infl"] = maybe_level_to_return(df["infl_raw"])

    # Basic derived series
    df["reit_real"] = df["reit_ret"] - df["infl"]
    df["infl_l1"] = df["infl"].shift(1)
    df["infl_l2"] = df["infl"].shift(2)
    df["reit_ret_l1"] = df["reit_ret"].shift(1)

    # Save clean panel (prefer parquet; fall back to CSV)
    clean_parquet = os.path.join(OUT_DIR, "clean_panel.parquet")
    clean_csv = os.path.join(OUT_DIR, "clean_panel.csv")
    try:
        df.to_parquet(clean_parquet)
    except Exception:
        df.to_csv(clean_csv)

    # Summary stats
    summ = summarize(df, ["reit_ret", "infl", "reit_real"])
    summ.to_csv(os.path.join(OUT_DIR, "summary_stats.csv"))

    # Correlations
    corr = df[["reit_ret", "infl", "reit_real"]].corr(method="pearson")
    scorr = df[["reit_ret", "infl", "reit_real"]].corr(method="spearman")
    corr.to_csv(os.path.join(OUT_DIR, "corr_pearson.csv"))
    scorr.to_csv(os.path.join(OUT_DIR, "corr_spearman.csv"))

    # Figure 1: Time series
    fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    ax[0].plot(df.index, 100*df["reit_ret"], color="tab:blue", lw=1)
    ax[0].axhline(0, color="black", lw=0.8)
    ax[0].set_ylabel("REIT return (%)")
    ax[0].set_title("Quarterly REIT returns")

    ax[1].plot(df.index, 100*df["infl"], color="tab:red", lw=1)
    ax[1].axhline(0, color="black", lw=0.8)
    ax[1].set_ylabel("Inflation (%)")
    ax[1].set_title("Quarterly inflation")

    plt.tight_layout()
    fig_path = os.path.join(FIG_DIR, "ts_reit_infl.png")
    fig.savefig(fig_path, dpi=200)
    plt.close(fig)

    # Figure 2: Scatter
    tmp = df[["reit_ret", "infl"]].dropna()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.regplot(data=tmp, x="infl", y="reit_ret", ax=ax,
                scatter_kws={"alpha": 0.6, "s": 35}, line_kws={"color": "black"})
    ax.axhline(0, color="grey", lw=0.8)
    ax.axvline(0, color="grey", lw=0.8)
    ax.set_xlabel("Inflation (decimal)")
    ax.set_ylabel("REIT return (decimal)")
    ax.set_title("REIT returns vs. inflation (contemporaneous)")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "scatter_reit_infl.png"), dpi=200)
    plt.close(fig)

    # Rolling correlation
    roll_window = 40  # ~10 years
    roll_corr = df["reit_ret"].rolling(roll_window).corr(df["infl"])
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df.index, roll_corr, color="tab:purple", lw=1.2)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title(f"Rolling correlation: REIT returns vs inflation ({roll_window}-quarter window)")
    ax.set_ylabel("Correlation")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "rolling_corr.png"), dpi=200)
    plt.close(fig)

    # OLS regressions with HAC SEs
    reg_tabs = []

    # Model A: contemporaneous
    resA = ols_hac(df["reit_ret"], df[["infl"]], lags=4)
    reg_tabs.append(fmt_reg_table(resA, "A: reit_ret ~ infl"))

    # Model B: include lags of inflation
    resB = ols_hac(df["reit_ret"], df[["infl", "infl_l1", "infl_l2"]], lags=4)
    reg_tabs.append(fmt_reg_table(resB, "B: reit_ret ~ infl + infl_l1 + infl_l2"))

    # Model C: add persistence of returns
    resC = ols_hac(df["reit_ret"], df[["infl", "infl_l1", "reit_ret_l1"]], lags=4)
    reg_tabs.append(fmt_reg_table(resC, "C: reit_ret ~ infl + infl_l1 + reit_ret_l1"))

    reg = pd.concat(reg_tabs, axis=0)
    reg.to_csv(os.path.join(OUT_DIR, "regressions_hac.csv"))

    # Diagnostics: Ljung-Box on residuals
    diag = []
    for name, res in [("A", resA), ("B", resB), ("C", resC)]:
        r = pd.Series(res.resid).dropna()
        lb = acorr_ljungbox(r, lags=[4, 8], return_df=True)
        lb["model"] = name
        diag.append(lb.reset_index(names="lag"))
    diag = pd.concat(diag, ignore_index=True)
    diag.to_csv(os.path.join(OUT_DIR, "ljungbox.csv"), index=False)

    # VAR / Granger causality (bivariate)
    var_df = df[["reit_ret", "infl"]].dropna()
    # ensure stationary-ish: these are rates/returns already, but we still fit levels
    model = VAR(var_df)
    sel = model.select_order(maxlags=8)
    # pick AIC-selected lag if available
    lag = sel.selected_orders.get("aic", None)
    lag = int(lag) if lag is not None else 2
    lag = max(1, min(lag, 8))
    var_res = model.fit(lag)

    # Granger causality tests
    gc1 = var_res.test_causality("reit_ret", ["infl"], kind="f")
    gc2 = var_res.test_causality("infl", ["reit_ret"], kind="f")

    def extract_df(obj):
        # statsmodels versions differ; be defensive
        d = getattr(obj, "df", None)
        if d is None:
            return {"df": None, "df_num": None, "df_denom": None}
        if isinstance(d, (tuple, list)) and len(d) == 2:
            return {"df": d, "df_num": d[0], "df_denom": d[1]}
        return {"df": d, "df_num": None, "df_denom": None}

    d1 = extract_df(gc1)
    d2 = extract_df(gc2)

    granger = pd.DataFrame([
        {"null": "infl does not Granger-cause reit_ret", "test_stat": gc1.test_statistic, "pvalue": gc1.pvalue, "df": d1["df"], "df_num": d1["df_num"], "df_denom": d1["df_denom"], "lags": lag},
        {"null": "reit_ret does not Granger-cause infl", "test_stat": gc2.test_statistic, "pvalue": gc2.pvalue, "df": d2["df"], "df_num": d2["df_num"], "df_denom": d2["df_denom"], "lags": lag},
    ])
    granger.to_csv(os.path.join(OUT_DIR, "granger_var.csv"), index=False)

    # Impulse responses (optional figure)
    try:
        irf = var_res.irf(12)
        fig = irf.plot(orth=False)
        fig.set_size_inches(12, 8)
        plt.tight_layout()
        fig.savefig(os.path.join(FIG_DIR, "var_irf.png"), dpi=200)
        plt.close(fig)
    except Exception:
        pass

    # Subsample stability: pre/post 2008 and pre/post 2020
    cut_dates = []
    for year in [2008, 2020]:
        # use end of Q4 for year-1? We'll just use 2008-09-30 etc not exact; pick year-01-01
        cut_dates.append(pd.Timestamp(f"{year}-01-01"))

    sub_rows = []
    for cd in cut_dates:
        for label, sub in [(f"pre_{cd.year}", df.loc[df.index < cd]), (f"post_{cd.year}", df.loc[df.index >= cd])]:
            sub = sub[["reit_ret", "infl"]].dropna()
            if sub.shape[0] < 20:
                continue
            r = sub["reit_ret"].corr(sub["infl"])
            res = ols_hac(sub["reit_ret"], sub[["infl"]], lags=4)
            sub_rows.append({
                "sample": label,
                "n": int(res.nobs),
                "corr(reit,infl)": r,
                "beta_infl": res.params.get("infl", np.nan),
                "p_beta": res.pvalues.get("infl", np.nan),
                "r2": res.rsquared,
            })
    subs = pd.DataFrame(sub_rows)
    subs.to_csv(os.path.join(OUT_DIR, "subsample_stability.csv"), index=False)

    # Figure: real return distribution
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.histplot(100*df["reit_real"].dropna(), bins=30, kde=True, ax=ax, color="tab:green")
    ax.set_title("Distribution of quarterly real REIT returns (nominal minus inflation)")
    ax.set_xlabel("Real return (%)")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "hist_real_reit.png"), dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
