# -*- coding: utf-8 -*-
"""Huangtupo radiocarbon chronology analysis.

Reads radiocarbon_measurements.csv (F14 values + 1σ), converts to conventional
radiocarbon age BP using the specification in data/analysis_spec.txt, then
calibrates (IntCal20) and summarizes calibrated calendar ranges.

Outputs:
- outputs/huangtupo_derived_dates.csv
- outputs/huangtupo_calibration_grid.parquet
- report/images/*.png

Reproducible, no network access required (relies on pyradiocarbon packaged curves).
"""

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ------------------------------
# Conversions and summaries
# ------------------------------

def f14_to_age_bp(f14: float, f14_1s: float, mean_life: float = 8033.0) -> Tuple[float, float]:
    """Convert fraction modern (F14) to conventional radiocarbon age BP.

    Uses: age = -mean_life * ln(F14)
    Uncertainty propagation: sigma_age = mean_life * (sigma_F14 / F14)

    mean_life=8033 corresponds to Libby half-life 5568 (conventional 14C age).
    """
    if not (f14 > 0):
        return (np.nan, np.nan)
    age = -mean_life * math.log(f14)
    sigma = mean_life * (f14_1s / f14)
    return age, sigma


def calbp_to_bce_ce(calbp: float) -> int:
    """Convert cal BP (before 1950) to calendar year in BCE/CE as integer.

    Uses astronomical year numbering internally (year = 1950 - calBP).
    Returns 'historical' year without year 0:
      - For CE years: 1.. present
      - For BCE years: negative integers where -1 == 1 BCE, -2 == 2 BCE, etc.
    """
    year_astr = 1950.0 - calbp
    y = int(round(year_astr))
    if y <= 0:
        # astronomical 0 corresponds to 1 BCE
        y = y - 1
    return y


def format_year(y: int) -> str:
    if y < 0:
        return f"{abs(y)} BCE"
    else:
        return f"{y} CE"


def hpd_intervals_from_grid(x: np.ndarray, p: np.ndarray, mass: float) -> List[Tuple[float, float]]:
    """Compute HPD region(s) from a discrete probability grid.

    Approach:
    - Normalize p
    - Find a probability threshold t such that sum(p[p>=t]) ~= mass
    - Return contiguous x-intervals where p >= t.

    Works for multimodal distributions and returns a set of intervals.
    """
    x = np.asarray(x)
    p = np.asarray(p)
    ok = np.isfinite(x) & np.isfinite(p)
    x, p = x[ok], p[ok]

    if len(x) == 0:
        return []

    # Ensure increasing x
    order = np.argsort(x)
    x, p = x[order], p[order]

    p = np.clip(p, 0, None)
    s = p.sum()
    if s <= 0:
        return []
    p = p / s

    # Determine threshold
    p_sorted = np.sort(p)[::-1]
    csum = np.cumsum(p_sorted)
    idx = np.searchsorted(csum, mass, side="left")
    if idx >= len(p_sorted):
        t = p_sorted[-1]
    else:
        t = p_sorted[idx]

    mask = p >= t
    if not mask.any():
        return []

    intervals = []
    start = None
    for xi, mi in zip(x, mask):
        if mi and start is None:
            start = xi
        elif (not mi) and start is not None:
            end = prev_x
            intervals.append((start, end))
            start = None
        prev_x = xi
    if start is not None:
        intervals.append((start, x[mask].max()))

    # Merge intervals that are separated by <= one grid step
    if len(intervals) <= 1:
        return intervals

    step = np.median(np.diff(x)) if len(x) > 1 else 1.0
    merged = [intervals[0]]
    for a, b in intervals[1:]:
        pa, pb = merged[-1]
        if a - pb <= 1.1 * step:
            merged[-1] = (pa, max(pb, b))
        else:
            merged.append((a, b))
    return merged


def intervals_to_string(intervals_calbp: List[Tuple[float, float]]) -> str:
    """Format calBP intervals as BCE/CE ranges."""
    parts = []
    for lo, hi in intervals_calbp:
        # Convert endpoints; note: calBP larger = older = more BCE.
        y_old = calbp_to_bce_ce(hi)
        y_yng = calbp_to_bce_ce(lo)
        parts.append(f"{format_year(y_old)}–{format_year(y_yng)}")
    return "; ".join(parts)


def cultural_period_from_year(year_ce: int) -> str:
    """Very coarse China-wide period bins, for sketch periodization."""
    # year_ce uses negative for BCE.
    y = year_ce
    if y <= -3000:
        return "Early Neolithic (broad)"
    if -3000 < y <= -2000:
        return "Late Neolithic (broad)"
    if -2000 < y <= -1600:
        return "Early Bronze Age (broad)"
    if -1600 < y <= -1046:
        return "Shang period (broad)"
    if -1046 < y <= -256:
        return "Zhou period (broad)"
    if -256 < y <= 220:
        return "Qin–Han (broad)"
    if 220 < y <= 589:
        return "Six Dynasties (broad)"
    if 589 < y <= 907:
        return "Sui–Tang (broad)"
    if 907 < y <= 1279:
        return "Song (broad)"
    if 1279 < y <= 1368:
        return "Yuan (broad)"
    if 1368 < y <= 1644:
        return "Ming (broad)"
    if 1644 < y <= 1912:
        return "Qing (broad)"
    return "Modern"


def parse_stratigraphic_order(s: str) -> float:
    """Extract an ordering key from a stratigraphic unit label.

    Heuristic:
    - If label contains a depth or layer number, use that.
    - Otherwise returns NaN.

    Assumption: higher layer numbers are deeper/older.
    """
    if not isinstance(s, str):
        return np.nan
    m = re.search(r"(layer|stratum|unit|su)\s*([0-9]+)", s, flags=re.I)
    if m:
        return float(m.group(2))
    m = re.search(r"\b([0-9]+)\b", s)
    if m:
        return float(m.group(1))
    return np.nan


# ------------------------------
# Calibration wrapper
# ------------------------------

def calibrate_age(age_bp: float, age_1s: float, curve: str = "intcal20") -> pd.DataFrame:
    """Calibrate a conventional 14C age using pyradiocarbon."""
    from pyradiocarbon import calibrate

    cal = calibrate(age_bp, age_1s, curve=curve)
    # Expect a DataFrame with columns including calbp and prob
    if isinstance(cal, pd.DataFrame):
        df = cal.copy()
    else:
        df = pd.DataFrame(cal)

    # Standardize column names
    cols = {c.lower(): c for c in df.columns}
    if "calbp" in cols:
        calbp_col = cols["calbp"]
    elif "cal_bp" in cols:
        calbp_col = cols["cal_bp"]
    else:
        # common alternative: 'cal_age'
        calbp_col = df.columns[0]

    if "prob" in cols:
        prob_col = cols["prob"]
    elif "p" in cols:
        prob_col = cols["p"]
    elif "pdf" in cols:
        prob_col = cols["pdf"]
    else:
        prob_col = df.columns[1]

    out = df.rename(columns={calbp_col: "calbp", prob_col: "prob"})[["calbp", "prob"]]
    out = out.sort_values("calbp")
    return out


# ------------------------------
# Main
# ------------------------------

def main():
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("report/images", exist_ok=True)

    rc = pd.read_csv("data/radiocarbon_measurements.csv")

    # Compute conventional ages
    ages = [f14_to_age_bp(f, s) for f, s in zip(rc["f14_residual_ratio"], rc["f14_1s"]) ]
    rc["age_bp"] = [a for a, _ in ages]
    rc["age_1s"] = [s for _, s in ages]

    # Strat order key
    rc["strat_order_key"] = rc["stratigraphic_unit"].astype(str).apply(parse_stratigraphic_order)

    # Calibration
    cal_grids = []
    summary_rows = []
    for i, row in rc.iterrows():
        cal = calibrate_age(row["age_bp"], row["age_1s"], curve="intcal20")
        cal["sample_id"] = row["sample_id"] if "sample_id" in rc.columns else str(i)
        cal_grids.append(cal)

        hpd68 = hpd_intervals_from_grid(cal["calbp"].values, cal["prob"].values, 0.6827)
        hpd95 = hpd_intervals_from_grid(cal["calbp"].values, cal["prob"].values, 0.9545)

        # point summaries
        # mean/median in calBP
        p = cal["prob"].values
        p = p / p.sum()
        calbp = cal["calbp"].values
        cdf = np.cumsum(p)
        med = np.interp(0.5, cdf, calbp)
        mean = float(np.sum(calbp * p))

        # Convert median to BCE/CE for period label
        med_year = calbp_to_bce_ce(med)
        summary_rows.append({
            "sample_id": row.get("sample_id", str(i)),
            "lab_id": row.get("lab_id", ""),
            "material": row.get("material", ""),
            "stratigraphic_unit": row.get("stratigraphic_unit", ""),
            "notes": row.get("notes", ""),
            "f14_residual_ratio": row["f14_residual_ratio"],
            "f14_1s": row["f14_1s"],
            "age_bp": row["age_bp"],
            "age_1s": row["age_1s"],
            "calbp_median": med,
            "calbp_mean": mean,
            "cal_68_hpd": intervals_to_string(hpd68),
            "cal_95_hpd": intervals_to_string(hpd95),
            "median_period": cultural_period_from_year(med_year),
        })

    cal_grid = pd.concat(cal_grids, ignore_index=True)

    # Save derived tables
    derived = pd.DataFrame(summary_rows)
    derived.to_csv("outputs/huangtupo_derived_dates.csv", index=False)
    try:
        cal_grid.to_parquet("outputs/huangtupo_calibration_grid.parquet", index=False)
    except Exception:
        cal_grid.to_csv("outputs/huangtupo_calibration_grid.csv", index=False)

    # ------------------------------
    # Figures
    # ------------------------------

    sns.set_context("talk")
    sns.set_style("whitegrid")

    # Fig 1: Conventional 14C ages ordered by stratigraphy (heuristic)
    fig, ax = plt.subplots(figsize=(10, 5.5))

    plot_df = derived.merge(rc[["sample_id", "strat_order_key"]], on="sample_id", how="left")
    # If order key exists, sort; otherwise sort by age
    if plot_df["strat_order_key"].notna().any():
        plot_df = plot_df.sort_values(["strat_order_key", "age_bp"], ascending=[True, True])
        xlabel = "Stratigraphic ordering key (heuristic; higher ~ deeper/older)"
    else:
        plot_df = plot_df.sort_values("age_bp", ascending=True)
        xlabel = "Samples (sorted by 14C age)"

    y = np.arange(len(plot_df))
    ax.errorbar(plot_df["age_bp"], y, xerr=plot_df["age_1s"], fmt='o', color='black', ecolor='gray', capsize=3)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["sample_id"].astype(str))
    ax.invert_yaxis()
    ax.set_xlabel("Conventional radiocarbon age (14C years BP ±1σ)")
    ax.set_ylabel("Sample")
    ax.set_title("Huangtupo: conventional 14C ages")
    fig.tight_layout()
    fig.savefig("report/images/fig1_conventional_ages.png", dpi=200)
    plt.close(fig)

    # Fig 2: Calibrated probability distributions (stacked)
    # Use a common calBP grid per sample plot
    fig, ax = plt.subplots(figsize=(10, 6.5))

    # Determine plotting order (same as fig1)
    ordered_ids = list(plot_df["sample_id"].astype(str))
    offset = 0
    for sid in ordered_ids:
        g = cal_grid[cal_grid["sample_id"].astype(str) == str(sid)].copy()
        g = g.sort_values("calbp")
        p = g["prob"].values
        p = p / p.max() if p.max() > 0 else p
        ax.fill_between(g["calbp"], offset, offset + p, alpha=0.8, linewidth=0.5)
        ax.text(g["calbp"].min(), offset + 0.5, str(sid), va='center', fontsize=10)
        offset += 1.2

    ax.set_xlabel("Calibrated age (cal BP; IntCal20)")
    ax.set_ylabel("Stacked relative probability")
    ax.set_title("Huangtupo: calibrated calendar-age distributions")
    ax.invert_xaxis()  # older to the left (higher calBP)
    fig.tight_layout()
    fig.savefig("report/images/fig2_calibrated_distributions.png", dpi=200)
    plt.close(fig)

    # Fig 3: Stratigraphic consistency check (if strat keys exist)
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    if plot_df["strat_order_key"].notna().any():
        ax.errorbar(plot_df["strat_order_key"], plot_df["calbp_median"],
                    yerr=None, fmt='o', color='black')
        ax.set_xlabel("Stratigraphic ordering key (heuristic)")
        ax.set_ylabel("Median calibrated age (cal BP)")
        ax.set_title("Stratigraphy vs. calibrated age (median)")
        ax.invert_yaxis()  # older (higher calBP) at top
    else:
        ax.text(0.5, 0.5, "No parseable stratigraphic ordering key;\nfigure not applicable.",
                ha='center', va='center')
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig("report/images/fig3_stratigraphy_vs_age.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
