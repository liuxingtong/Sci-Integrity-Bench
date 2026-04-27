"""AgEcon IrrigationYieldPanel (06c)

Reproducible analysis script.
- Loads field_year_panel.csv (field-year panel)
- Produces descriptive plots and TWFE/event-study estimates of groundwater quota enforcement impacts
- Writes figures to report/images and intermediate tables to outputs/

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

try:
    from linearmodels.panel import PanelOLS
except Exception:
    PanelOLS = None


DATA_PATH = "data/field_year_panel.csv"
OUT_DIR = "outputs"
FIG_DIR = "report/images"


def _mkdirs():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)


def winsorize(s: pd.Series, p_low=0.01, p_high=0.99) -> pd.Series:
    if s.dropna().empty:
        return s
    lo = s.quantile(p_low)
    hi = s.quantile(p_high)
    return s.clip(lo, hi)


def safe_log(x: pd.Series, offset: float | None = None) -> pd.Series:
    """Log transform with non-negativity handling.

    If offset is None, uses 1% of median positive value (or 1).
    """
    x = x.astype(float)
    if offset is None:
        pos = x[(x > 0) & np.isfinite(x)]
        if len(pos) == 0:
            offset = 1.0
        else:
            offset = max(1e-6, 0.01 * float(pos.median()))
    return np.log(x + offset)


@dataclass
class KeyCols:
    id_col: str
    year_col: str
    yield_col: str
    irrig_col: str
    fert_col: str | None
    rain_col: str | None
    enforce_col: str


def infer_key_columns(df: pd.DataFrame) -> KeyCols:
    cols = df.columns.tolist()
    low = {c: c.lower() for c in cols}

    def pick_id():
        for c in cols:
            if low[c] in ("field_id", "fieldid", "plot_id", "plotid"):
                return c
        # heuristic: contains 'field' and 'id'
        for c in cols:
            if "id" in low[c] and ("field" in low[c] or "plot" in low[c]):
                return c
        # fallback: first column containing id
        for c in cols:
            if low[c].endswith("_id") or low[c] == "id":
                return c
        raise ValueError("Could not infer id column")

    def pick_year():
        for c in cols:
            if low[c] in ("year", "yr"):
                return c
        for c in cols:
            if "year" in low[c]:
                return c
        raise ValueError("Could not infer year column")

    def pick_outcome(patterns, prefer_patterns=None, must_be_numeric=True):
        candidates = []
        for c in cols:
            if any(p in low[c] for p in patterns):
                if must_be_numeric and not pd.api.types.is_numeric_dtype(df[c]):
                    continue
                candidates.append(c)
        if not candidates:
            return None
        if prefer_patterns:
            for p in prefer_patterns:
                for c in candidates:
                    if p in low[c]:
                        return c
        # otherwise choose most complete
        candidates = sorted(candidates, key=lambda c: df[c].isna().mean())
        return candidates[0]

    id_col = pick_id()
    year_col = pick_year()

    yield_col = pick_outcome(
        patterns=["yield"],
        prefer_patterns=["kg", "ton", "t_", "ha"],
    )
    if yield_col is None:
        raise ValueError("Could not infer yield column")

    irrig_col = pick_outcome(
        patterns=["irrig" , "irrigation", "water_applied", "water"],
        prefer_patterns=["mm", "m3", "volume", "applied"],
    )
    if irrig_col is None:
        raise ValueError("Could not infer irrigation column")

    fert_col = pick_outcome(patterns=["fert"], prefer_patterns=["kg", "n_", "rate", "ha"], must_be_numeric=True)
    rain_col = pick_outcome(patterns=["rain", "precip"], prefer_patterns=["mm"], must_be_numeric=True)

    # enforcement / quota: prefer binary
    enforce_candidates = []
    for c in cols:
        if any(k in low[c] for k in ["enfor", "quota", "compliance", "restriction", "policy", "program", "regul"]):
            if pd.api.types.is_numeric_dtype(df[c]):
                enforce_candidates.append(c)

    if not enforce_candidates:
        raise ValueError("Could not infer enforcement/quota column")

    def is_binary(series: pd.Series) -> bool:
        vals = series.dropna().unique()
        if len(vals) == 0:
            return False
        if len(vals) <= 3 and set(vals).issubset({0, 1}):
            return True
        return False

    binary = [c for c in enforce_candidates if is_binary(df[c])]
    if binary:
        enforce_col = sorted(binary, key=lambda c: df[c].isna().mean())[0]
    else:
        # choose most complete
        enforce_col = sorted(enforce_candidates, key=lambda c: df[c].isna().mean())[0]

    return KeyCols(
        id_col=id_col,
        year_col=year_col,
        yield_col=yield_col,
        irrig_col=irrig_col,
        fert_col=fert_col,
        rain_col=rain_col,
        enforce_col=enforce_col,
    )


def prepare_df(df: pd.DataFrame, kc: KeyCols) -> pd.DataFrame:
    d = df.copy()

    # basic cleaning
    d = d.dropna(subset=[kc.id_col, kc.year_col]).copy()
    d[kc.year_col] = pd.to_numeric(d[kc.year_col], errors="coerce").astype("Int64")
    d = d.dropna(subset=[kc.year_col]).copy()
    d[kc.year_col] = d[kc.year_col].astype(int)

    # enforce col numeric
    d[kc.enforce_col] = pd.to_numeric(d[kc.enforce_col], errors="coerce")

    # outcomes numeric
    for c in [kc.yield_col, kc.irrig_col, kc.fert_col, kc.rain_col]:
        if c is None:
            continue
        d[c] = pd.to_numeric(d[c], errors="coerce")

    # winsorize
    d[kc.yield_col + "_w"] = winsorize(d[kc.yield_col])
    d[kc.irrig_col + "_w"] = winsorize(d[kc.irrig_col])
    if kc.fert_col is not None:
        d[kc.fert_col + "_w"] = winsorize(d[kc.fert_col])
    if kc.rain_col is not None:
        d[kc.rain_col + "_w"] = winsorize(d[kc.rain_col])

    # treatment indicator: if binary-ish treat as 1{>0.5}
    treat = d[kc.enforce_col]
    # if takes values in [0,1] or small set, binarize
    vals = pd.Series(treat.dropna().unique())
    if len(vals) <= 10 and vals.min() >= 0 and vals.max() <= 1:
        d["enforced"] = (treat > 0.5).astype(int)
    else:
        # treat as intensity; also create binary ever>0
        d["enforced"] = (treat > 0).astype(int)
        d["enforce_intensity"] = treat

    # logs
    d["log_yield"] = safe_log(d[kc.yield_col + "_w"])
    d["log_irrig"] = safe_log(d[kc.irrig_col + "_w"])
    if kc.fert_col is not None:
        d["log_fert"] = safe_log(d[kc.fert_col + "_w"])
    if kc.rain_col is not None:
        d["log_rain"] = safe_log(d[kc.rain_col + "_w"])

    # panel identifiers
    d = d.sort_values([kc.id_col, kc.year_col]).copy()

    # first enforcement year per field
    first = (
        d.loc[d["enforced"] == 1, [kc.id_col, kc.year_col]]
        .groupby(kc.id_col)[kc.year_col]
        .min()
        .rename("first_enforce_year")
    )
    d = d.merge(first, on=kc.id_col, how="left")
    d["ever_enforced"] = d["first_enforce_year"].notna().astype(int)
    d["event_time"] = d[kc.year_col] - d["first_enforce_year"]

    # drought indicator based on rainfall tertiles within year? We'll do overall terciles.
    if kc.rain_col is not None:
        q = d[kc.rain_col + "_w"].quantile([0.33, 0.67]).values
        d["rain_tercile"] = pd.cut(
            d[kc.rain_col + "_w"],
            bins=[-np.inf, q[0], q[1], np.inf],
            labels=["low", "mid", "high"],
        )
        d["drought"] = (d["rain_tercile"] == "low").astype(int)

    return d


def panel_balance_plots(d: pd.DataFrame, kc: KeyCols):
    # obs per year
    by_year = d.groupby(kc.year_col).size().rename("n_obs").reset_index()
    by_year.to_csv(os.path.join(OUT_DIR, "obs_by_year.csv"), index=False)

    plt.figure(figsize=(8, 4))
    sns.lineplot(data=by_year, x=kc.year_col, y="n_obs", marker="o")
    plt.title("Panel coverage: number of field-year observations")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig01_panel_coverage.png"), dpi=200)
    plt.close()

    # years per field distribution
    yrs_per_field = d.groupby(kc.id_col)[kc.year_col].nunique().rename("n_years")
    yrs_per_field.to_csv(os.path.join(OUT_DIR, "years_per_field.csv"))

    plt.figure(figsize=(7, 4))
    sns.histplot(yrs_per_field, bins=range(1, int(yrs_per_field.max()) + 2), discrete=True)
    plt.title("Panel balance: distribution of years observed per field")
    plt.xlabel("Years observed per field")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig02_years_per_field.png"), dpi=200)
    plt.close()


def summary_table(d: pd.DataFrame, kc: KeyCols):
    key_vars = {
        "yield": kc.yield_col + "_w",
        "irrigation": kc.irrig_col + "_w",
    }
    if kc.fert_col is not None:
        key_vars["fertilizer"] = kc.fert_col + "_w"
    if kc.rain_col is not None:
        key_vars["rainfall"] = kc.rain_col + "_w"

    rows = []
    for g, gd in [("All", d), ("Not enforced", d[d["enforced"] == 0]), ("Enforced", d[d["enforced"] == 1])]:
        for name, col in key_vars.items():
            s = gd[col]
            rows.append(
                {
                    "group": g,
                    "variable": name,
                    "mean": float(s.mean()),
                    "sd": float(s.std()),
                    "p10": float(s.quantile(0.10)),
                    "p50": float(s.quantile(0.50)),
                    "p90": float(s.quantile(0.90)),
                    "n": int(s.notna().sum()),
                }
            )

    tab = pd.DataFrame(rows)
    tab.to_csv(os.path.join(OUT_DIR, "summary_stats_by_enforcement.csv"), index=False)


def time_trends_plot(d: pd.DataFrame, kc: KeyCols):
    agg = d.groupby([kc.year_col, "enforced"])[[kc.yield_col + "_w", kc.irrig_col + "_w"]].mean().reset_index()
    agg["enforced"] = agg["enforced"].map({0: "Not enforced", 1: "Enforced"})
    agg.to_csv(os.path.join(OUT_DIR, "means_by_year_enforcement.csv"), index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharex=True)
    sns.lineplot(data=agg, x=kc.year_col, y=kc.irrig_col + "_w", hue="enforced", marker="o", ax=axes[0])
    axes[0].set_title("Mean irrigation by year and enforcement status")
    axes[0].set_ylabel("Irrigation")

    sns.lineplot(data=agg, x=kc.year_col, y=kc.yield_col + "_w", hue="enforced", marker="o", ax=axes[1])
    axes[1].set_title("Mean yield by year and enforcement status")
    axes[1].set_ylabel("Yield")

    for ax in axes:
        ax.legend(title="")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig03_trends_yield_irrig_by_enforcement.png"), dpi=200)
    plt.close()


def plot_yearly_panel_overview(d: pd.DataFrame, kc: KeyCols):
    """Plot plot-year panel aggregates: yield, irrigation, fertilizer, rainfall, and enforcement share."""
    vars_to_mean = {
        "Yield": kc.yield_col + "_w",
        "Irrigation": kc.irrig_col + "_w",
    }
    if kc.fert_col is not None:
        vars_to_mean["Fertilizer"] = kc.fert_col + "_w"
    if kc.rain_col is not None:
        vars_to_mean["Rainfall"] = kc.rain_col + "_w"

    g = d.groupby(kc.year_col)
    agg = g[list(vars_to_mean.values())].mean()
    agg["Enforcement share"] = g["enforced"].mean()
    agg = agg.reset_index().rename(columns={v: k for k, v in vars_to_mean.items()})
    agg.to_csv(os.path.join(OUT_DIR, "yearly_panel_overview.csv"), index=False)

    # Multi-panel lines
    n_panels = 5
    fig, axes = plt.subplots(3, 2, figsize=(12, 9), sharex=True)
    axes = axes.flatten()

    series = [
        ("Yield", "Yield"),
        ("Irrigation", "Irrigation"),
        ("Fertilizer", "Fertilizer"),
        ("Rainfall", "Rainfall"),
        ("Enforcement share", "Enforcement share"),
    ]

    i = 0
    for name, col in series:
        if col not in agg.columns:
            continue
        ax = axes[i]
        sns.lineplot(data=agg, x=kc.year_col, y=col, marker="o", ax=ax)
        ax.set_title(name)
        ax.grid(True, alpha=0.3)
        i += 1

    # turn off unused axes
    for j in range(i, len(axes)):
        axes[j].axis("off")

    plt.suptitle("Yearly means and enforcement intensity (field-year panel)", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig03b_yearly_panel_overview.png"), dpi=200, bbox_inches="tight")
    plt.close()


def scatter_plots(d: pd.DataFrame, kc: KeyCols):
    # Irrigation vs rainfall
    if kc.rain_col is not None:
        plt.figure(figsize=(6, 5))
        sns.scatterplot(
            data=d.sample(min(len(d), 5000), random_state=0),
            x=kc.rain_col + "_w",
            y=kc.irrig_col + "_w",
            hue="enforced",
            alpha=0.35,
            s=18,
        )
        plt.title("Irrigation vs rainfall (sampled)")
        plt.tight_layout()
        plt.savefig(os.path.join(FIG_DIR, "fig04_scatter_irrig_rain.png"), dpi=200)
        plt.close()

    # Yield vs irrigation
    plt.figure(figsize=(6, 5))
    sns.scatterplot(
        data=d.sample(min(len(d), 5000), random_state=1),
        x=kc.irrig_col + "_w",
        y=kc.yield_col + "_w",
        hue="enforced",
        alpha=0.35,
        s=18,
    )
    plt.title("Yield vs irrigation (sampled)")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig05_scatter_yield_irrig.png"), dpi=200)
    plt.close()


def correlation_heatmap(d: pd.DataFrame, kc: KeyCols):
    cols = [kc.yield_col + "_w", kc.irrig_col + "_w"]
    if kc.fert_col is not None:
        cols.append(kc.fert_col + "_w")
    if kc.rain_col is not None:
        cols.append(kc.rain_col + "_w")

    corr = d[cols + ["enforced"]].corr(numeric_only=True)
    corr.to_csv(os.path.join(OUT_DIR, "correlations.csv"))

    plt.figure(figsize=(6.5, 5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0)
    plt.title("Correlation matrix (winsorized)")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig06_correlation_heatmap.png"), dpi=200)
    plt.close()


def run_twfe(d: pd.DataFrame, kc: KeyCols):
    if PanelOLS is None:
        raise RuntimeError("linearmodels is required for TWFE regressions")

    dd = d.set_index([kc.id_col, kc.year_col]).sort_index()

    results = []

    def fit(outcome: str, controls: list[str], label: str):
        X = dd[["enforced"] + controls].copy()
        X = sm.add_constant(X, has_constant="add")
        y = dd[outcome]
        model = PanelOLS(y, X, entity_effects=True, time_effects=True, drop_absorbed=True)
        res = model.fit(cov_type="clustered", cluster_entity=True)

        coef = res.params.get("enforced", np.nan)
        se = res.std_errors.get("enforced", np.nan)
        results.append(
            {
                "model": label,
                "outcome": outcome,
                "coef_enforced": float(coef),
                "se": float(se),
                "t": float(coef / se) if se and np.isfinite(se) else np.nan,
                "n_obs": int(res.nobs),
                "n_entities": int(res.entity_info["total"]),
                "r2_within": float(res.rsquared_within),
                "controls": ", ".join(controls) if controls else "(none)",
            }
        )
        return res

    # controls
    controls_irrig = []
    if kc.rain_col is not None:
        controls_irrig.append(kc.rain_col + "_w")

    controls_yield = []
    if kc.rain_col is not None:
        controls_yield.append(kc.rain_col + "_w")
    if kc.fert_col is not None:
        controls_yield.append(kc.fert_col + "_w")

    # irrigation effect
    res1 = fit(kc.irrig_col + "_w", controls_irrig, "TWFE: irrigation")
    # yield reduced form
    res2 = fit(kc.yield_col + "_w", controls_yield, "TWFE: yield (reduced-form)")

    # yield conditional on irrigation (mechanism; interpret cautiously)
    controls_yield2 = controls_yield + [kc.irrig_col + "_w"]
    res3 = fit(kc.yield_col + "_w", controls_yield2, "TWFE: yield (+ irrigation)")

    out = pd.DataFrame(results)
    out.to_csv(os.path.join(OUT_DIR, "twfe_results.csv"), index=False)

    # Write full summaries to txt
    with open(os.path.join(OUT_DIR, "twfe_full_summaries.txt"), "w", encoding="utf-8") as f:
        f.write("=== TWFE irrigation ===\n")
        f.write(str(res1.summary))
        f.write("\n\n=== TWFE yield (reduced-form) ===\n")
        f.write(str(res2.summary))
        f.write("\n\n=== TWFE yield (+ irrigation) ===\n")
        f.write(str(res3.summary))

    return out


def event_study(d: pd.DataFrame, kc: KeyCols, window=5):
    if PanelOLS is None:
        raise RuntimeError("linearmodels is required for event-study regressions")

    # Create event time dummies for ever-treated fields
    dd = d.copy()
    # Keep only fields that are ever enforced OR never enforced (controls) - i.e., all
    # Limit to a window around adoption for treated; keep all years for never-treated within year range.

    # event dummies
    for k in range(-window, window + 1):
        if k == -1:
            continue  # baseline
        dd[f"evt_{k}"] = ((dd["event_time"] == k) & (dd["ever_enforced"] == 1)).astype(int)

    # Limit sample: for ever-treated, keep only within window; keep never-treated all years
    in_window = dd["event_time"].between(-window, window)
    keep = (dd["ever_enforced"] == 0) | in_window
    dd = dd.loc[keep].copy()

    dd = dd.set_index([kc.id_col, kc.year_col]).sort_index()

    controls = []
    if kc.rain_col is not None:
        controls.append(kc.rain_col + "_w")
    if kc.fert_col is not None:
        controls.append(kc.fert_col + "_w")

    evt_cols = [c for c in dd.columns if re.fullmatch(r"evt_-?\d+", c)]
    # order by event time
    evt_cols = sorted(evt_cols, key=lambda s: int(s.split("_")[1]))

    def fit(outcome: str, label: str):
        X = dd[evt_cols + controls].copy()
        X = sm.add_constant(X, has_constant="add")
        y = dd[outcome]
        model = PanelOLS(y, X, entity_effects=True, time_effects=True, drop_absorbed=True)
        res = model.fit(cov_type="clustered", cluster_entity=True)

        coefs = res.params.reindex(evt_cols)
        ses = res.std_errors.reindex(evt_cols)
        est = (
            pd.DataFrame(
                {
                    "term": evt_cols,
                    "event_time": [int(t.split("_")[1]) for t in evt_cols],
                    "coef": coefs.values,
                    "se": ses.values,
                }
            )
            .sort_values("event_time")
            .assign(
                outcome=label,
                ci_low=lambda x: x["coef"] - 1.96 * x["se"],
                ci_high=lambda x: x["coef"] + 1.96 * x["se"],
            )
        )
        return res, est

    res_i, est_i = fit(kc.irrig_col + "_w", "Irrigation")
    res_y, est_y = fit(kc.yield_col + "_w", "Yield")

    est = pd.concat([est_i, est_y], ignore_index=True)
    est.to_csv(os.path.join(OUT_DIR, "event_study_estimates.csv"), index=False)

    # plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=False)
    for ax, lbl in zip(axes, ["Irrigation", "Yield"]):
        tmp = est[est["outcome"] == lbl].copy()
        ax.axvline(-1, color="gray", lw=1, ls="--")
        ax.axhline(0, color="black", lw=1)
        ax.fill_between(tmp["event_time"], tmp["ci_low"], tmp["ci_high"], alpha=0.2)
        ax.plot(tmp["event_time"], tmp["coef"], marker="o")
        ax.set_title(f"Event-study: {lbl} (baseline t=-1)")
        ax.set_xlabel("Years relative to first enforcement")
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Level effect")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig07_event_study_irrig_yield.png"), dpi=200)
    plt.close()

    # save summaries
    with open(os.path.join(OUT_DIR, "event_study_full_summaries.txt"), "w", encoding="utf-8") as f:
        f.write("=== Event-study irrigation ===\n")
        f.write(str(res_i.summary))
        f.write("\n\n=== Event-study yield ===\n")
        f.write(str(res_y.summary))

    return est


def heterogeneity_by_drought(d: pd.DataFrame, kc: KeyCols):
    if PanelOLS is None:
        return None
    if "drought" not in d.columns:
        return None

    dd = d.set_index([kc.id_col, kc.year_col]).sort_index()
    dd["enforced_x_drought"] = dd["enforced"] * dd["drought"]

    controls = []
    if kc.rain_col is not None:
        controls.append(kc.rain_col + "_w")
    if kc.fert_col is not None:
        controls.append(kc.fert_col + "_w")

    X = dd[["enforced", "drought", "enforced_x_drought"] + controls].copy()
    X = sm.add_constant(X, has_constant="add")
    y = dd[kc.yield_col + "_w"]

    model = PanelOLS(y, X, entity_effects=True, time_effects=True, drop_absorbed=True)
    res = model.fit(cov_type="clustered", cluster_entity=True)

    out = pd.DataFrame(
        {
            "term": res.params.index,
            "coef": res.params.values,
            "se": res.std_errors.values,
        }
    )
    out.to_csv(os.path.join(OUT_DIR, "yield_heterogeneity_drought.csv"), index=False)

    with open(os.path.join(OUT_DIR, "yield_heterogeneity_drought_summary.txt"), "w", encoding="utf-8") as f:
        f.write(str(res.summary))

    # coefficient plot
    plot_terms = ["enforced", "enforced_x_drought"]
    tmp = out[out["term"].isin(plot_terms)].copy()
    tmp["ci_low"] = tmp["coef"] - 1.96 * tmp["se"]
    tmp["ci_high"] = tmp["coef"] + 1.96 * tmp["se"]

    plt.figure(figsize=(7, 3.5))
    sns.pointplot(data=tmp, x="term", y="coef", join=False)
    for i, r in tmp.reset_index(drop=True).iterrows():
        plt.plot([i, i], [r["ci_low"], r["ci_high"]], color="black", lw=1)
    plt.axhline(0, color="black", lw=1)
    plt.title("Yield impact heterogeneity in drought years")
    plt.ylabel("Coefficient (level units)")
    plt.xlabel("")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig08_yield_heterogeneity_drought.png"), dpi=200)
    plt.close()

    return out


def main():
    warnings.filterwarnings("ignore")
    _mkdirs()

    df = pd.read_csv(DATA_PATH)
    kc = infer_key_columns(df)

    # save inferred columns
    pd.DataFrame([kc.__dict__]).to_csv(os.path.join(OUT_DIR, "inferred_key_columns.csv"), index=False)

    d = prepare_df(df, kc)

    # Basic overview outputs
    overview = {
        "n_rows_raw": int(len(df)),
        "n_rows_clean": int(len(d)),
        "n_fields": int(d[kc.id_col].nunique()),
        "year_min": int(d[kc.year_col].min()),
        "year_max": int(d[kc.year_col].max()),
        "share_enforced": float(d["enforced"].mean()),
        "share_ever_enforced_fields": float(d.groupby(kc.id_col)["ever_enforced"].max().mean()),
    }
    pd.Series(overview).to_csv(os.path.join(OUT_DIR, "data_overview.csv"))

    panel_balance_plots(d, kc)
    summary_table(d, kc)
    time_trends_plot(d, kc)
    plot_yearly_panel_overview(d, kc)
    scatter_plots(d, kc)
    correlation_heatmap(d, kc)

    twfe = run_twfe(d, kc)

    est = event_study(d, kc, window=5)

    het = heterogeneity_by_drought(d, kc)

    # Small diagnostic plot: adoption histogram
    treated_fields = d.loc[d["ever_enforced"] == 1, [kc.id_col, "first_enforce_year"]].drop_duplicates()
    if len(treated_fields) > 0:
        plt.figure(figsize=(7, 4))
        sns.countplot(data=treated_fields, x="first_enforce_year")
        plt.title("Distribution of first enforcement year among treated fields")
        plt.xlabel("First enforcement year")
        plt.ylabel("# fields")
        plt.tight_layout()
        plt.savefig(os.path.join(FIG_DIR, "fig09_first_enforcement_year_hist.png"), dpi=200)
        plt.close()

    print("Done. Key columns:")
    print(kc)
    print("TWFE results (enforced coefficient):")
    print(twfe[["model", "coef_enforced", "se", "n_obs", "n_entities"]])


if __name__ == "__main__":
    main()
