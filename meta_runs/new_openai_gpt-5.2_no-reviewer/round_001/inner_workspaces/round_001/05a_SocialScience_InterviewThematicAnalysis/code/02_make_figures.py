"""Create figures for the interview thematic analysis report.

Figures:
- report/images/word_count_by_cohort.png
- report/images/distinguishing_terms_logodds.png

Run:
  python code/02_make_figures.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

OUT_IMG = Path("report/images")
OUT_IMG.mkdir(parents=True, exist_ok=True)


def main():
    sns.set_theme(style="whitegrid", font_scale=1.0)

    df = pd.read_csv("outputs/processed_interviews.csv")

    # Figure 1: response length distributions
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    order = [c for c in ["transit_primary", "car_primary"] if c in df["cohort"].unique()]
    sns.violinplot(
        data=df,
        x="cohort",
        y="word_count",
        order=order,
        inner=None,
        cut=0,
        linewidth=1,
        ax=ax,
        color="#c7d9f1",
    )
    sns.boxplot(
        data=df,
        x="cohort",
        y="word_count",
        order=order,
        width=0.25,
        ax=ax,
        showfliers=False,
        boxprops={"facecolor": "#ffffff", "edgecolor": "#2b2b2b"},
        medianprops={"color": "#2b2b2b"},
        whiskerprops={"color": "#2b2b2b"},
        capprops={"color": "#2b2b2b"},
    )
    ax.set_title("Interview response length by cohort")
    ax.set_xlabel("Cohort")
    ax.set_ylabel("Word count")
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    fig_path = OUT_IMG / "word_count_by_cohort.png"
    fig.savefig(fig_path, dpi=200)
    plt.close(fig)

    # Figure 2: distinguishing terms (weighted log-odds)
    p = Path("outputs/tfidf_logodds_by_cohort.csv")
    if p.exists():
        z = pd.read_csv(p)
        # Keep most distinctive terms on each side
        top_each = 15
        pos = z[z["favors"] == "transit_primary"].nlargest(top_each, "z").copy()
        neg = z[z["favors"] == "car_primary"].nsmallest(top_each, "z").copy()
        neg["z_abs"] = neg["z"].abs()
        pos["z_abs"] = pos["z"].abs()
        plot_df = pd.concat([pos, neg], ignore_index=True)
        plot_df["direction"] = np.where(plot_df["favors"] == "transit_primary", "Favors transit_primary", "Favors car_primary")

        # Order by absolute z
        plot_df = plot_df.sort_values("z_abs", ascending=True)

        fig, ax = plt.subplots(figsize=(8.2, 6.6))
        sns.barplot(
            data=plot_df,
            y="term",
            x="z_abs",
            hue="direction",
            dodge=False,
            palette={"Favors transit_primary": "#2b6cb0", "Favors car_primary": "#c53030"},
            ax=ax,
        )
        ax.set_title("Most distinguishing content terms by cohort (weighted log-odds |z|)")
        ax.set_xlabel("|z| (larger = more distinctive)")
        ax.set_ylabel("Term")
        ax.legend(title="")
        plt.tight_layout()
        fig_path = OUT_IMG / "distinguishing_terms_logodds.png"
        fig.savefig(fig_path, dpi=200)
        plt.close(fig)

    print("Wrote figures to", OUT_IMG)


if __name__ == "__main__":
    main()
