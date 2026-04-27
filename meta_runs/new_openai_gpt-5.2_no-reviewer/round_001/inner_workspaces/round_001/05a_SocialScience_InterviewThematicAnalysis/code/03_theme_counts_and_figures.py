"""Compute transparent code-based counts from LLM thematic coding and generate figures.

Inputs:
  outputs/thematic_codes.json
  outputs/cleaned_excerpts.csv
Outputs:
  outputs/theme_counts_by_cohort.csv
  outputs/respondent_codes_flat.csv
  report/images/theme_prevalence_by_cohort.png

If thematic_codes.json contains an error, this script will still write empty outputs.
"""

from __future__ import annotations

import json
import os

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def main():
    os.makedirs("outputs", exist_ok=True)
    os.makedirs(os.path.join("report", "images"), exist_ok=True)

    df = pd.read_csv("outputs/cleaned_excerpts.csv")

    with open("outputs/thematic_codes.json", "r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, dict) or payload.get("ok") is False or "respondent_codes" not in payload:
        # write empty but valid artifacts
        pd.DataFrame(columns=["cohort", "code", "n_respondents", "share_of_cohort"]).to_csv(
            "outputs/theme_counts_by_cohort.csv", index=False
        )
        pd.DataFrame(columns=["respondent_id", "cohort", "code"]).to_csv("outputs/respondent_codes_flat.csv", index=False)
        return

    themes = payload.get("themes", [])
    code_to_label = {t.get("code"): t.get("label") for t in themes if isinstance(t, dict)}

    rc = pd.DataFrame(payload["respondent_codes"])
    # Normalize
    rc["respondent_id"] = rc["respondent_id"].astype(str)
    rc["cohort"] = rc["cohort"].astype(str)

    # Explode codes
    rc["codes"] = rc["codes"].apply(lambda x: x if isinstance(x, list) else [])
    flat = rc.explode("codes").rename(columns={"codes": "code"})
    flat = flat.dropna(subset=["code"])
    flat["code"] = flat["code"].astype(str)

    # Keep only known codes (guardrail)
    known = set(code_to_label.keys())
    if known:
        flat = flat[flat["code"].isin(known)]

    # Merge in cohort from source df if needed
    if "cohort" not in flat.columns or flat["cohort"].isna().any():
        flat = flat.drop(columns=["cohort"], errors="ignore").merge(
            df[["respondent_id", "cohort"]].astype(str), on="respondent_id", how="left"
        )

    flat = flat[["respondent_id", "cohort", "code"]].drop_duplicates()
    flat.to_csv("outputs/respondent_codes_flat.csv", index=False)

    # Counts: number of respondents per cohort coded with each code
    cohort_sizes = df.groupby("cohort")["respondent_id"].nunique().to_dict()
    counts = (
        flat.groupby(["cohort", "code"])["respondent_id"]
        .nunique()
        .reset_index()
        .rename(columns={"respondent_id": "n_respondents"})
    )
    counts["cohort_n"] = counts["cohort"].map(cohort_sizes)
    counts["share_of_cohort"] = counts["n_respondents"] / counts["cohort_n"]
    counts["label"] = counts["code"].map(code_to_label).fillna(counts["code"])

    counts.to_csv("outputs/theme_counts_by_cohort.csv", index=False)

    # Figure: theme prevalence by cohort
    if not counts.empty:
        # order by overall prevalence
        overall = counts.groupby("label")["n_respondents"].sum().sort_values(ascending=False)
        order = list(overall.index)

        plot_df = counts.copy()
        plot_df["label"] = pd.Categorical(plot_df["label"], categories=order, ordered=True)

        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(10.5, max(4.5, 0.35 * len(order) + 1.5)))
        ax = sns.barplot(
            data=plot_df,
            y="label",
            x="share_of_cohort",
            hue="cohort",
            orient="h",
        )
        ax.set_title("Theme prevalence by cohort (share of respondents coded)")
        ax.set_xlabel("Share of cohort")
        ax.set_ylabel("")
        ax.set_xlim(0, 1)
        ax.legend(title="Cohort", loc="lower right")
        plt.tight_layout()
        plt.savefig(os.path.join("report", "images", "theme_prevalence_by_cohort.png"), dpi=200)
        plt.close()


if __name__ == "__main__":
    main()
