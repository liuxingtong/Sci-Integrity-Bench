#!/usr/bin/env python
"""Analyze synthetic SOC incident narratives.

Reproducible preprocessing and transparent quantitative summaries:
- dataset overview and counts by source_system
- narrative length distributions (words/chars)
- keyword/search-string frequency summaries (documented regex lists)
- simple unigram/bigram frequency

Outputs:
- outputs/summary_tables/*.csv
- report/images/*.png
"""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


DATA_PATH = Path("data/incident_narratives.csv")
OUT_DIR = Path("outputs")
TABLE_DIR = OUT_DIR / "summary_tables"
IMG_DIR = Path("report") / "images"


def normalize_text(s: str) -> str:
    if pd.isna(s):
        return ""
    s = str(s)
    # minimal cleaning: normalize whitespace; keep punctuation for later regex
    s = s.replace("\u2019", "'")
    s = re.sub(r"\s+", " ", s).strip()
    return s


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-\.]*")


def tokens_lower(s: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(s or "")]


def compute_keyword_flags(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Compute counts for documented search strings.

    Returns:
      df_flags: incident-level boolean columns per keyword bucket
      spec: dict describing the regex patterns (for reporting)
    """

    # Buckets are intentionally coarse and explainable (search-string based).
    # Patterns chosen to match common SOC narrative phrasing; they are not exhaustive.
    buckets: dict[str, list[str]] = {
        "credential_access_auth": [
            r"\bbrute\s*force\b",
            r"\bpassword\s*spray\b",
            r"\bcredential\b",
            r"\blogin\b",
            r"\bauth(entication|orization)?\b",
            r"\bfailed\s+log(in|on)\b",
            r"\bmfa\b",
        ],
        "phishing_social": [
            r"\bphish(ing)?\b",
            r"\bspear\s*phish\b",
            r"\bmalicious\s+email\b",
            r"\battachment\b",
            r"\blink\b",
            r"\binvoice\b",
        ],
        "malware_execution": [
            r"\bmalware\b",
            r"\bransom(ware)?\b",
            r"\btrojan\b",
            r"\bexe\b",
            r"\bscript\b",
            r"\bpowershell\b",
            r"\bmacro\b",
        ],
        "c2_network": [
            r"\bcommand\s+and\s+control\b",
            r"\bc2\b",
            r"\bbeacon\b",
            r"\bcallback\b",
            r"\boutbound\b",
            r"\bdns\b",
            r"\bhttp(s)?\b",
        ],
        "lateral_movement_remote": [
            r"\blateral\s+movement\b",
            r"\brdp\b",
            r"\bpsremoting\b",
            r"\bwinrm\b",
            r"\bsmb\b",
            r"\bremote\s+desktop\b",
        ],
        "discovery_scanning": [
            r"\bport\s+scan\b",
            r"\bscan(ned|ning)?\b",
            r"\benumerat(e|ion)\b",
            r"\bdiscovery\b",
            r"\bnmap\b",
        ],
        "exfiltration_data": [
            r"\bexfiltrat(e|ion)\b",
            r"\bdata\s+loss\b",
            r"\bupload\b",
            r"\barchive\b",
            r"\bzip\b",
            r"\bcompress\b",
        ],
        "impact_availability": [
            r"\bdenial\s+of\s+service\b",
            r"\bdos\b",
            r"\bservice\s+down\b",
            r"\boutage\b",
            r"\bencrypt(ed|ion)\b",
        ],
        "response_actions": [
            r"\bisolat(ed|ion|e)\b",
            r"\bblock(ed|ing)?\b",
            r"\bquarantin(ed|e)\b",
            r"\breset\b",
            r"\bdisabled\b",
            r"\bcontain(ment|ed)?\b",
            r"\btriage\b",
            r"\bclosed\b",
        ],
        "false_positive_benign": [
            r"\bfalse\s+positive\b",
            r"\bbenign\b",
            r"\bexpected\b",
            r"\btest(ing)?\b",
        ],
    }

    compiled = {k: [re.compile(p, flags=re.IGNORECASE) for p in pats] for k, pats in buckets.items()}

    def match_bucket(text: str, rex_list: list[re.Pattern]) -> bool:
        return any(r.search(text or "") for r in rex_list)

    flags = {}
    for bucket, rex_list in compiled.items():
        flags[bucket] = df["narrative_clean"].apply(lambda t: match_bucket(t, rex_list)).astype(int)

    df_flags = pd.DataFrame(flags)
    spec = {k: buckets[k] for k in buckets}
    return df_flags, spec


def top_ngrams(texts: list[str], n: int = 1, topk: int = 25, stopwords: set[str] | None = None) -> list[tuple[str, int]]:
    stopwords = stopwords or set()
    counts = Counter()
    for t in texts:
        toks = [x for x in tokens_lower(t) if x not in stopwords]
        if n == 1:
            grams = toks
        else:
            grams = [" ".join(toks[i : i + n]) for i in range(0, max(0, len(toks) - n + 1))]
        counts.update(grams)
    return counts.most_common(topk)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)

    # Minimal schema checks
    expected_cols = {"incident_id", "source_system", "narrative_text"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Preprocess
    df["narrative_clean"] = df["narrative_text"].map(normalize_text)
    df["narrative_lower"] = df["narrative_clean"].str.lower()
    df["n_chars"] = df["narrative_clean"].str.len()
    df["n_words"] = df["narrative_clean"].apply(lambda s: len(tokens_lower(s)))

    # Basic summaries
    counts_by_system = df["source_system"].value_counts(dropna=False).rename_axis("source_system").reset_index(name="n_incidents")
    counts_by_system.to_csv(TABLE_DIR / "counts_by_source_system.csv", index=False)

    len_summary = (
        df.groupby("source_system")[["n_words", "n_chars"]]
        .agg(["count", "mean", "median", "min", "max"])
        .reset_index()
    )
    # Flatten multiindex columns
    len_summary.columns = ["_".join([c for c in col if c]) if isinstance(col, tuple) else col for col in len_summary.columns]
    len_summary.to_csv(TABLE_DIR / "length_summary_by_source_system.csv", index=False)

    # Keyword flags
    df_flags, keyword_spec = compute_keyword_flags(df)
    df_k = pd.concat([df[["incident_id", "source_system"]], df_flags], axis=1)
    df_k.to_csv(TABLE_DIR / "incident_keyword_flags.csv", index=False)

    keyword_rate = (
        df_k.groupby("source_system")[list(df_flags.columns)]
        .agg(["sum", "mean"])
        .reset_index()
    )
    keyword_rate.columns = ["_".join([c for c in col if c]) if isinstance(col, tuple) else col for col in keyword_rate.columns]
    keyword_rate.to_csv(TABLE_DIR / "keyword_bucket_rates_by_source_system.csv", index=False)

    # N-gram summaries (transparent; simple tokenization)
    stop = {
        "the",
        "and",
        "to",
        "of",
        "a",
        "in",
        "on",
        "for",
        "was",
        "were",
        "is",
        "are",
        "with",
        "as",
        "at",
        "by",
        "from",
        "an",
        "be",
        "this",
        "that",
        "it",
        "we",
        "they",
        "our",
        "their",
        "user",
        "host",
        "device",
        "system",
        "alert",
        "detected",
        "activity",
    }

    ngram_rows = []
    for sys in sorted(df["source_system"].dropna().unique().tolist()):
        texts = df.loc[df["source_system"] == sys, "narrative_clean"].tolist()
        for n in [1, 2]:
            top = top_ngrams(texts, n=n, topk=30, stopwords=stop)
            for gram, c in top:
                ngram_rows.append({"source_system": sys, "ngram_n": n, "ngram": gram, "count": c})

    ngrams_df = pd.DataFrame(ngram_rows)
    ngrams_df.to_csv(TABLE_DIR / "top_ngrams_by_source_system.csv", index=False)

    # Bucket rate differences (edr - network_ids) for quick triage signal (not statistical significance)
    means = df_k.groupby("source_system")[list(df_flags.columns)].mean()
    if set(["edr", "network_ids"]).issubset(means.index):
        diffs = (means.loc["edr"] - means.loc["network_ids"]).sort_values(ascending=False).reset_index()
        diffs.columns = ["bucket", "mean_rate_diff_edr_minus_network_ids"]
        diffs.to_csv(TABLE_DIR / "keyword_bucket_rate_differences_edr_minus_network_ids.csv", index=False)

    # Figures
    sns.set_theme(style="whitegrid")

    # Fig 1: counts by source_system
    plt.figure(figsize=(6, 4))
    ax = sns.barplot(data=counts_by_system, x="source_system", y="n_incidents", color="#4C72B0")
    ax.set_title("Incidents by source_system")
    ax.set_xlabel("source_system")
    ax.set_ylabel("Number of incidents")
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height())}", (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha="center", va="bottom", fontsize=10, xytext=(0, 3), textcoords="offset points")
    plt.tight_layout()
    plt.savefig(IMG_DIR / "fig1_counts_by_source_system.png", dpi=200)
    plt.close()

    # Fig 2: word count distribution
    plt.figure(figsize=(7, 4))
    ax = sns.boxplot(data=df, x="source_system", y="n_words", palette="Set2")
    ax.set_title("Narrative length (word count) by source_system")
    ax.set_xlabel("source_system")
    ax.set_ylabel("Words per narrative")
    plt.tight_layout()
    plt.savefig(IMG_DIR / "fig2_word_count_by_source_system.png", dpi=200)
    plt.close()

    # Fig 3: keyword bucket means (rate of mention)
    # Use mean per system; plot only buckets other than response_actions for readability
    plot_cols = [c for c in df_flags.columns]
    mean_df = df_k.groupby("source_system")[plot_cols].mean().reset_index().melt(id_vars="source_system", var_name="bucket", value_name="rate")
    plt.figure(figsize=(10, 5))
    ax = sns.barplot(data=mean_df, x="bucket", y="rate", hue="source_system")
    ax.set_title("Keyword-bucket mention rate by source_system (search-string based)")
    ax.set_xlabel("Bucket")
    ax.set_ylabel("Fraction of incidents mentioning bucket")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(IMG_DIR / "fig3_keyword_bucket_rates.png", dpi=200)
    plt.close()

    # Save preprocessing + keyword spec
    spec_path = OUT_DIR / "keyword_search_spec.json"
    import json

    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump({"token_regex": TOKEN_RE.pattern, "keyword_buckets": keyword_spec}, f, indent=2)

    # Save a compact dataset snapshot for LLM prompt construction
    df[["incident_id", "source_system", "narrative_clean", "n_words", "n_chars"]].to_csv(
        OUT_DIR / "incident_preprocessed.csv", index=False
    )


if __name__ == "__main__":
    main()
