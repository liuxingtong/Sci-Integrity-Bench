#!/usr/bin/env python3
"""Assemble report/report.md from computed outputs."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd


def md_table(df: pd.DataFrame, floatfmt: str = ".2f") -> str:
    # stable column order
    return df.to_markdown(index=False, floatfmt=floatfmt)


def main():
    report_path = Path("report/report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    counts = pd.read_csv("outputs/table_counts_by_source.csv")
    lengths = pd.read_csv("outputs/table_length_by_source.csv")
    kw = pd.read_csv("outputs/table_keyword_hits_by_source.csv")
    top_ngrams = pd.read_csv("outputs/top_ngrams_by_source.csv")

    # Pretty keyword table: long format with totals and per-source
    kw_long = kw.melt(id_vars=["source_system"], var_name="category", value_name="hits")
    kw_long["category"] = kw_long["category"].str.replace("^kw_", "", regex=True)
    kw_pivot = kw_long.pivot_table(index="category", columns="source_system", values="hits", aggfunc="sum", fill_value=0).reset_index()
    # Add total + simple difference
    src_cols = [c for c in kw_pivot.columns if c != "category"]
    if len(src_cols) == 2:
        a, b = src_cols
        kw_pivot["total"] = kw_pivot[a] + kw_pivot[b]
        kw_pivot["diff_(edr-network_ids)"] = kw_pivot.get("edr", 0) - kw_pivot.get("network_ids", 0)
    kw_pivot = kw_pivot.sort_values("total", ascending=False)

    # Top ngrams per source: show top 12
    top12 = top_ngrams.sort_values(["source_system", "count"], ascending=[True, False]).groupby("source_system").head(12)

    # Load Gemini extracted content if available
    gemini_text = None
    gemini_json = None
    if Path("outputs/gemini_extracted.txt").exists():
        gemini_text = Path("outputs/gemini_extracted.txt").read_text(encoding="utf-8")
    if Path("outputs/gemini_extracted.json").exists():
        gemini_json = json.loads(Path("outputs/gemini_extracted.json").read_text(encoding="utf-8"))

    # Render Gemini section
    if gemini_json:
        label_set = gemini_json.get("label_set", [])
        patterns = gemini_json.get("patterns", [])
        contrast = gemini_json.get("source_system_contrast", {})
        workflow = gemini_json.get("suggested_triage_workflow", [])

        # Convert label set to markdown list
        label_md = []
        for item in label_set:
            label_md.append(
                f"- **{item.get('label','')}** (priority: {item.get('suggested_priority','')}) — {item.get('definition','')}\n"
                f"  - Typical signals: {', '.join(item.get('typical_signals', [])[:8]) if isinstance(item.get('typical_signals'), list) else item.get('typical_signals','')}\n"
                f"  - Notes: {item.get('notes','')}"
            )
        patterns_md = []
        for p in patterns:
            sp = p.get("supporting_phrases", [])
            if isinstance(sp, list):
                sp = sp[:5]
            patterns_md.append(f"- **{p.get('pattern','')}** — supporting phrases: {sp}")
        workflow_md = "\n".join([f"{i+1}. {s}" for i, s in enumerate(workflow)]) if isinstance(workflow, list) else str(workflow)
        contrast_md = (
            "**EDR**: " + str(contrast.get("edr", "")) + "\n\n"
            "**Network IDS**: " + str(contrast.get("network_ids", "")) + "\n\n"
            "**Caveats**: " + str(contrast.get("caveats", ""))
        )
    else:
        label_md = ["Gemini structured JSON output not available; see `outputs/gemini_extracted.txt` for raw text (if present)."]
        patterns_md = []
        workflow_md = ""
        contrast_md = ""

    md = f"""# CyberSecurity Incident Narrative Triage (Scenario 05c)

## Overview
This report supports SOC triage for short incident narratives (synthetic exercise). Each record is an alert-cluster summary with a `source_system` label indicating which sensor family surfaced the cluster first (`edr` vs `network_ids`). The goal is to produce transparent, script-derived summaries and a compact structured triage scheme supported by those summaries.

## Methods
### Data
- Input file: `data/incident_narratives.csv`
- Fields used: `incident_id`, `source_system`, `narrative_text`

### Preprocessing (reproducible)
Implemented in `code/01_summarize.py`:
- Strip leading/trailing whitespace; normalize repeated whitespace.
- Normalize `source_system` to lowercase.
- Derive length features: character count, simple token count (regex tokens), and a rough sentence count (punctuation-based).
- Compute **keyword-category hit counts** using documented regex/substring patterns (see `KEYWORD_CATEGORIES` in `code/01_summarize.py`). These counts are intended as coarse triage signals, not ground truth.
- Compute top unigrams/bigrams per `source_system` via `CountVectorizer(stop_words='english', ngram_range=(1,2))`.

Outputs are written to `outputs/` (CSV tables plus `summary_for_llm.json`).

### LLM-assisted structured triage
Implemented in `code/03_call_gemini.py` using the Google Generative AI SDK with model **`gemini-1.5-pro`**. The prompt includes:
- Script-computed dataset summaries (counts and length statistics)
- Script-computed keyword hit totals and top n-grams by source
- A small subset of representative narratives (incident_id + text)

The full raw API response is saved verbatim to `outputs/gemini_raw.json`. The report summarizes the returned structured output (if present) and does not add new IOCs or numbers.

## Results

### Basic dataset composition
{md_table(counts)}

### Narrative length by source system
{md_table(lengths)}

Figures:
- Incident counts by source: ![](images/fig_counts_by_source.png)
- Narrative length distribution (words): ![](images/fig_length_words_by_source.png)

### Keyword-category hits (scripted regex counts)
Table shows total hit counts aggregated across narratives per source system.

{md_table(kw_pivot, floatfmt=".0f")}

Figure:
- Keyword-category hit totals by source: ![](images/fig_keyword_hits_by_source.png)

### Frequent n-grams by source system (top 12 each)
{md_table(top12)}

## LLM-assisted triage synthesis (Gemini)
### Proposed compact label set
""" + "\n".join(label_md) + f"""

### Recurring patterns (with supporting narrative phrases)
""" + ("\n".join(patterns_md) if patterns_md else "(No structured pattern list available.)") + f"""

### Tentative contrast by `source_system`
{contrast_md if contrast_md else "(No structured contrast section available.)"}

### Suggested triage workflow
{workflow_md if workflow_md else "(No workflow steps available.)"}

## Discussion
The scripted summaries provide a transparent, reproducible view of (i) dataset composition, (ii) narrative length differences, (iii) coarse keyword signals, and (iv) high-frequency terms by sensor family. These artifacts can support SOC triage by quickly surfacing which incident clusters mention concepts like credential access, malware execution, or beaconing.

The Gemini-assisted synthesis is best treated as an *organizational aid* for analysts: it proposes a label set and decision cues grounded in the provided narratives and computed summaries. Because narratives are short, synthetic, and not standardized, keyword counts and n-gram frequencies are approximate and should be interpreted as lightweight heuristics (e.g., “mentions of ‘powershell’” rather than confirmed execution).

## Limitations
- **Small-N / synthetic data**: patterns may not generalize to real-world SOC streams.
- **Heuristic text features**: regex keyword hits can over-count (false positives) or miss paraphrases (false negatives).
- **No ground truth**: `source_system` indicates which sensor family fired first, not the true locus of activity.
- **LLM output constraints**: the Gemini response is constrained to provided text and computed tables; it should not be treated as evidence without analyst verification.

## Reproducibility
Run, in order:
1. `python code/01_summarize.py`
2. `python code/02_make_figures.py`
3. `python code/03_call_gemini.py` (requires `GOOGLE_API_KEY`)
4. `python code/04_build_report.py`

All generated artifacts are written under `outputs/` and `report/images/`.
"""

    report_path.write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
