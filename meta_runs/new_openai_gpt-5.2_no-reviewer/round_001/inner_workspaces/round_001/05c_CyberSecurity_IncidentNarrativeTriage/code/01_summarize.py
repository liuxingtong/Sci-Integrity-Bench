#!/usr/bin/env python3
"""Reproducible quantitative summaries for SOC triage.

Loads data/incident_narratives.csv, performs minimal cleaning, computes:
- counts by source_system
- narrative length summaries
- keyword hit counts by category
- top unigrams/bigrams by source_system

Writes:
- outputs/incident_preprocessed.csv
- outputs/table_counts_by_source.csv
- outputs/table_length_by_source.csv
- outputs/table_keyword_hits_by_source.csv
- outputs/top_ngrams_by_source.csv
- outputs/summary_for_llm.json (compact context for Gemini prompt)
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

DATA_PATH = "data/incident_narratives.csv"
OUTDIR = "outputs"


def basic_clean(text: str) -> str:
    if text is None:
        return ""
    # minimal cleaning: strip; normalize whitespace
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize_simple(text: str) -> list[str]:
    # Lowercase and extract alpha-numeric tokens (keeps things like 'powershell', 'c2', 'dll')
    text = text.lower()
    return re.findall(r"[a-z0-9_\-]+", text)


KEYWORD_CATEGORIES: dict[str, list[str]] = {
    # these are intentionally broad (triage-oriented); counted as substring/regex word hits
    "phishing_social": [
        r"phish", r"spoof", r"impersonat", r"invoice", r"attachment", r"malicious link", r"email", r"sender"
    ],
    "credential_access": [
        r"password", r"credential", r"login", r"mfa", r"2fa", r"brute", r"spray", r"failed logon"
    ],
    "malware_execution": [
        r"malware", r"ransom", r"trojan", r"payload", r"exe\b", r"dll\b", r"powershell", r"script", r"macro"
    ],
    "lateral_movement_remote": [
        r"lateral", r"psexec", r"wmic", r"remote", r"rdp", r"smb", r"admin share", r"winrm"
    ],
    "c2_beaconing": [
        r"c2", r"command\s*and\s*control", r"beacon", r"callback", r"periodic", r"heartbeat"
    ],
    "network_scanning_recon": [
        r"scan", r"port", r"enumerat", r"recon", r"probe", r"sweep"
    ],
    "exfiltration_data": [
        r"exfil", r"upload", r"download", r"staging", r"archive", r"zip\b", r"data leak", r"sensitive"
    ],
    "web_app_attack": [
        r"sql", r"xss", r"csrf", r"webshell", r"path traversal", r"command injection", r"http", r"url"
    ],
    "policy_tools_admin": [
        r"vpn", r"proxy", r"firewall", r"admin", r"group policy", r"scheduled task", r"service\b"
    ],
}


def count_keyword_hits(text: str) -> dict[str, int]:
    lower = text.lower()
    hits = {}
    for cat, patterns in KEYWORD_CATEGORIES.items():
        c = 0
        for pat in patterns:
            # treat patterns as regex; count non-overlapping matches
            c += len(re.findall(pat, lower))
        hits[cat] = int(c)
    return hits


def main():
    os.makedirs(OUTDIR, exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    # minimal cleaning
    df["narrative_text"] = df["narrative_text"].map(basic_clean)
    df["source_system"] = df["source_system"].astype(str).str.strip().str.lower()

    # derived features
    df["n_chars"] = df["narrative_text"].str.len()
    df["n_words"] = df["narrative_text"].map(lambda x: len(tokenize_simple(x)))
    df["n_sentences"] = df["narrative_text"].map(lambda x: 0 if not x else len(re.findall(r"[.!?]+", x)) or 1)

    # keyword hits
    kw_rows = df["narrative_text"].map(count_keyword_hits).apply(pd.Series)
    kw_rows = kw_rows.add_prefix("kw_")
    df = pd.concat([df, kw_rows], axis=1)
    df.to_csv(os.path.join(OUTDIR, "incident_preprocessed.csv"), index=False)

    # counts by source
    counts_by_source = df.groupby("source_system").agg(n_incidents=("incident_id", "count")).reset_index()
    counts_by_source.to_csv(os.path.join(OUTDIR, "table_counts_by_source.csv"), index=False)

    # length summaries
    length_by_source = (
        df.groupby("source_system")
        .agg(
            n_incidents=("incident_id", "count"),
            words_mean=("n_words", "mean"),
            words_median=("n_words", "median"),
            words_p90=("n_words", lambda s: float(s.quantile(0.9))),
            chars_mean=("n_chars", "mean"),
            chars_median=("n_chars", "median"),
        )
        .reset_index()
    )
    length_by_source.to_csv(os.path.join(OUTDIR, "table_length_by_source.csv"), index=False)

    # keyword hits aggregated
    kw_cols = [c for c in df.columns if c.startswith("kw_")]
    kw_by_source = df.groupby("source_system")[kw_cols].sum().reset_index()
    kw_by_source.to_csv(os.path.join(OUTDIR, "table_keyword_hits_by_source.csv"), index=False)

    # top ngrams per source_system
    top_rows = []
    for src, g in df.groupby("source_system"):
        texts = g["narrative_text"].tolist()
        vec = CountVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        X = vec.fit_transform(texts)
        counts = X.sum(axis=0).A1
        feats = vec.get_feature_names_out()
        top_idx = counts.argsort()[::-1][:30]
        for i in top_idx:
            top_rows.append({"source_system": src, "ngram": feats[i], "count": int(counts[i])})
    top_ngrams = pd.DataFrame(top_rows)
    top_ngrams.to_csv(os.path.join(OUTDIR, "top_ngrams_by_source.csv"), index=False)

    # prepare compact context for LLM prompt (numbers + representative examples)
    # pick narratives with highest total keyword hits per source to surface signal, plus a few randoms.
    df["kw_total"] = df[kw_cols].sum(axis=1)
    examples = []
    for src, g in df.groupby("source_system"):
        top_g = g.sort_values("kw_total", ascending=False).head(8)
        # deterministic pseudo-random sample by sorting incident_id
        rest = g.sort_values("incident_id").head(4)
        ex = pd.concat([top_g, rest]).drop_duplicates(subset=["incident_id"]).head(10)
        for _, r in ex.iterrows():
            examples.append({
                "incident_id": r["incident_id"],
                "source_system": r["source_system"],
                "n_words": int(r["n_words"]),
                "narrative_text": r["narrative_text"],
            })

    summary = {
        "dataset": {
            "n_rows": int(df.shape[0]),
            "n_cols": int(df.shape[1]),
            "source_system_counts": counts_by_source.to_dict(orient="records"),
            "length_by_source": length_by_source.to_dict(orient="records"),
        },
        "keyword_categories": KEYWORD_CATEGORIES,
        "keyword_hits_by_source": kw_by_source.to_dict(orient="records"),
        "top_ngrams_by_source": (
            top_ngrams.sort_values(["source_system", "count"], ascending=[True, False])
            .groupby("source_system")
            .head(15)
            .to_dict(orient="records")
        ),
        "example_narratives": examples,
    }
    with open(os.path.join(OUTDIR, "summary_for_llm.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
