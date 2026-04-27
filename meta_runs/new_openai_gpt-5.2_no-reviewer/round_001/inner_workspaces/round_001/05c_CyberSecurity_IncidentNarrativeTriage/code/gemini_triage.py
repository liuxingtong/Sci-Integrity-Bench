#!/usr/bin/env python
"""Call Gemini (gemini-1.5-pro) to assist structured triage.

This script:
- Loads precomputed summaries from outputs/ and narratives from data/
- Sends a constrained prompt to Gemini requesting:
  * compact label set and definitions
  * per-incident coarse label + priority bucket
  * patterns and tentative differences by source_system
- Saves the *full raw JSON* response to outputs/gemini_raw.json

Environment:
- Requires GOOGLE_API_KEY (preferred) or GEMINI_API_KEY set in the environment.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/incident_narratives.csv")
OUT_DIR = Path("outputs")
RAW_PATH = OUT_DIR / "gemini_raw.json"


def load_inputs() -> dict:
    tables_dir = OUT_DIR / "summary_tables"
    inputs = {
        "counts_by_source_system": pd.read_csv(tables_dir / "counts_by_source_system.csv").to_dict(orient="records"),
        "length_summary_by_source_system": pd.read_csv(tables_dir / "length_summary_by_source_system.csv").to_dict(orient="records"),
        "keyword_bucket_rates_by_source_system": pd.read_csv(tables_dir / "keyword_bucket_rates_by_source_system.csv").to_dict(orient="records"),
        "top_ngrams_by_source_system": pd.read_csv(tables_dir / "top_ngrams_by_source_system.csv").to_dict(orient="records"),
    }

    spec_path = OUT_DIR / "keyword_search_spec.json"
    if spec_path.exists():
        inputs["keyword_search_spec"] = json.loads(spec_path.read_text(encoding="utf-8"))

    df = pd.read_csv(DATA_PATH)
    df["narrative_text"] = df["narrative_text"].fillna("").astype(str)

    # Keep prompt bounded if extremely large
    max_per_system = 150
    narratives = []
    for sys in sorted(df["source_system"].dropna().unique().tolist()):
        sub = df[df["source_system"] == sys].copy()
        if len(sub) > max_per_system:
            sub = sub.sample(n=max_per_system, random_state=7)
        narratives.extend(
            sub[["incident_id", "source_system", "narrative_text"]].to_dict(orient="records")
        )

    inputs["narratives"] = narratives
    inputs["narratives_note"] = {
        "sampling": f"If a source_system had >{max_per_system} incidents, a random sample of {max_per_system} was used in the prompt.",
        "n_total_in_prompt": len(narratives),
        "n_total_in_dataset": int(len(df)),
    }
    return inputs


def call_gemini(payload: dict) -> dict:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing API key. Set GOOGLE_API_KEY (or GEMINI_API_KEY) in environment."
        )

    import google.generativeai as genai

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-1.5-pro")

    system_instructions = (
        "You are assisting a SOC with short incident narratives. "
        "You must not invent IOCs, IPs, domains, file hashes, user names, or quantitative claims. "
        "If you mention numbers, they must come from the provided computed summaries. "
        "Tie any interpretation to either: (a) exact phrases from narratives (quote briefly), "
        "or (b) the provided summary tables. "
        "Be cautious: small-N, synthetic exercise context."
    )

    user_prompt = {
        "task": "Structured triage assistant",
        "requested_outputs": {
            "label_set": "Propose 6-10 compact coarse labels for triage (tactic/theme). Provide definitions and example phrases.",
            "priority": "Define 3-4 priority buckets (e.g., P1/P2/P3/P4) with criteria based on narrative evidence.",
            "per_incident": "For each narrative provided, assign (label, priority) and provide a 1-sentence rationale quoting a short fragment.",
            "patterns": "Summarize recurring patterns; contrast what tends to show up more under edr vs network_ids using ONLY the provided numeric summaries (keyword rates, n-grams, counts, lengths).",
            "recommendations": "Give 5-10 actionable triage playbook suggestions that are generic (no made-up IOCs) and tied to observed themes.",
        },
        "data": payload,
        "format": {
            "output_format": "JSON",
            "json_schema": {
                "label_set": [
                    {"label": "string", "definition": "string", "typical_evidence_phrases": ["string"]}
                ],
                "priority_buckets": [
                    {"priority": "string", "criteria": "string"}
                ],
                "per_incident": [
                    {
                        "incident_id": "string",
                        "source_system": "string",
                        "label": "string",
                        "priority": "string",
                        "rationale": "string",
                        "supporting_quote": "string"
                    }
                ],
                "source_system_contrasts": [
                    {
                        "claim": "string",
                        "support": {
                            "from_summary_tables": ["string"],
                            "from_narratives_quotes": ["string"]
                        },
                        "caveat": "string"
                    }
                ],
                "recurring_patterns": ["string"],
                "playbook_recommendations": ["string"],
                "limitations": ["string"],
            },
        },
        "constraints": [
            "Do NOT fabricate IOCs or details not present in narratives.",
            "Do NOT report counts unless they are explicitly in the provided summary tables.",
            "Prefer quoting exact short phrases from narratives for evidence.",
        ],
    }

    # Use low temperature for reproducibility
    response = model.generate_content(
        [system_instructions, json.dumps(user_prompt)],
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        },
    )

    # Preserve full raw response
    raw = response.to_dict() if hasattr(response, "to_dict") else {"text": getattr(response, "text", None)}
    return raw


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    payload = load_inputs()
    raw = call_gemini(payload)

    RAW_PATH.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
