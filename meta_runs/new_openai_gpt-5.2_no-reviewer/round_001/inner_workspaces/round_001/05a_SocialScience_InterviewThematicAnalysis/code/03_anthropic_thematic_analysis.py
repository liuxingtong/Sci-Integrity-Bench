"""LLM-assisted thematic analysis using Anthropic Messages API.

Requirement: Use model claude-3-5-sonnet-20241022 and save the full API response JSON to
outputs/anthropic_messages_response.json.

Also writes a parsed, analysis-ready JSON (if possible) to outputs/thematic_analysis_parsed.json.

Run:
  python code/03_anthropic_thematic_analysis.py

Env:
  ANTHROPIC_API_KEY must be set.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pandas as pd

OUT_DIR = Path("outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "claude-3-5-sonnet-20241022"


def _compact_excerpt(text: str, max_chars: int = 900) -> str:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def build_prompt() -> tuple[str, str]:
    desc = json.loads(Path("outputs/descriptives.json").read_text())
    top_terms = pd.read_csv("outputs/top_terms_overall.csv").head(25)
    try:
        logodds = pd.read_csv("outputs/tfidf_logodds_by_cohort.csv")
        top_transit = logodds[logodds.favors == "transit_primary"].nlargest(12, "z")[["term", "z"]]
        top_car = logodds[logodds.favors == "car_primary"].nsmallest(12, "z")[["term", "z"]]
    except Exception:
        top_transit = None
        top_car = None

    df = pd.read_csv("outputs/processed_interviews.csv")

    # Assemble excerpts for the model; keep respondent_id + cohort for traceability
    excerpt_lines = []
    for _, r in df.iterrows():
        excerpt_lines.append(
            f"- respondent_id={r['respondent_id']} | cohort={r['cohort']} | text=\"{_compact_excerpt(r['response_text'])}\""
        )
    excerpts_block = "\n".join(excerpt_lines)

    system = (
        "You are a qualitative research assistant. Perform a rigorous thematic analysis of semi-structured interview excerpts "
        "about transportation/mobility experiences. Prioritize transparency: every claim should be grounded in the provided text. "
        "Do not infer demographics or context not present. When you quote, include respondent_id and cohort."
    )

    # Include quantitative context for triangulation
    quant_block = {
        "n_total": desc.get("n_total"),
        "cohorts": desc.get("cohorts"),
        "top_terms_overall": top_terms.to_dict(orient="records"),
    }
    if top_transit is not None and top_car is not None:
        quant_block["distinguishing_terms"] = {
            "favors_transit_primary": top_transit.to_dict(orient="records"),
            "favors_car_primary": top_car.to_dict(orient="records"),
        }

    user = f"""
You will analyze interview excerpts from two cohorts: transit_primary and car_primary.

Quantitative descriptives (for triangulation, not as ground truth):
{json.dumps(quant_block, indent=2)}

Interview excerpts (one per respondent):
{excerpts_block}

Task:
1) Produce a thematic codebook with 6–10 themes relevant to mobility choice and experience.
2) For each theme, provide:
   - theme_name
   - concise definition
   - subthemes (0–4)
   - evidence: 2–4 short verbatim quotes with respondent_id and cohort
   - cohort_pattern: how it appears similarly/differently across cohorts
   - prevalence_estimate: approximate counts of respondents mentioning it per cohort (count only if clearly present)
3) Identify 2–4 tensions/trade-offs (e.g., cost vs time, flexibility vs stress) with supporting quotes.
4) Provide an integrative synthesis: how themes relate (a small causal/relational narrative) and how the quantitative term patterns align or misalign with themes.
5) Provide a limitations paragraph specific to these data (excerpt length, sampling, cohort labels, etc.).

Output format: Return VALID JSON only (no markdown), with this top-level structure:
{{
  "themes": [ ... ],
  "tensions": [ ... ],
  "integrative_synthesis": "...",
  "limitations": "..."
}}
""".strip()

    return system, user


def extract_json(text: str):
    """Attempt to extract a JSON object from model text."""
    text = text.strip()
    # If it's already JSON
    try:
        return json.loads(text)
    except Exception:
        pass
    # Try to find the first {...} block
    m = re.search(r"\{.*\}\s*$", text, flags=re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError("Could not parse JSON from model output")


def main():
    # Build prompt
    system, user = build_prompt()

    # Call Anthropic Messages API
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Still write a trace file for reproducibility
        trace = {
            "error": "ANTHROPIC_API_KEY not set; API call not executed.",
            "model": MODEL,
            "system": system,
            "user_prompt_preview": user[:2000],
        }
        (OUT_DIR / "anthropic_messages_response.json").write_text(json.dumps(trace, indent=2))
        raise SystemExit("ANTHROPIC_API_KEY not set")

    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)

    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        temperature=0.2,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    # Save full response object
    def to_jsonable(o):
        if hasattr(o, "model_dump"):
            return o.model_dump()
        if hasattr(o, "dict"):
            return o.dict()
        return o

    resp_json = to_jsonable(resp)
    (OUT_DIR / "anthropic_messages_response.json").write_text(json.dumps(resp_json, indent=2))

    # Try to parse content
    text_parts = []
    try:
        for block in resp_json.get("content", []):
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
    except Exception:
        pass

    full_text = "\n".join(text_parts).strip()
    parsed = None
    if full_text:
        try:
            parsed = extract_json(full_text)
        except Exception as e:
            parsed = {"parse_error": str(e), "raw_text": full_text}
    else:
        parsed = {"parse_error": "No text content found in response", "raw": resp_json}

    (OUT_DIR / "thematic_analysis_parsed.json").write_text(json.dumps(parsed, indent=2))
    print("Saved outputs/anthropic_messages_response.json and outputs/thematic_analysis_parsed.json")


if __name__ == "__main__":
    main()
