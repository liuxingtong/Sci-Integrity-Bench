"""Policy comparison analysis for RobotPickPlaceComparison.

Reads data/pick_place_metrics.csv (long-form or semi-wide), summarizes metrics for
pi_new vs pi_base across simulation and real-world, computes bootstrap CIs and
produces figures + tables for report/report.md.

Reproducible: fixed RNG seeds.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


RNG = np.random.default_rng(7)


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_and_normalize(path: str) -> pd.DataFrame:
    """Load CSV and normalize to columns: metric, policy, domain, value, (optional) unit."""
    df = pd.read_csv(path)

    # Standardize column names
    df.columns = [c.strip() for c in df.columns]

    # Identify policy column
    policy_col = None
    for cand in ["policy", "pi", "controller", "agent"]:
        if cand in df.columns:
            policy_col = cand
            break
    if policy_col is None:
        # Try to infer from any column containing 'pi_'
        for c in df.columns:
            if df[c].dtype == object and df[c].astype(str).str.contains("pi_").any():
                policy_col = c
                break
    if policy_col is None:
        raise ValueError(f"Could not find policy column in {df.columns.tolist()}")

    # Identify metric column
    metric_col = None
    for cand in ["metric", "metric_name", "name", "measure"]:
        if cand in df.columns:
            metric_col = cand
            break
    if metric_col is None:
        raise ValueError(f"Could not find metric column in {df.columns.tolist()}")

    # Identify value columns.
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    # Case A: long-form with explicit domain + value
    domain_col = None
    for cand in ["domain", "sim_real", "setting", "env", "world"]:
        if cand in df.columns:
            # needs to have sim/real-like values
            vals = set(df[cand].astype(str).str.lower().unique().tolist())
            if any(v in vals for v in ["sim", "simulation", "real", "real_world", "real-world", "robot"]):
                domain_col = cand
                break

    value_col = None
    for cand in ["value", "val", "score", "mean"]:
        if cand in df.columns and cand in numeric_cols:
            value_col = cand
            break

    # Case B: semi-wide: separate numeric columns for sim/real
    sim_col = None
    real_col = None
    for c in numeric_cols:
        lc = c.lower()
        if any(k in lc for k in ["sim", "simulation"]):
            sim_col = c if sim_col is None else sim_col
        if any(k in lc for k in ["real", "robot"]):
            real_col = c if real_col is None else real_col

    unit_col = "unit" if "unit" in df.columns else None

    if domain_col is not None and value_col is not None:
        out = df[[metric_col, policy_col, domain_col, value_col] + ([unit_col] if unit_col else [])].copy()
        out = out.rename(columns={metric_col: "metric", policy_col: "policy", domain_col: "domain", value_col: "value"})
        out["domain"] = out["domain"].astype(str).str.lower()
        out["domain"] = out["domain"].replace({
            "simulation": "sim",
            "real_world": "real",
            "real-world": "real",
            "robot": "real",
        })
        return out

    if sim_col is not None and real_col is not None:
        keep = [metric_col, policy_col, sim_col, real_col] + ([unit_col] if unit_col else [])
        out = df[keep].copy()
        out = out.rename(columns={metric_col: "metric", policy_col: "policy"})
        out = out.melt(id_vars=["metric", "policy"] + ([unit_col] if unit_col else []),
                       value_vars=[sim_col, real_col],
                       var_name="domain", value_name="value")
        out["domain"] = out["domain"].astype(str).str.lower()
        out["domain"] = out["domain"].apply(lambda s: "sim" if "sim" in s else ("real" if "real" in s or "robot" in s else s))
        if unit_col:
            out = out.rename(columns={unit_col: "unit"})
        return out

    # Fallback: if there is only one numeric column, treat it as value and require a domain column
    if len(numeric_cols) == 1 and domain_col is not None:
        value_col = numeric_cols[0]
        out = df[[metric_col, policy_col, domain_col, value_col] + ([unit_col] if unit_col else [])].copy()
        out = out.rename(columns={metric_col: "metric", policy_col: "policy", domain_col: "domain", value_col: "value"})
        out["domain"] = out["domain"].astype(str).str.lower().replace({"simulation": "sim", "robot": "real"})
        if unit_col:
            out = out.rename(columns={unit_col: "unit"})
        return out

    raise ValueError(
        "Could not normalize data. Expected either long-form (domain+value) or wide sim/real numeric columns. "
        f"Columns={df.columns.tolist()}, numeric={numeric_cols}"
    )


def infer_direction(metric: str) -> int:
    """Return +1 if higher is better, -1 if lower is better."""
    m = metric.lower()
    lower_better_patterns = [
        "time", "duration", "latency", "error", "distance", "rmse", "mae", "mse",
        "collision", "collisions", "contact", "force", "energy", "cost",
        "drop", "drops", "failure", "fail", "violation", "overshoot",
    ]
    higher_better_patterns = [
        "success", "accuracy", "precision", "recall", "f1", "score", "reward",
        "completion", "throughput",
    ]
    if any(p in m for p in lower_better_patterns) and not any(p in m for p in higher_better_patterns):
        return -1
    # default to higher-is-better
    return +1


def bootstrap_ci(x: np.ndarray, n_boot: int = 5000, ci: float = 0.95) -> Tuple[float, float, float]:
    """Return (mean, lo, hi) bootstrap percentile CI."""
    x = x[np.isfinite(x)]
    if x.size == 0:
        return np.nan, np.nan, np.nan
    mean = float(np.mean(x))
    if x.size == 1:
        return mean, mean, mean
    idx = RNG.integers(0, x.size, size=(n_boot, x.size))
    boots = np.mean(x[idx], axis=1)
    alpha = (1 - ci) / 2
    lo = float(np.quantile(boots, alpha))
    hi = float(np.quantile(boots, 1 - alpha))
    return mean, lo, hi


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (metric, domain, policy), g in df.groupby(["metric", "domain", "policy"], dropna=False):
        x = g["value"].to_numpy(dtype=float)
        mean, lo, hi = bootstrap_ci(x)
        rows.append({
            "metric": metric,
            "domain": domain,
            "policy": policy,
            "n": int(np.isfinite(x).sum()),
            "mean": mean,
            "ci_lo": lo,
            "ci_hi": hi,
        })
    return pd.DataFrame(rows).sort_values(["domain", "metric", "policy"]).reset_index(drop=True)


def identify_policies(policies: Iterable[str]) -> Tuple[str, str]:
    policies = sorted([str(p) for p in policies])
    base = None
    new = None
    for p in policies:
        if re.search(r"base", str(p), re.I):
            base = p
        if re.search(r"new", str(p), re.I):
            new = p
    if base is None and len(policies) >= 2:
        base = policies[0]
    if new is None and len(policies) >= 2:
        # choose the other policy if possible
        new = policies[1] if policies[1] != base else policies[-1]
    if base is None or new is None:
        raise ValueError(f"Could not identify base/new policies from {policies}")
    return base, new


def compute_deltas(summary: pd.DataFrame) -> pd.DataFrame:
    """Compute new-vs-base deltas per metric/domain from summary means."""
    base, new = identify_policies(summary["policy"].dropna().unique().tolist())

    piv = summary.pivot_table(index=["metric", "domain"], columns="policy", values="mean", aggfunc="first")
    piv = piv.reset_index()
    if base not in piv.columns or new not in piv.columns:
        raise ValueError(f"Missing base/new in pivot columns: {piv.columns.tolist()}")

    out = piv[["metric", "domain", base, new]].copy()
    out = out.rename(columns={base: "base_mean", new: "new_mean"})
    out["direction"] = out["metric"].apply(infer_direction)

    # signed improvement: positive => better
    out["signed_delta"] = (out["new_mean"] - out["base_mean"]) * out["direction"]

    # percent improvement (positive => better), with safe handling for base ~ 0
    denom = out["base_mean"].abs()
    out["pct_improvement"] = np.where(denom > 1e-12, out["signed_delta"] / denom, np.nan)

    out["base_policy"] = base
    out["new_policy"] = new
    return out


def plot_metric_bars(summary: pd.DataFrame, out_png: str) -> None:
    _ensure_dir(os.path.dirname(out_png))

    # keep consistent ordering
    metric_order = sorted(summary["metric"].unique().tolist())
    domain_order = [d for d in ["sim", "real"] if d in summary["domain"].unique().tolist()]
    if not domain_order:
        domain_order = sorted(summary["domain"].unique().tolist())

    # Create a facet grid: two panels (sim/real)
    sns.set_theme(style="whitegrid", context="talk")

    # Scale figure height by number of metrics
    fig_h = max(4.5, 0.5 * len(metric_order))
    fig, axes = plt.subplots(1, len(domain_order), figsize=(8.5 * max(1, len(domain_order)), fig_h), sharey=True)
    if len(domain_order) == 1:
        axes = [axes]

    for ax, domain in zip(axes, domain_order):
        sub = summary[summary["domain"] == domain].copy()
        sub["metric"] = pd.Categorical(sub["metric"], categories=metric_order, ordered=True)
        sub = sub.sort_values("metric")

        # Horizontal bar plot with CI whiskers
        policies = sorted(sub["policy"].unique().tolist())
        y = np.arange(len(metric_order))
        height = 0.35 if len(policies) == 2 else 0.8 / max(1, len(policies))
        offsets = np.linspace(-(len(policies)-1)/2, (len(policies)-1)/2, len(policies)) * height

        for off, pol in zip(offsets, policies):
            g = sub[sub["policy"] == pol].set_index("metric").reindex(metric_order)
            means = g["mean"].to_numpy()
            lo = g["ci_lo"].to_numpy()
            hi = g["ci_hi"].to_numpy()
            ax.barh(y + off, means, height=height, label=str(pol), alpha=0.9)
            ax.errorbar(means, y + off, xerr=[means - lo, hi - means], fmt='none', ecolor='black', elinewidth=1, capsize=3)

        ax.set_yticks(y)
        ax.set_yticklabels(metric_order)
        ax.set_title(domain)
        ax.axvline(0, color="black", linewidth=1)
        ax.set_xlabel("Metric value")

    axes[0].legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def plot_improvement_heatmap(deltas: pd.DataFrame, out_png: str, domain: str = "real") -> None:
    _ensure_dir(os.path.dirname(out_png))
    sub = deltas[deltas["domain"] == domain].copy()
    if sub.empty:
        # fallback to whatever exists
        sub = deltas.copy()

    sub = sub.sort_values("signed_delta", ascending=False)
    mat = sub.set_index("metric")[["signed_delta", "pct_improvement"]]

    sns.set_theme(style="white", context="talk")
    fig, ax = plt.subplots(figsize=(9, max(4, 0.45 * len(mat))))
    # Use a diverging colormap centered at 0 for signed_delta
    sns.heatmap(mat[["signed_delta"]], ax=ax, cmap="RdYlGn", center=0, cbar_kws={"label": "Signed improvement (+ better)"},
                linewidths=0.5, linecolor="white")
    ax.set_title(f"pi_new vs pi_base: signed improvement by metric ({domain})")
    ax.set_xlabel("")
    ax.set_ylabel("Metric")
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def bootstrap_delta_independent(x_base: np.ndarray, x_new: np.ndarray, direction: int, n_boot: int = 5000, ci: float = 0.95) -> Dict[str, float]:
    """Bootstrap signed delta of means between new and base (independent resampling).

    Returns dict with mean, ci, and probability of improvement (p_delta_gt_0).
    """
    x_base = x_base[np.isfinite(x_base)]
    x_new = x_new[np.isfinite(x_new)]
    if x_base.size == 0 or x_new.size == 0:
        return {"signed_delta": np.nan, "ci_lo": np.nan, "ci_hi": np.nan, "p_delta_gt_0": np.nan}

    # observed
    obs = (np.mean(x_new) - np.mean(x_base)) * direction

    if x_base.size == 1 and x_new.size == 1:
        return {"signed_delta": float(obs), "ci_lo": float(obs), "ci_hi": float(obs), "p_delta_gt_0": float(obs > 0)}

    idx_b = RNG.integers(0, x_base.size, size=(n_boot, x_base.size))
    idx_n = RNG.integers(0, x_new.size, size=(n_boot, x_new.size))
    boots = (np.mean(x_new[idx_n], axis=1) - np.mean(x_base[idx_b], axis=1)) * direction

    alpha = (1 - ci) / 2
    lo = float(np.quantile(boots, alpha))
    hi = float(np.quantile(boots, 1 - alpha))
    p = float(np.mean(boots > 0))
    return {"signed_delta": float(obs), "ci_lo": lo, "ci_hi": hi, "p_delta_gt_0": p}


def plot_delta_forest(delta_boot: pd.DataFrame, out_png: str, domain: str = "real") -> None:
    _ensure_dir(os.path.dirname(out_png))
    sub = delta_boot[delta_boot["domain"] == domain].copy()
    if sub.empty:
        return
    sub = sub.sort_values("signed_delta", ascending=True)

    sns.set_theme(style="whitegrid", context="talk")
    fig_h = max(4.5, 0.5 * len(sub))
    fig, ax = plt.subplots(figsize=(11, fig_h))

    y = np.arange(len(sub))
    ax.hlines(y, sub["ci_lo"], sub["ci_hi"], color="black", linewidth=2)
    ax.plot(sub["signed_delta"], y, 'o', color="#1f77b4")
    ax.axvline(0, color="black", linewidth=1)

    ax.set_yticks(y)
    ax.set_yticklabels(sub["metric"].tolist())
    ax.set_xlabel("Signed delta (positive = better for pi_new)")
    ax.set_title(f"pi_new vs pi_base: bootstrap CI for signed delta ({domain})")

    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def plot_sim2real_gap(summary: pd.DataFrame, out_png: str) -> None:
    _ensure_dir(os.path.dirname(out_png))
    sns.set_theme(style="whitegrid", context="talk")

    # Compute mean gap per metric/policy
    piv = summary.pivot_table(index=["metric", "policy"], columns="domain", values="mean", aggfunc="first")
    if not set(["sim", "real"]).issubset(set(piv.columns)):
        # Not available
        return

    piv = piv.reset_index()
    piv["direction"] = piv["metric"].apply(infer_direction)
    # degradation: positive means worse in real than sim
    piv["degradation"] = (piv["real"] - piv["sim"]) * piv["direction"]

    metric_order = piv.sort_values("degradation", ascending=False)["metric"].unique().tolist()
    fig_h = max(4.5, 0.5 * len(metric_order))
    fig, ax = plt.subplots(figsize=(10, fig_h))

    sns.barplot(data=piv, y="metric", x="degradation", hue="policy", order=metric_order, ax=ax)
    ax.axvline(0, color="black", linewidth=1)
    ax.set_title("Sim-to-real degradation by metric (positive = worse on robot)")
    ax.set_xlabel("(real - sim) * direction")
    ax.set_ylabel("Metric")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def main() -> None:
    in_path = os.path.join("data", "pick_place_metrics.csv")
    out_dir = "outputs"
    img_dir = os.path.join("report", "images")
    _ensure_dir(out_dir)
    _ensure_dir(img_dir)

    df = load_and_normalize(in_path)

    # Basic cleaning
    df["policy"] = df["policy"].astype(str)
    df["metric"] = df["metric"].astype(str)
    df["domain"] = df["domain"].astype(str).str.lower()

    # Keep only sim/real if present, else all
    if set(df["domain"].unique()) & {"sim", "real"}:
        df = df[df["domain"].isin(["sim", "real"])].copy()

    df.to_csv(os.path.join(out_dir, "normalized_longform.csv"), index=False)

    summary = summarize(df)
    summary.to_csv(os.path.join(out_dir, "summary_bootstrap.csv"), index=False)

    deltas = compute_deltas(summary)
    deltas.to_csv(os.path.join(out_dir, "deltas.csv"), index=False)

    # Bootstrap uncertainty for deltas using the raw long-form values
    base_pol, new_pol = identify_policies(df["policy"].dropna().unique().tolist())
    delta_rows = []
    for (metric, domain), g in df.groupby(["metric", "domain"], dropna=False):
        direction = infer_direction(metric)
        x_base = g.loc[g["policy"] == base_pol, "value"].to_numpy(dtype=float)
        x_new = g.loc[g["policy"] == new_pol, "value"].to_numpy(dtype=float)
        stats = bootstrap_delta_independent(x_base, x_new, direction=direction)
        delta_rows.append({
            "metric": metric,
            "domain": domain,
            "base_policy": base_pol,
            "new_policy": new_pol,
            "direction": direction,
            "n_base": int(np.isfinite(x_base).sum()),
            "n_new": int(np.isfinite(x_new).sum()),
            **stats,
        })
    delta_boot = pd.DataFrame(delta_rows).sort_values(["domain", "metric"]).reset_index(drop=True)
    delta_boot.to_csv(os.path.join(out_dir, "delta_bootstrap.csv"), index=False)

    # Overall aggregate score (for recommendation): average signed z-normalized improvement in real.
    # Compute within-metric scale using base sim+real std to avoid unit issues.
    # Compute per-metric std across all values (both policies, both domains)
    scales = df.groupby("metric")["value"].std(ddof=1).replace(0, np.nan)
    deltas["scale_std"] = deltas["metric"].map(scales)
    deltas["signed_delta_z"] = deltas["signed_delta"] / deltas["scale_std"]

    # Summarize by domain
    agg = deltas.groupby("domain").agg(
        mean_signed_delta_z=("signed_delta_z", "mean"),
        median_signed_delta_z=("signed_delta_z", "median"),
        n_metrics=("metric", "nunique"),
        n_improved=("signed_delta", lambda s: int(np.sum(s > 0))),
        n_worsened=("signed_delta", lambda s: int(np.sum(s < 0))),
    ).reset_index()
    agg["base_policy"] = base_pol
    agg["new_policy"] = new_pol
    agg.to_csv(os.path.join(out_dir, "aggregate_domain_summary.csv"), index=False)

    # Figures
    plot_metric_bars(summary, os.path.join(img_dir, "metric_bars_sim_real.png"))
    plot_improvement_heatmap(deltas, os.path.join(img_dir, "improvement_heatmap_real.png"), domain="real")
    plot_delta_forest(delta_boot, os.path.join(img_dir, "delta_forest_real.png"), domain="real")
    plot_sim2real_gap(summary, os.path.join(img_dir, "sim2real_degradation.png"))

    # Write a compact markdown snippet with key numbers for inclusion in report.
    # Pick real-domain deltas sorted by signed improvement
    real = deltas[deltas["domain"] == "real"].sort_values("signed_delta", ascending=False)
    real_tbl = real[["metric", "base_mean", "new_mean", "signed_delta", "pct_improvement"]].copy()
    real_tbl["pct_improvement"] = real_tbl["pct_improvement"] * 100
    real_tbl.to_csv(os.path.join(out_dir, "real_domain_ranked.csv"), index=False)

    # Also compute how many metrics are better on robot, plus bootstrap win probabilities
    db_real = delta_boot[delta_boot["domain"] == "real"].copy()
    rec = {
        "base_policy": base_pol,
        "new_policy": new_pol,
        "real_n_metrics": int(real["metric"].nunique()),
        "real_n_improved_point": int((real["signed_delta"] > 0).sum()),
        "real_n_worsened_point": int((real["signed_delta"] < 0).sum()),
        "real_mean_signed_delta_z": float(agg.loc[agg["domain"] == "real", "mean_signed_delta_z"].iloc[0]) if (agg["domain"] == "real").any() else np.nan,
        "real_mean_p_improved": float(db_real["p_delta_gt_0"].mean()) if not db_real.empty else np.nan,
        "real_n_metrics_p_gt_0_75": int((db_real["p_delta_gt_0"] > 0.75).sum()) if not db_real.empty else 0,
        "real_n_metrics_p_gt_0_90": int((db_real["p_delta_gt_0"] > 0.90).sum()) if not db_real.empty else 0,
    }
    pd.DataFrame([rec]).to_csv(os.path.join(out_dir, "recommendation_numbers.csv"), index=False)


if __name__ == "__main__":
    main()
