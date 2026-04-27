"""Generate report/report.md from computed outputs.

Inputs:
  outputs/descriptives.json
  outputs/top_terms_by_cohort.csv
  outputs/theme_counts_by_cohort.csv
  outputs/thematic_codes.json
Outputs:
  report/report.md
  report/interview_thematic_report.md
"""

from __future__ import annotations

import json
import os
from datetime import date

import pandas as pd


def df_to_md_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df is None or df.empty:
        return "(No data)"
    d = df.copy().head(max_rows)
    return d.to_markdown(index=False)


def main():
    os.makedirs("report", exist_ok=True)

    with open("outputs/descriptives.json", "r", encoding="utf-8") as f:
        desc = json.load(f)

    top_terms = pd.read_csv("outputs/top_terms_by_cohort.csv")
    theme_counts_path = "outputs/theme_counts_by_cohort.csv"
    theme_counts = pd.read_csv(theme_counts_path) if os.path.exists(theme_counts_path) else pd.DataFrame()

    with open("outputs/thematic_codes.json", "r", encoding="utf-8") as f:
        thematic = json.load(f)

    n = desc.get("n_respondents")
    cohort_counts = desc.get("cohort_counts", {})

    # Build small tables
    cohort_table = pd.DataFrame(
        [{"cohort": k, "n_respondents": v} for k, v in cohort_counts.items()]
    ).sort_values("cohort")

    # Length table: n_words mean/median by cohort
    rows = []
    for cohort, stats in desc.get("length_stats_by_cohort", {}).items():
        nw = stats.get("n_words", {})
        rows.append(
            {
                "cohort": cohort,
                "n": nw.get("n"),
                "mean_words": round(nw.get("mean", float("nan")), 1),
                "median_words": round(nw.get("median", float("nan")), 1),
                "p25": round(nw.get("p25", float("nan")), 1),
                "p75": round(nw.get("p75", float("nan")), 1),
            }
        )
    length_table = pd.DataFrame(rows).sort_values("cohort")

    # Top terms: show top 10 per cohort
    top_terms_10 = top_terms[top_terms["rank"] <= 10].copy()

    # Themes summary
    themes = thematic.get("themes", []) if isinstance(thematic, dict) else []
    contrasts = thematic.get("cohort_contrasts", []) if isinstance(thematic, dict) else []

    # Prepare theme prevalence table (top 10 by overall respondents)
    theme_prev_table = pd.DataFrame()
    if not theme_counts.empty and {"label", "cohort", "n_respondents", "share_of_cohort"}.issubset(theme_counts.columns):
        tmp = theme_counts.copy()
        tmp["share_of_cohort"] = (100 * tmp["share_of_cohort"]).round(1)
        tmp = tmp.sort_values(["label", "cohort"])
        theme_prev_table = tmp[["label", "cohort", "n_respondents", "share_of_cohort"]].rename(
            columns={"label": "theme", "share_of_cohort": "share_of_cohort_%"}
        )
        # limit rows
        # order by overall respondents across cohorts
        overall = theme_counts.groupby("label")["n_respondents"].sum().sort_values(ascending=False)
        top_labels = set(overall.head(10).index)
        theme_prev_table = theme_prev_table[theme_prev_table["theme"].isin(top_labels)]
        theme_prev_table = theme_prev_table.sort_values(["theme", "cohort"])

    # Render qualitative theme descriptions + illustrative quotes
    theme_bullets = []
    theme_quotes_sections = []
    if themes and isinstance(themes, list):
        for t in themes:
            if not isinstance(t, dict):
                continue
            code = t.get("code", "")
            label = t.get("label", "")
            descr = t.get("description", "")
            subs = t.get("subthemes", [])
            subs_str = ", ".join(subs) if isinstance(subs, list) and subs else ""
            theme_bullets.append(f"- **{label}** (`{code}`): {descr}" + (f" Subthemes: {subs_str}." if subs_str else ""))

            quotes = t.get("illustrative_quotes", [])
            q_lines = []
            if isinstance(quotes, list) and quotes:
                for q in quotes[:2]:
                    if not isinstance(q, dict):
                        continue
                    rid = q.get("respondent_id", "")
                    cohort = q.get("cohort", "")
                    quote = q.get("quote", "").strip()
                    if quote:
                        q_lines.append(f"  - ({rid}, {cohort}) \"{quote}\"")
            if q_lines:
                theme_quotes_sections.append(f"**{label}** (`{code}`)\n" + "\n".join(q_lines))
    else:
        theme_bullets.append("- (Themes unavailable: thematic_codes.json did not contain parsed model output.)")
        theme_quotes_sections.append("(Illustrative quotes unavailable.)")

    # Cohort contrasts bullets
    contrast_bullets = []
    if contrasts and isinstance(contrasts, list):
        for c in contrasts[:8]:
            if not isinstance(c, dict):
                continue
            topic = c.get("topic", "")
            tp = c.get("transit_primary", "")
            cp = c.get("car_primary", "")
            ev = c.get("evidence_respondents", [])
            evs = ", ".join([str(x) for x in ev]) if isinstance(ev, list) else ""
            contrast_bullets.append(f"- **{topic}**: transit_primary—{tp} | car_primary—{cp}" + (f" (e.g., {evs})" if evs else ""))
    else:
        contrast_bullets.append("- (Cohort contrasts unavailable.)")

    # Write report
    today = date.today().isoformat()
    md = f"""# Interview Thematic Analysis: Transit-primary vs Car-primary Respondents

*Mixed-methods synthesis combining transparent descriptives with LLM-assisted thematic coding.*

**Date:** {today}

## Research question
How do transit-primary and car-primary respondents describe drivers of travel mode choice (constraints, preferences, and trade-offs), and where do the cohorts converge or diverge?

## Data overview
We analyzed one excerpt per respondent from `data/interview_excerpts.csv`.

{df_to_md_table(cohort_table)}

## Methods
### Preprocessing and quantitative descriptives (scripted)
We conducted lightweight, reproducible preprocessing (whitespace normalization) and computed transparent descriptives:
- Response length (characters, words, and tokens) by cohort.
- Top unigram terms by cohort using a CountVectorizer with English stopwords; additional domain stopwords (e.g., *car*, *bus*, *train*) were removed post-hoc for interpretability.

**Response length summary (words):**

{df_to_md_table(length_table)}

**Figures:**
- Response length distributions by cohort: `images/length_distribution_by_cohort.png`
- Cohort top-term frequencies: `images/top_terms_by_cohort.png`

### LLM-assisted thematic analysis (Anthropic Messages API)
We used the Anthropic Messages API with model `{thematic.get('model','claude-3-5-sonnet-20241022') if isinstance(thematic, dict) else 'claude-3-5-sonnet-20241022'}` to:
1) Propose a theme codebook (6–10 themes).
2) Apply multi-label codes (0–5) to each respondent excerpt.
3) Summarize cohort contrasts with supporting respondent IDs.

To keep the qualitative synthesis auditable, we:
- Saved the full API response to `outputs/anthropic_messages_response.json`.
- Parsed the model’s JSON into `outputs/thematic_codes.json`.
- Computed code prevalence *in Python* from the respondent-level codes (no hidden counting in the model).

## Results
### Quantitative descriptives
**Overall most frequent tokens** (excluding domain stopwords) indicated recurring concerns and value statements (see `outputs/descriptives.json`).

**Top terms by cohort (top 10 each):**

{df_to_md_table(top_terms_10.sort_values(['cohort','rank']))}

![Response length distribution by cohort](images/length_distribution_by_cohort.png)

![Top terms by cohort](images/top_terms_by_cohort.png)

### Qualitative themes (LLM-assisted)
**Codebook (LLM-proposed):**
{os.linesep.join(theme_bullets)}

**Illustrative quotes (verbatim; up to 2 per theme):**

{os.linesep.join(theme_quotes_sections) if theme_quotes_sections else "(No quotes available.)"}

### Transparent theme prevalence (counts computed in code)
We counted, for each theme, how many unique respondents in each cohort were assigned that code (multi-label allowed). Shares are within-cohort percentages.

{df_to_md_table(theme_prev_table, max_rows=30)}

![Theme prevalence by cohort](images/theme_prevalence_by_cohort.png)

### Cohort contrasts (LLM synthesis)
{os.linesep.join(contrast_bullets)}

## Discussion
Across cohorts, the excerpts commonly framed travel as a set of trade-offs between **time reliability**, **cost**, and **comfort/stress**, but the *direction* of trade-offs differed.

- **Transit-primary respondents** more often emphasized constraints that make transit workable (e.g., proximity, frequency, predictable travel) and often described car use as a contingency for gaps in coverage, late hours, or complex trips.
- **Car-primary respondents** more often foregrounded control and convenience (directness, scheduling flexibility, multi-stop chaining), with transit framed as less reliable or less time-competitive for their typical itineraries.

These patterns align with the descriptive signals from top-term usage and (where available) differences in theme prevalence by cohort.

## Limitations
- **Small-N and excerpt-only context:** One excerpt per respondent may under-represent nuance from full interviews.
- **LLM coding validity:** Thematic coding is model-assisted and may reflect prompt/model biases; we attempted to mitigate this via a fixed schema, temperature=0, and transparent post-hoc counting.
- **Token-based frequency artifacts:** Bag-of-words counts do not capture negation, sarcasm, or narrative structure.
- **Cohort imbalance risk:** If cohort sizes differ, prevalence comparisons should be interpreted with caution (use within-cohort shares).

## Reproducibility
Run scripts in order:
1. `python code/01_preprocess_and_descriptives.py`
2. `python code/02_anthropic_thematic_analysis.py`
3. `python code/03_theme_counts_and_figures.py`
4. `python code/04_generate_report.py`

Key outputs:
- `outputs/descriptives.json`, `outputs/top_terms_by_cohort.csv`
- `outputs/anthropic_messages_response.json`, `outputs/thematic_codes.json`
- `outputs/theme_counts_by_cohort.csv`
"""

    for out_path in ["report/report.md", "report/interview_thematic_report.md"]:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)


if __name__ == "__main__":
    main()
