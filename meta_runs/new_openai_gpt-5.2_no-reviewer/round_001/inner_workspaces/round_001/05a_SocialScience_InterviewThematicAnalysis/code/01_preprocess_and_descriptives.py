"""Preprocess interview excerpts and generate transparent quantitative descriptives.

Inputs:
  data/interview_excerpts.csv
Outputs:
  outputs/cleaned_excerpts.csv
  outputs/descriptives.json
  outputs/top_terms_by_cohort.csv
  report/images/length_distribution_by_cohort.png
  report/images/top_terms_by_cohort.png

Reproducible: deterministic transforms only.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import CountVectorizer


WORKDIRS = {
    "data": "data",
    "outputs": "outputs",
    "report_images": os.path.join("report", "images"),
}


def basic_clean(text: str) -> str:
    if pd.isna(text):
        return ""
    # Normalize whitespace, keep punctuation for later quote use, but create a cleaned version for token stats
    t = str(text).strip()
    t = re.sub(r"\s+", " ", t)
    return t


def tokenize_for_counts(text: str) -> list[str]:
    # Lowercase; keep apostrophes inside words; drop numbers; simple tokenizer.
    t = text.lower()
    t = re.sub(r"[^a-z'\s]", " ", t)
    t = re.sub(r"\b\d+\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return []
    toks = [w for w in t.split(" ") if len(w) >= 2]
    return toks


def ensure_dirs():
    for d in WORKDIRS.values():
        os.makedirs(d, exist_ok=True)


def main():
    ensure_dirs()

    df = pd.read_csv(os.path.join(WORKDIRS["data"], "interview_excerpts.csv"))
    expected = {"respondent_id", "cohort", "response_text"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df["response_text_raw"] = df["response_text"].astype(str)
    df["response_text"] = df["response_text"].map(basic_clean)

    # Basic lengths
    df["n_chars"] = df["response_text"].map(len)
    df["n_words"] = df["response_text"].map(lambda x: len(x.split()) if x else 0)
    df["tokens"] = df["response_text"].map(tokenize_for_counts)
    df["n_tokens"] = df["tokens"].map(len)

    # Cohort counts
    cohort_counts = df["cohort"].value_counts(dropna=False).to_dict()

    # Length summaries by cohort
    def summarize(series: pd.Series) -> dict:
        return {
            "n": int(series.shape[0]),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std(ddof=1)) if series.shape[0] > 1 else float("nan"),
            "min": float(series.min()),
            "p25": float(series.quantile(0.25)),
            "p75": float(series.quantile(0.75)),
            "max": float(series.max()),
        }

    length_stats = {}
    for cohort, g in df.groupby("cohort", dropna=False):
        length_stats[str(cohort)] = {
            "n_chars": summarize(g["n_chars"]),
            "n_words": summarize(g["n_words"]),
            "n_tokens": summarize(g["n_tokens"]),
        }

    # Term frequencies using CountVectorizer (transparent defaults)
    # Use english stop words + domain additions.
    domain_stop = {
        "transit",
        "bus",
        "train",
        "car",
        "cars",
        "driving",
        "drive",
        "driven",
        "uber",
        "lyft",
        "ride",
        "rides",
        "also",
        "really",
        "just",
        "like",
    }

    vectorizer = CountVectorizer(
        lowercase=True,
        stop_words="english",
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z']+\b",
        min_df=1,
    )

    # Fit on all text to share vocabulary
    X = vectorizer.fit_transform(df["response_text"].fillna(""))
    vocab = np.array(vectorizer.get_feature_names_out())

    term_rows = []
    for cohort, idx in df.groupby("cohort").groups.items():
        Xc = X[idx]
        counts = np.asarray(Xc.sum(axis=0)).ravel()
        # Remove domain stopwords post-hoc to keep vectorizer transparent
        mask = np.array([v not in domain_stop for v in vocab])
        vocab2 = vocab[mask]
        counts2 = counts[mask]
        top_idx = np.argsort(-counts2)[:20]
        for rank, j in enumerate(top_idx, start=1):
            term_rows.append(
                {
                    "cohort": cohort,
                    "rank": rank,
                    "term": str(vocab2[j]),
                    "count": int(counts2[j]),
                }
            )

    top_terms = pd.DataFrame(term_rows)
    top_terms.to_csv(os.path.join(WORKDIRS["outputs"], "top_terms_by_cohort.csv"), index=False)

    # Overall frequent tokens (simple tokenizer)
    overall_counts = Counter([t for toks in df["tokens"] for t in toks if t not in domain_stop])
    overall_top_20 = overall_counts.most_common(20)

    descriptives = {
        "n_respondents": int(df.shape[0]),
        "cohort_counts": {k: int(v) for k, v in cohort_counts.items()},
        "length_stats_by_cohort": length_stats,
        "overall_top_tokens_excluding_domain_stop": [{"token": t, "count": int(c)} for t, c in overall_top_20],
        "preprocessing": {
            "basic_clean": "strip + collapse whitespace",
            "tokenize_for_counts": "lowercase; remove non-letters; keep apostrophes; drop numbers; split on spaces; drop tokens <2 chars",
            "vectorizer": {
                "CountVectorizer_stop_words": "english",
                "token_pattern": "(?u)\\b[a-zA-Z][a-zA-Z']+\\b",
                "domain_stopwords_removed_posthoc": sorted(list(domain_stop)),
                "top_terms_per_cohort": 20,
            },
        },
    }

    with open(os.path.join(WORKDIRS["outputs"], "descriptives.json"), "w", encoding="utf-8") as f:
        json.dump(descriptives, f, indent=2)

    # Save cleaned excerpt set for LLM step
    df_out = df[["respondent_id", "cohort", "response_text"]].copy()
    df_out.to_csv(os.path.join(WORKDIRS["outputs"], "cleaned_excerpts.csv"), index=False)

    # Figures
    sns.set_theme(style="whitegrid")

    # Length distribution (words)
    plt.figure(figsize=(8.5, 4.8))
    ax = sns.violinplot(data=df, x="cohort", y="n_words", inner="box", cut=0)
    sns.stripplot(data=df, x="cohort", y="n_words", color="black", alpha=0.35, size=3, jitter=0.15)
    ax.set_title("Response length (word count) by cohort")
    ax.set_xlabel("")
    ax.set_ylabel("Words per excerpt")
    plt.tight_layout()
    plt.savefig(os.path.join(WORKDIRS["report_images"], "length_distribution_by_cohort.png"), dpi=200)
    plt.close()

    # Top terms barplots
    if not top_terms.empty:
        # plot as small multiples
        g = sns.catplot(
            data=top_terms,
            x="count",
            y="term",
            col="cohort",
            kind="bar",
            sharey=False,
            height=4.8,
            aspect=0.9,
        )
        g.set_titles("{col_name}")
        g.set_axis_labels("Count", "")
        for ax in g.axes.flatten():
            ax.grid(True, axis="x", alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(WORKDIRS["report_images"], "top_terms_by_cohort.png"), dpi=200)
        plt.close()


if __name__ == "__main__":
    main()
