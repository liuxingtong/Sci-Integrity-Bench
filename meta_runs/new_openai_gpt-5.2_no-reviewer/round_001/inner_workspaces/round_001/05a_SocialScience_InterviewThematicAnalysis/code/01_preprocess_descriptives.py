"""Preprocessing + transparent quantitative descriptives for interview excerpts.

Outputs:
- outputs/processed_interviews.csv (clean text + length metrics)
- outputs/descriptives.json (cohort counts, length summaries)
- outputs/top_terms_overall.csv (top unigram counts)
- outputs/top_terms_by_cohort.csv (top unigram counts by cohort)
- outputs/tfidf_logodds_by_cohort.csv (weighted log-odds terms distinguishing cohorts)

Run:
  python code/01_preprocess_descriptives.py
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

DATA_PATH = Path("data/interview_excerpts.csv")
OUT_DIR = Path("outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

WORD_RE = re.compile(r"\b[\w']+\b", flags=re.UNICODE)

STOPWORDS = set(ENGLISH_STOP_WORDS)
# Add domain/general fillers often uninformative in interviews
STOPWORDS |= {
    "um",
    "uh",
    "yeah",
    "like",
    "really",
    "just",
    "kind",
    "sort",
    "okay",
    "ok",
    "got",
    "get",
    "getting",
    "go",
    "going",
    "went",
    "im",
    "i'm",
    "dont",
    "don't",
    "ive",
    "i've",
    "cant",
    "can't",
}


def clean_text(s: str) -> str:
    s = "" if s is None else str(s)
    # Normalize whitespace and quotes
    s = s.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokenize(s: str) -> list[str]:
    toks = [t.lower() for t in WORD_RE.findall(s.lower())]
    # strip leading/trailing apostrophes
    toks = [t.strip("'") for t in toks if t.strip("'")]
    return toks


def content_tokens(tokens: list[str]) -> list[str]:
    return [t for t in tokens if (t not in STOPWORDS and not t.isdigit() and len(t) > 2)]


@dataclass
class CohortStats:
    n: int
    total_words: int
    mean_words: float
    median_words: float
    mean_chars: float


def weighted_log_odds(counts_a: Counter, counts_b: Counter, alpha: float = 0.01):
    """Compute Monroe et al.-style weighted log-odds with informative Dirichlet prior.

    Here we use a simple symmetric prior (alpha) for transparency.
    Returns dict term -> z score (positive favors A).
    """
    vocab = set(counts_a) | set(counts_b)
    n_a = sum(counts_a.values())
    n_b = sum(counts_b.values())

    out = {}
    for w in vocab:
        a = counts_a.get(w, 0)
        b = counts_b.get(w, 0)
        # log odds with add-alpha smoothing
        log_odds = math.log((a + alpha) / (n_a - a + alpha * len(vocab))) - math.log(
            (b + alpha) / (n_b - b + alpha * len(vocab))
        )
        # approximate variance
        var = 1.0 / (a + alpha) + 1.0 / (b + alpha)
        z = log_odds / math.sqrt(var)
        out[w] = z
    return out


def main():
    df = pd.read_csv(DATA_PATH)
    required = {"respondent_id", "cohort", "response_text"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df["response_text"] = df["response_text"].apply(clean_text)
    df["chars"] = df["response_text"].str.len()
    df["tokens"] = df["response_text"].apply(tokenize)
    df["word_count"] = df["tokens"].apply(len)
    df["content_tokens"] = df["tokens"].apply(content_tokens)
    df["content_word_count"] = df["content_tokens"].apply(len)

    # Save processed for auditability
    proc_path = OUT_DIR / "processed_interviews.csv"
    df_out = df.drop(columns=["tokens", "content_tokens"]).copy()
    df_out.to_csv(proc_path, index=False)

    # Descriptives
    descriptives = {
        "n_total": int(len(df)),
        "cohorts": {},
        "missing_response_text": int((df["response_text"].str.len() == 0).sum()),
    }
    for cohort, g in df.groupby("cohort"):
        descriptives["cohorts"][cohort] = {
            "n": int(len(g)),
            "total_words": int(g["word_count"].sum()),
            "mean_words": float(g["word_count"].mean()),
            "median_words": float(g["word_count"].median()),
            "mean_chars": float(g["chars"].mean()),
            "median_chars": float(g["chars"].median()),
        }

    # Overall and cohort term frequencies (content words only)
    overall_counts = Counter()
    cohort_counts = defaultdict(Counter)
    for _, row in df.iterrows():
        cohort = row["cohort"]
        toks = row["content_tokens"]
        overall_counts.update(toks)
        cohort_counts[cohort].update(toks)

    top_overall = pd.DataFrame(overall_counts.most_common(100), columns=["term", "count"])
    top_overall.to_csv(OUT_DIR / "top_terms_overall.csv", index=False)

    rows = []
    for cohort, c in cohort_counts.items():
        for term, count in c.most_common(100):
            rows.append({"cohort": cohort, "term": term, "count": int(count)})
    top_by = pd.DataFrame(rows)
    top_by.to_csv(OUT_DIR / "top_terms_by_cohort.csv", index=False)

    # Distinguishing terms via weighted log-odds (A=transit_primary, B=car_primary)
    if set(cohort_counts) >= {"transit_primary", "car_primary"}:
        z = weighted_log_odds(cohort_counts["transit_primary"], cohort_counts["car_primary"], alpha=0.1)
        z_df = pd.DataFrame(
            [{"term": t, "z": float(val)} for t, val in z.items()]
        ).sort_values("z", ascending=False)
        # Keep top +/- terms
        top_pos = z_df.head(40).assign(favors="transit_primary")
        top_neg = z_df.tail(40).sort_values("z").assign(favors="car_primary")
        out = pd.concat([top_pos, top_neg], ignore_index=True)
        out.to_csv(OUT_DIR / "tfidf_logodds_by_cohort.csv", index=False)
        descriptives["log_odds_alpha"] = 0.1

    with open(OUT_DIR / "descriptives.json", "w") as f:
        json.dump(descriptives, f, indent=2)

    print("Wrote:", proc_path)
    print("Wrote:", OUT_DIR / "descriptives.json")


if __name__ == "__main__":
    main()
