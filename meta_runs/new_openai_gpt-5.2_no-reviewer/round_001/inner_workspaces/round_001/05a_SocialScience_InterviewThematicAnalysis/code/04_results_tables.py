"""Create small result tables (CSV/Markdown-friendly) for reporting."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

OUT_DIR = Path("outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    desc = json.loads((OUT_DIR / "descriptives.json").read_text())
    cohorts = desc.get("cohorts", {})
    rows = []
    for cohort, d in cohorts.items():
        rows.append(
            {
                "cohort": cohort,
                "n": d.get("n"),
                "mean_words": d.get("mean_words"),
                "median_words": d.get("median_words"),
                "mean_chars": d.get("mean_chars"),
                "median_chars": d.get("median_chars"),
            }
        )
    stats = pd.DataFrame(rows).sort_values("cohort")
    stats.to_csv(OUT_DIR / "cohort_length_summary.csv", index=False)

    # A compact set of top terms overall for the report
    top_overall = pd.read_csv(OUT_DIR / "top_terms_overall.csv").head(20)
    top_overall.to_csv(OUT_DIR / "top_terms_overall_top20.csv", index=False)

    # If log-odds exists, export compact top terms
    p = OUT_DIR / "tfidf_logodds_by_cohort.csv"
    if p.exists():
        z = pd.read_csv(p)
        top_transit = z[z.favors == "transit_primary"].nlargest(15, "z")[["term", "z"]]
        top_car = z[z.favors == "car_primary"].nsmallest(15, "z")[["term", "z"]]
        top_transit.to_csv(OUT_DIR / "distinctive_terms_transit_primary.csv", index=False)
        top_car.to_csv(OUT_DIR / "distinctive_terms_car_primary.csv", index=False)

    print("Wrote outputs/cohort_length_summary.csv and term tables")


if __name__ == "__main__":
    main()
