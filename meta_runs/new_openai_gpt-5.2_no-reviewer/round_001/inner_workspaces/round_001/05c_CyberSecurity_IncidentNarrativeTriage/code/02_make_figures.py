#!/usr/bin/env python3
"""Generate required figures for incident narrative triage."""

from __future__ import annotations

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

OUTDIR = "report/images"


def main():
    os.makedirs(OUTDIR, exist_ok=True)

    df = pd.read_csv("outputs/incident_preprocessed.csv")

    # Figure 1: incident counts by source_system
    counts = df["source_system"].value_counts().rename_axis("source_system").reset_index(name="n_incidents")
    plt.figure(figsize=(5, 3.2))
    sns.barplot(data=counts, x="source_system", y="n_incidents", color="#4C78A8")
    plt.title("Incident count by source system")
    plt.xlabel("Source system")
    plt.ylabel("Number of incident narratives")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "fig_counts_by_source.png"), dpi=200)
    plt.close()

    # Figure 2: narrative length distributions (words) by source_system
    plt.figure(figsize=(6.2, 3.6))
    sns.boxplot(data=df, x="source_system", y="n_words", color="#72B7B2")
    sns.stripplot(data=df.sample(min(len(df), 200), random_state=0), x="source_system", y="n_words", color="black", alpha=0.35, size=2, jitter=0.2)
    plt.title("Narrative length by source system (words)")
    plt.xlabel("Source system")
    plt.ylabel("Words per narrative")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "fig_length_words_by_source.png"), dpi=200)
    plt.close()

    # Figure 3: keyword-category hit totals by source (stacked)
    kw_cols = [c for c in df.columns if c.startswith("kw_")]
    kw = df.groupby("source_system")[kw_cols].sum()
    kw = kw.rename(columns=lambda c: c.replace("kw_", ""))
    # Order categories by total
    kw = kw[kw.sum(axis=0).sort_values(ascending=False).index]

    ax = kw.T.plot(kind="bar", figsize=(8.0, 4.2), width=0.85)
    ax.set_title("Keyword-category hit totals by source system")
    ax.set_xlabel("Keyword category")
    ax.set_ylabel("Total hits (substring/regex matches)")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "fig_keyword_hits_by_source.png"), dpi=200)
    plt.close()


if __name__ == "__main__":
    sns.set_theme(style="whitegrid")
    main()
