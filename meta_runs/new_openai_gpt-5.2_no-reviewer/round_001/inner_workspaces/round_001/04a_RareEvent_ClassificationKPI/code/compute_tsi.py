#!/usr/bin/env python3
"""Compute Temporal Stability Index (TSI) on model output traces.

Task 04a_RareEvent_ClassificationKPI.

Definition (given):
Let x be the 1-D series of model outputs.
If fewer than two samples: TSI = 1.0.
Otherwise let d be first differences of x.
Let sigma_x and sigma_d be the population standard deviations (ddof=0)
computed over x and d respectively.
Let eps = 1e-12.
TSI = clip(1 - sigma_d / (sigma_x + eps), 0, 1).

This script:
- loads data/experiment_traces.csv (rows assumed in time order)
- computes TSI for the full series
- generates diagnostic figures
- writes outputs/tsi_results.json and outputs/prefix_tsi.csv
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


EPS = 1e-12


def temporal_stability_index(x: np.ndarray, eps: float = EPS) -> float:
    """Compute TSI as defined in the task (population std, ddof=0)."""
    x = np.asarray(x, dtype=float)
    if x.size < 2:
        return 1.0
    d = np.diff(x)
    sigma_x = float(np.std(x, ddof=0))
    sigma_d = float(np.std(d, ddof=0))
    tsi = 1.0 - sigma_d / (sigma_x + eps)
    # clamp to [0, 1]
    if tsi < 0.0:
        tsi = 0.0
    if tsi > 1.0:
        tsi = 1.0
    return float(tsi)


def main():
    root = Path(__file__).resolve().parents[1]
    data_path = root / "data" / "experiment_traces.csv"
    out_dir = root / "outputs"
    fig_dir = root / "report" / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    if "model_output" not in df.columns:
        raise ValueError(f"Expected column 'model_output' in {data_path}, got columns={list(df.columns)}")

    x = df["model_output"].to_numpy(dtype=float)

    # Full-series TSI and components
    if x.size < 2:
        d = np.array([])
        sigma_x = float(np.std(x, ddof=0)) if x.size else float("nan")
        sigma_d = float("nan")
        tsi_full = 1.0
    else:
        d = np.diff(x)
        sigma_x = float(np.std(x, ddof=0))
        sigma_d = float(np.std(d, ddof=0))
        tsi_full = temporal_stability_index(x)

    # Prefix (online) TSI for validation/convergence visualization
    prefix_idx = np.arange(1, x.size + 1)
    prefix_tsi = np.empty_like(prefix_idx, dtype=float)
    for i in range(x.size):
        prefix_tsi[i] = temporal_stability_index(x[: i + 1])

    prefix_df = pd.DataFrame({"n_samples": prefix_idx, "tsi_prefix": prefix_tsi})
    prefix_df.to_csv(out_dir / "prefix_tsi.csv", index=False)

    # Save scalar results
    results = {
        "n_samples": int(x.size),
        "eps": EPS,
        "sigma_x_population": sigma_x,
        "sigma_d_population": sigma_d,
        "tsi_full": tsi_full,
    }
    with open(out_dir / "tsi_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # ---------- Figures ----------
    # 1) Time series of model_output
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(np.arange(x.size), x, lw=1.0)
    ax.set_title("Model output over time")
    ax.set_xlabel("time index")
    ax.set_ylabel("model_output")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(fig_dir / "timeseries_model_output.png", dpi=200)
    plt.close(fig)

    # 2) First differences time series
    fig, ax = plt.subplots(figsize=(10, 3.5))
    if d.size:
        ax.plot(np.arange(d.size), d, lw=1.0)
    ax.axhline(0, color="k", lw=0.8, alpha=0.6)
    ax.set_title("First differences of model output")
    ax.set_xlabel("time index")
    ax.set_ylabel("diff(model_output)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(fig_dir / "timeseries_first_differences.png", dpi=200)
    plt.close(fig)

    # 3) Distribution diagnostics: histogram of x and d
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    axes[0].hist(x[~np.isnan(x)], bins=50, color="#4C72B0", alpha=0.9)
    axes[0].set_title("Distribution of model_output")
    axes[0].set_xlabel("model_output")
    axes[0].set_ylabel("count")
    axes[0].grid(True, alpha=0.25)

    if d.size:
        axes[1].hist(d[~np.isnan(d)], bins=50, color="#DD8452", alpha=0.9)
    axes[1].set_title("Distribution of first differences")
    axes[1].set_xlabel("diff(model_output)")
    axes[1].set_ylabel("count")
    axes[1].grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(fig_dir / "hist_model_output_and_differences.png", dpi=200)
    plt.close(fig)

    # 4) Prefix TSI convergence plot
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(prefix_idx, prefix_tsi, lw=1.5)
    ax.set_title("Temporal Stability Index (prefix estimate)")
    ax.set_xlabel("number of samples (prefix length)")
    ax.set_ylabel("TSI")
    ax.set_ylim(-0.02, 1.02)
    ax.grid(True, alpha=0.3)
    # annotate final
    ax.axhline(tsi_full, color="k", ls="--", lw=1.0, alpha=0.7)
    ax.text(0.99, 0.03, f"Full-series TSI = {tsi_full:.4f}", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.8, edgecolor="none"))
    fig.tight_layout()
    fig.savefig(fig_dir / "prefix_tsi_convergence.png", dpi=200)
    plt.close(fig)

    # 5) Rolling variability ratio (sigma_d / sigma_x) as local stability proxy
    # Not part of definition; provided for interpretability.
    win = max(10, min(200, x.size // 20 if x.size else 10))
    if x.size >= win + 1:
        # compute rolling std of x and rolling std of d aligned to window ending at t
        rx = pd.Series(x).rolling(win).std(ddof=0)
        rd = pd.Series(np.r_[np.nan, d]).rolling(win).std(ddof=0)  # pad to align
        ratio = rd / (rx + EPS)

        fig, ax = plt.subplots(figsize=(10, 3.5))
        ax.plot(ratio.to_numpy(), lw=1.0, color="#55A868")
        ax.set_title(f"Rolling variability ratio σ_d/σ_x (window={win})")
        ax.set_xlabel("time index")
        ax.set_ylabel("σ_d / (σ_x + ε)")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(fig_dir / "rolling_ratio_sigma_d_over_sigma_x.png", dpi=200)
        plt.close(fig)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
