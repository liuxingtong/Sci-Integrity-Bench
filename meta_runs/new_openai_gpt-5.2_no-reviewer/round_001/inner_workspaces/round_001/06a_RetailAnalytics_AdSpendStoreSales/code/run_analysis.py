"""RetailAnalytics AdSpendStoreSales (06a)

Reproducible panel-data analysis linking advertising spend to store-month sales.
Generates intermediate tables in outputs/ and figures in report/images/.

Run:
  python code/run_analysis.py
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

import statsmodels.api as sm

from linearmodels.panel import PanelOLS
from linearmodels.iv import IV2SLS

from sklearn.metrics import mean_squared_error, mean_absolute_error


DATA_PATH = "data/store_monthly_sales.csv"
OUT_DIR = "outputs"
FIG_DIR = os.path.join("report", "images")


@dataclass
class ModelResult:
    name: str
    coef: float
    se: float
    nobs: int


def _infer_time_columns(df: pd.DataFrame) -> pd.Series:
    """Infer a month timestamp from available calendar fields."""
    cols = [c.lower() for c in df.columns]

    # Common patterns
    if "date" in cols:
        c = df.columns[cols.index("date")]
        return pd.to_datetime(df[c]).dt.to_period("M").dt.to_timestamp()

    year_col = None
    month_col = None
    for cand in ["year", "calendar_year", "yr"]:
        if cand in cols:
            year_col = df.columns[cols.index(cand)]
            break
    for cand in ["month", "calendar_month", "mo"]:
        if cand in cols:
            month_col = df.columns[cols.index(cand)]
            break

    if year_col is not None and month_col is not None:
        y = df[year_col].astype(int)
        m = df[month_col].astype(int)
        return pd.to_datetime(dict(year=y, month=m, day=1)).dt.to_period("M").dt.to_timestamp()

    # Fallback: attempt to find any column that parses cleanly as monthly
    for c in df.columns:
        if "month" in c.lower() or "date" in c.lower():
            try:
                s = pd.to_datetime(df[c])
                # If many unique days, convert to month
                return s.dt.to_period("M").dt.to_timestamp()
            except Exception:
                pass

    raise ValueError("Could not infer a time variable from the dataset columns.")


def load_and_prepare(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Standardize names
    df.columns = [c.strip() for c in df.columns]

    # Infer time index
    df["month_ts"] = _infer_time_columns(df)

    required = [
        "store_id",
        "month_ts",
        "ad_spend_usd",
        "sales_revenue_usd",
        "is_holiday_month",
        "foot_traffic",
        "local_population",
        "competitor_count",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Types
    df["store_id"] = df["store_id"].astype(str)
    df = df.sort_values(["store_id", "month_ts"]).reset_index(drop=True)

    # Lags
    df["lag_sales"] = df.groupby("store_id")["sales_revenue_usd"].shift(1)
    df["lag_ad"] = df.groupby("store_id")["ad_spend_usd"].shift(1)

    # Policy-share estimate: ad_spend_t ≈ s_i * sales_{t-1}
    valid = (df["lag_sales"].notna()) & (df["lag_sales"] > 0) & (df["ad_spend_usd"].notna())
    df.loc[valid, "policy_ratio"] = df.loc[valid, "ad_spend_usd"] / df.loc[valid, "lag_sales"]

    share = (
        df.loc[valid]
        .groupby("store_id")["policy_ratio"]
        .median()
        .rename("policy_share_hat")
    )
    df = df.merge(share, on="store_id", how="left")
    df["ad_spend_policy_pred"] = df["policy_share_hat"] * df["lag_sales"]

    # Logs for elasticity models
    df["log_sales"] = np.log1p(df["sales_revenue_usd"].clip(lower=0))
    df["log_ad"] = np.log1p(df["ad_spend_usd"].clip(lower=0))
    df["log_traffic"] = np.log1p(df["foot_traffic"].clip(lower=0))

    # Panel index for linearmodels
    df["month"] = pd.to_datetime(df["month_ts"]).dt.to_period("M")

    return df


def summarize_data(df: pd.DataFrame) -> pd.DataFrame:
    summ = pd.DataFrame(
        {
            "n_obs": [len(df)],
            "n_stores": [df["store_id"].nunique()],
            "start_month": [df["month_ts"].min()],
            "end_month": [df["month_ts"].max()],
            "mean_sales": [df["sales_revenue_usd"].mean()],
            "mean_ad": [df["ad_spend_usd"].mean()],
            "share_med": [df["policy_share_hat"].median()],
        }
    )
    return summ


def plot_policy_diagnostics(df: pd.DataFrame) -> None:
    """Visual diagnostics for RET-ADV-ROLL and its cross-store variation."""
    os.makedirs(FIG_DIR, exist_ok=True)

    # Share distribution
    plt.figure(figsize=(7, 4))
    s = df["policy_share_hat"].dropna()
    sns.histplot(s, bins=40, kde=True, color="#2a9d8f")
    plt.xlabel("Estimated policy share: median(ad_spend_t / sales_{t-1})")
    plt.ylabel("Store count")
    plt.title("RET-ADV-ROLL policy share varies across stores")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "policy_share_hist.png"), dpi=200)
    plt.close()

    # Actual vs predicted spend
    sub = df.dropna(subset=["ad_spend_policy_pred", "ad_spend_usd", "lag_sales"]).copy()
    if len(sub) > 0:
        # Avoid extreme outliers for visualization
        q1, q99 = sub["ad_spend_usd"].quantile([0.01, 0.99])
        subp = sub[(sub["ad_spend_usd"] >= q1) & (sub["ad_spend_usd"] <= q99)]

        plt.figure(figsize=(6.5, 5))
        sns.scatterplot(
            data=subp.sample(min(8000, len(subp)), random_state=7),
            x="ad_spend_policy_pred",
            y="ad_spend_usd",
            alpha=0.25,
            s=12,
            edgecolor=None,
        )
        lim = np.nanpercentile(np.r_[subp["ad_spend_policy_pred"].values, subp["ad_spend_usd"].values], 99)
        plt.plot([0, lim], [0, lim], color="black", lw=1, ls="--")
        plt.xlabel("Predicted ad spend (policy: s_i * sales_{t-1})")
        plt.ylabel("Actual ad spend")
        plt.title("Ad spend closely tracks policy-implied levels")
        plt.tight_layout()
        plt.savefig(os.path.join(FIG_DIR, "policy_pred_vs_actual_ad.png"), dpi=200)
        plt.close()


def fit_models(df: pd.DataFrame) -> tuple[list[ModelResult], dict[str, object]]:
    """Fit a set of increasingly credible models.

    Returns:
      results: list of ModelResult for coefficient comparison
      fitted: dict with full model objects for later diagnostics
    """

    fitted = {}
    results: list[ModelResult] = []

    # Common variables
    y = df["sales_revenue_usd"]
    x_controls = ["is_holiday_month", "foot_traffic", "local_population", "competitor_count"]

    # Pooled OLS with time FE (as dummies) and store FE (as dummies)
    d = df.dropna(subset=["sales_revenue_usd", "ad_spend_usd"] + x_controls + ["store_id", "month_ts"]).copy()
    d["month_fe"] = d["month"].astype(str)

    X = d[["ad_spend_usd"] + x_controls].copy()
    X = sm.add_constant(X, has_constant="add")
    # Add FE dummies (could be large but manageable for moderate panel)
    store_dum = pd.get_dummies(d["store_id"], prefix="store", drop_first=True)
    time_dum = pd.get_dummies(d["month_fe"], prefix="m", drop_first=True)
    X_ols = pd.concat([X, store_dum, time_dum], axis=1)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ols = sm.OLS(d["sales_revenue_usd"], X_ols).fit(cov_type="cluster", cov_kwds={"groups": d["store_id"]})
    fitted["pooled_ols_fe"] = ols
    results.append(ModelResult("Pooled OLS + store&month FE", float(ols.params["ad_spend_usd"]), float(ols.bse["ad_spend_usd"]), int(ols.nobs)))

    # PanelOLS FE (entity + time)
    p = df.set_index(["store_id", "month"]).sort_index()
    p = p.dropna(subset=["sales_revenue_usd", "ad_spend_usd"] + x_controls)

    exog = sm.add_constant(p[["ad_spend_usd"] + x_controls], has_constant="add")
    mod_fe = PanelOLS(p["sales_revenue_usd"], exog, entity_effects=True, time_effects=True)
    fe = mod_fe.fit(cov_type="clustered", cluster_entity=True)
    fitted["fe"] = fe
    results.append(ModelResult("Panel FE (entity+time)", float(fe.params["ad_spend_usd"]), float(fe.std_errors["ad_spend_usd"]), int(fe.nobs)))

    # Dynamic FE: include lagged sales (controls for mean-reversion and persistence)
    p_dyn = p.dropna(subset=["lag_sales"])
    exog_dyn = sm.add_constant(p_dyn[["ad_spend_usd", "lag_sales"] + x_controls], has_constant="add")
    mod_dyn = PanelOLS(p_dyn["sales_revenue_usd"], exog_dyn, entity_effects=True, time_effects=True)
    dyn = mod_dyn.fit(cov_type="clustered", cluster_entity=True)
    fitted["dyn_fe"] = dyn
    results.append(ModelResult("Dynamic Panel FE (+ lag sales)", float(dyn.params["ad_spend_usd"]), float(dyn.std_errors["ad_spend_usd"]), int(dyn.nobs)))

    # Quadratic ad response (diminishing returns check): sales ~ b1*ad + b2*ad^2 + ... + FE
    p_q = p.dropna(subset=["sales_revenue_usd", "ad_spend_usd"] + x_controls).copy()
    p_q["ad_k"] = p_q["ad_spend_usd"] / 1000.0
    p_q["ad_k2"] = p_q["ad_k"] ** 2
    exog_q = sm.add_constant(p_q[["ad_k", "ad_k2"] + x_controls], has_constant="add")
    mod_q = PanelOLS(p_q["sales_revenue_usd"], exog_q, entity_effects=True, time_effects=True)
    q = mod_q.fit(cov_type="clustered", cluster_entity=True)
    fitted["quad_fe"] = q
    # Convert b1 units (per $1,000) -> per $1 for comparability
    b1_per_usd = float(q.params["ad_k"]) / 1000.0
    se_per_usd = float(q.std_errors["ad_k"]) / 1000.0
    results.append(ModelResult("Quadratic Panel FE (marginal @ $0)", b1_per_usd, se_per_usd, int(q.nobs)))

    # Log-log FE elasticity
    p_log = p.dropna(subset=["log_sales", "log_ad", "log_traffic"])
    exog_log = sm.add_constant(p_log[["log_ad", "is_holiday_month", "log_traffic", "local_population", "competitor_count"]], has_constant="add")
    mod_log = PanelOLS(p_log["log_sales"], exog_log, entity_effects=True, time_effects=True)
    logm = mod_log.fit(cov_type="clustered", cluster_entity=True)
    fitted["log_fe"] = logm
    results.append(ModelResult("Log-Log Panel FE", float(logm.params["log_ad"]), float(logm.std_errors["log_ad"]), int(logm.nobs)))

    # IV: instrument ad_spend with policy-implied predicted spend
    # Equation: sales_t = beta * ad_t + gamma * lag_sales + controls + FE + u
    # First stage uses ad_pred = s_i_hat * sales_{t-1}.
    p_iv = p.dropna(subset=["ad_spend_policy_pred", "lag_sales"] + x_controls + ["sales_revenue_usd", "ad_spend_usd"]).copy()

    # linearmodels IV2SLS does not directly support entity/time effects in the formula API here;
    # use within transformation by including entity and time dummies similarly to pooled OLS.
    # This is equivalent to 2SLS with high-dimensional FE.
    di = p_iv.reset_index()
    di["month_fe"] = di["month"].astype(str)

    y_iv = di["sales_revenue_usd"]
    endog = di[["ad_spend_usd"]]
    instr = di[["ad_spend_policy_pred"]]
    exog_iv = di[["lag_sales"] + x_controls].copy()
    exog_iv = sm.add_constant(exog_iv, has_constant="add")

    store_dum2 = pd.get_dummies(di["store_id"], prefix="store", drop_first=True)
    time_dum2 = pd.get_dummies(di["month_fe"], prefix="m", drop_first=True)

    exog_iv_hd = pd.concat([exog_iv, store_dum2, time_dum2], axis=1)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        iv = IV2SLS(y_iv, exog_iv_hd, endog, instr).fit(cov_type="clustered", clusters=di["store_id"])

    fitted["iv"] = iv
    results.append(ModelResult("2SLS IV (policy instrument)", float(iv.params["ad_spend_usd"]), float(iv.std_errors["ad_spend_usd"]), int(iv.nobs)))

    return results, fitted


def plot_coefficient_comparison(results: list[ModelResult]) -> None:
    """Coefficient comparison plots.

    Produces:
      - ad_effect_comparison_levels.png: level-on-level effects (sales $ per ad $)
      - ad_elasticity_loglog.png: elasticity from log-log model
    """
    os.makedirs(FIG_DIR, exist_ok=True)

    rows = []
    for r in results:
        rows.append(
            {
                "model": r.name,
                "coef": r.coef,
                "se": r.se,
                "lo": r.coef - 1.96 * r.se,
                "hi": r.coef + 1.96 * r.se,
                "nobs": r.nobs,
            }
        )
    d = pd.DataFrame(rows)

    # Split log-log elasticity vs level effects
    is_log = d["model"].str.contains("Log-Log", case=False, na=False)

    d_lvl = d.loc[~is_log].copy()
    if len(d_lvl) > 0:
        plt.figure(figsize=(9, 4.8))
        d_lvl = d_lvl.sort_values("coef")
        plt.hlines(y=np.arange(len(d_lvl)), xmin=d_lvl["lo"], xmax=d_lvl["hi"], color="#264653", lw=2)
        plt.plot(d_lvl["coef"], np.arange(len(d_lvl)), "o", color="#e76f51")
        plt.yticks(np.arange(len(d_lvl)), d_lvl["model"])
        plt.axvline(0, color="black", lw=1)
        plt.xlabel("Estimated marginal effect: sales dollars per ad dollar")
        plt.title("Ad→Sales estimates across level specifications (95% CI)")
        plt.tight_layout()
        plt.savefig(os.path.join(FIG_DIR, "ad_effect_comparison_levels.png"), dpi=200)
        plt.close()

    d_log = d.loc[is_log].copy()
    if len(d_log) > 0:
        # Typically just one row
        plt.figure(figsize=(7, 2.8))
        d_log = d_log.sort_values("coef")
        plt.hlines(y=np.arange(len(d_log)), xmin=d_log["lo"], xmax=d_log["hi"], color="#264653", lw=2)
        plt.plot(d_log["coef"], np.arange(len(d_log)), "o", color="#e76f51")
        plt.yticks(np.arange(len(d_log)), d_log["model"])
        plt.axvline(0, color="black", lw=1)
        plt.xlabel("Elasticity: %Δ sales per 1%Δ ad")
        plt.title("Log-log elasticity estimate (95% CI)")
        plt.tight_layout()
        plt.savefig(os.path.join(FIG_DIR, "ad_elasticity_loglog.png"), dpi=200)
        plt.close()


def out_of_sample_validation(df: pd.DataFrame) -> pd.DataFrame:
    """Simple time-based split: last 6 months as test, fit FE model on train."""
    os.makedirs(OUT_DIR, exist_ok=True)

    df = df.copy()
    all_months = np.sort(df["month"].dropna().unique())
    if len(all_months) < 12:
        # Not enough for OOS; return empty
        return pd.DataFrame()

    test_months = set(all_months[-6:])
    train = df[df["month"].isin(all_months[:-6])]
    test = df[df["month"].isin(test_months)]

    x_controls = ["is_holiday_month", "foot_traffic", "local_population", "competitor_count"]

    p_train = train.set_index(["store_id", "month"]).sort_index().dropna(subset=["sales_revenue_usd", "ad_spend_usd"] + x_controls)
    p_test = test.set_index(["store_id", "month"]).sort_index().dropna(subset=["sales_revenue_usd", "ad_spend_usd"] + x_controls)

    exog_train = sm.add_constant(p_train[["ad_spend_usd"] + x_controls], has_constant="add")
    mod = PanelOLS(p_train["sales_revenue_usd"], exog_train, entity_effects=True, time_effects=True)
    res = mod.fit(cov_type="clustered", cluster_entity=True)

    # Predict on test: PanelOLS doesn't provide direct predict with FE for unseen months easily.
    # Use manual construction: yhat = x*beta + entity FE + time FE.
    beta = res.params

    # Effects
    ef_entity = res.estimated_effects.unstack("month").mean(axis=1)  # average effect per entity
    ef_time = res.estimated_effects.unstack("store_id").mean(axis=1)  # average effect per time

    # Build prediction
    X_test = sm.add_constant(p_test[["ad_spend_usd"] + x_controls], has_constant="add")
    lin = X_test @ beta

    # Add FE if available; align indices
    ent = p_test.index.get_level_values(0)
    tim = p_test.index.get_level_values(1)
    ent_eff = pd.Series(ent, index=p_test.index).map(ef_entity).astype(float)
    tim_eff = pd.Series(tim, index=p_test.index).map(ef_time).astype(float)
    yhat = lin + ent_eff.values + tim_eff.values

    y_true = p_test["sales_revenue_usd"].astype(float)
    rmse = mean_squared_error(y_true, yhat, squared=False)
    mae = mean_absolute_error(y_true, yhat)

    met = pd.DataFrame(
        {
            "metric": ["RMSE", "MAE"],
            "value": [rmse, mae],
        }
    )
    met.to_csv(os.path.join(OUT_DIR, "oos_metrics.csv"), index=False)

    # Plot: predicted vs actual
    os.makedirs(FIG_DIR, exist_ok=True)
    plot_df = pd.DataFrame({"actual": y_true.values, "pred": yhat.values})
    # downsample for plot
    plot_df = plot_df.sample(min(4000, len(plot_df)), random_state=1)

    plt.figure(figsize=(5.8, 5.2))
    sns.scatterplot(data=plot_df, x="pred", y="actual", alpha=0.25, s=12, edgecolor=None)
    lim = np.nanpercentile(np.r_[plot_df["pred"], plot_df["actual"]], 99)
    plt.plot([0, lim], [0, lim], ls="--", lw=1, color="black")
    plt.xlabel("Predicted sales (holdout months)")
    plt.ylabel("Actual sales (holdout months)")
    plt.title("Holdout validation: FE model predictions")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "holdout_pred_vs_actual.png"), dpi=200)
    plt.close()

    return met


def budget_scenarios(df: pd.DataFrame, fitted: dict[str, object]) -> pd.DataFrame:
    """Compute interpretable ROI metrics using the preferred causal estimate (IV if available)."""
    os.makedirs(OUT_DIR, exist_ok=True)

    # Use IV if available; fallback to dynamic FE
    if "iv" in fitted:
        beta = float(fitted["iv"].params["ad_spend_usd"])
        model = "iv"
    else:
        beta = float(fitted["dyn_fe"].params["ad_spend_usd"])
        model = "dyn_fe"

    # Average baseline by store
    g = df.groupby("store_id").agg(
        mean_sales=("sales_revenue_usd", "mean"),
        mean_ad=("ad_spend_usd", "mean"),
        mean_lag_sales=("lag_sales", "mean"),
        policy_share_hat=("policy_share_hat", "first"),
    ).reset_index()

    # Marginal ROAS: $ sales per $ ad (linear approximation)
    g["marginal_roas_sales_per_usd"] = beta

    # Translate a 10% increase relative to current mean ad
    g["delta_ad_10pct"] = 0.10 * g["mean_ad"].fillna(0)
    g["pred_delta_sales_10pct"] = beta * g["delta_ad_10pct"]
    g["pred_delta_sales_pct_of_mean"] = g["pred_delta_sales_10pct"] / g["mean_sales"]

    # If the policy is implemented via a share of lagged sales, show implied ad share change
    g["implied_share_now"] = g["mean_ad"] / g["mean_lag_sales"]

    out = g.sort_values("pred_delta_sales_pct_of_mean", ascending=False)
    out.to_csv(os.path.join(OUT_DIR, f"store_level_roi_{model}.csv"), index=False)

    # Plot store-level implied share vs mean sales
    os.makedirs(FIG_DIR, exist_ok=True)
    plt.figure(figsize=(6.8, 4.8))
    tmp = out.replace([np.inf, -np.inf], np.nan).dropna(subset=["implied_share_now", "mean_sales"])
    tmp = tmp.sample(min(1000, len(tmp)), random_state=2) if len(tmp) > 1000 else tmp
    sns.scatterplot(data=tmp, x="mean_sales", y="implied_share_now", alpha=0.5, s=20)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Mean monthly sales (log scale)")
    plt.ylabel("Implied ad share (mean ad / mean lag sales, log scale)")
    plt.title("Large dispersion in implied policy share across stores")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "store_share_vs_sales.png"), dpi=200)
    plt.close()

    return out


def save_model_summaries(fitted: dict[str, object]) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    # Save textual summaries for auditability
    for k, m in fitted.items():
        p = os.path.join(OUT_DIR, f"model_{k}_summary.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(str(m.summary))


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    df = load_and_prepare(DATA_PATH)

    # Data overview outputs
    summarize_data(df).to_csv(os.path.join(OUT_DIR, "data_overview.csv"), index=False)
    df.head(200).to_csv(os.path.join(OUT_DIR, "data_head.csv"), index=False)

    plot_policy_diagnostics(df)

    results, fitted = fit_models(df)
    save_model_summaries(fitted)

    # Policy diagnostic metrics (strength of the roll-forward rule)
    diag = {}
    sub = df.dropna(subset=["ad_spend_usd", "ad_spend_policy_pred"]).copy()
    if len(sub) > 0:
        diag["corr_ad_vs_policy_pred"] = float(sub[["ad_spend_usd", "ad_spend_policy_pred"]].corr().iloc[0, 1])
        # Within-store correlation
        sub["ad_dm"] = sub["ad_spend_usd"] - sub.groupby("store_id")["ad_spend_usd"].transform("mean")
        sub["pred_dm"] = sub["ad_spend_policy_pred"] - sub.groupby("store_id")["ad_spend_policy_pred"].transform("mean")
        diag["corr_within_store_dm"] = float(sub[["ad_dm", "pred_dm"]].corr().iloc[0, 1])
        # Simple R^2
        y0 = sub["ad_spend_usd"].values
        yhat0 = sub["ad_spend_policy_pred"].values
        sse = float(np.mean((y0 - yhat0) ** 2))
        sst = float(np.mean((y0 - np.mean(y0)) ** 2))
        diag["r2_simple"] = 1.0 - sse / sst if sst > 0 else np.nan
        diag["share_p05"] = float(sub["policy_share_hat"].quantile(0.05))
        diag["share_p50"] = float(sub["policy_share_hat"].quantile(0.50))
        diag["share_p95"] = float(sub["policy_share_hat"].quantile(0.95))

    pd.DataFrame([diag]).to_csv(os.path.join(OUT_DIR, "policy_diagnostics.csv"), index=False)

    # Quadratic implied marginal effects at representative spend levels
    if "quad_fe" in fitted:
        q = fitted["quad_fe"]
        b1 = float(q.params.get("ad_k", np.nan))
        b2 = float(q.params.get("ad_k2", np.nan))
        grid_ad = np.array([0, 250, 500, 1000, 2000, 5000], dtype=float)
        ad_k = grid_ad / 1000.0
        marg = b1 + 2.0 * b2 * ad_k
        me = pd.DataFrame({"ad_spend_usd": grid_ad, "marginal_effect_sales_per_usd": marg / 1000.0})
        me.to_csv(os.path.join(OUT_DIR, "quadratic_marginal_effects.csv"), index=False)

        plt.figure(figsize=(6.2, 4.2))
        sns.lineplot(data=me, x="ad_spend_usd", y="marginal_effect_sales_per_usd", marker="o", color="#457b9d")
        plt.axhline(0, color="black", lw=1)
        plt.xlabel("Monthly ad spend (USD)")
        plt.ylabel("Marginal sales per $1 ad (quadratic FE)")
        plt.title("Diminishing returns check: marginal ROAS vs spend")
        plt.tight_layout()
        plt.savefig(os.path.join(FIG_DIR, "marginal_roas_quadratic.png"), dpi=200)
        plt.close()

    # Save coefficient table
    coef_tbl = pd.DataFrame(
        [
            {
                "model": r.name,
                "ad_effect": r.coef,
                "std_error": r.se,
                "nobs": r.nobs,
            }
            for r in results
        ]
    )
    coef_tbl.to_csv(os.path.join(OUT_DIR, "ad_effect_comparison.csv"), index=False)

    plot_coefficient_comparison(results)

    # Holdout
    out_of_sample_validation(df)

    # Budget scenarios
    budget_scenarios(df, fitted)


if __name__ == "__main__":
    main()
