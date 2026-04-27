"""Run LLM-assisted thematic analysis using Anthropic Messages API.

Requirement:
  - Use Anthropic Messages API only, model `claude-3-5-sonnet-20241022`.

Inputs:
  outputs/cleaned_excerpts.csv
Outputs:
  outputs/anthropic_messages_response.json  (raw API response or error object)
  outputs/thematic_codes.json               (parsed JSON payload if available)

Notes:
  - If the API key is missing or the call fails, we still write a structured error
    JSON to anthropic_messages_response.json so the pipeline remains reproducible.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime

import pandas as pd


MODEL_NAME = "claude-3-5-sonnet-20241022"


def extract_json_from_text(text: str) -> dict | None:
    """Best-effort extraction of a single top-level JSON object from model text."""
    if not text:
        return None
    # Find first '{' and last '}'
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    blob = text[start : end + 1]
    try:
        return json.loads(blob)
    except Exception:
        return None


def build_prompt(df: pd.DataFrame) -> str:
    # Keep prompt deterministic and constrained.
    rows = []
    for _, r in df.iterrows():
        rid = str(r["respondent_id"])
        cohort = str(r["cohort"])
        txt = str(r["response_text"]).strip()
        rows.append(f"- respondent_id: {rid} | cohort: {cohort}\n  excerpt: {txt}")

    rubric = """
You are assisting with qualitative thematic analysis of semi-structured interview excerpts about travel mode choice.

Task:
1) Propose a concise codebook (6–10 themes) that is grounded in the excerpts.
2) Apply the codes to EACH respondent excerpt (multi-label allowed; 0–5 codes per excerpt).
3) Provide cohort contrasts (transit_primary vs car_primary): where they converge/diverge.
4) Provide representative verbatim quotes with respondent_id and cohort for each theme.
5) Flag uncertainties/edge cases.

Output format STRICT:
Return a single valid JSON object ONLY (no markdown), following this schema:
{
  "themes": [
    {
      "code": "short_code",
      "label": "Human-readable label",
      "description": "1-3 sentences",
      "subthemes": ["..."],
      "illustrative_quotes": [
        {"respondent_id": "...", "cohort": "...", "quote": "..."}
      ]
    }
  ],
  "respondent_codes": [
    {
      "respondent_id": "...",
      "cohort": "...",
      "codes": ["short_code", "..."],
      "rationale": "1-2 sentences"
    }
  ],
  "cohort_contrasts": [
    {"topic": "...", "transit_primary": "...", "car_primary": "...", "evidence_respondents": ["id1","id2"]}
  ],
  "quality_checks": {
    "coding_notes": "...",
    "potential_biases": ["..."],
    "missing_info": ["..."]
  }
}

Constraints:
- Use ONLY codes listed in themes[].code.
- Keep codes stable (no duplicates).
- Quotes must be verbatim spans from excerpts.
- If an excerpt has no clear code, use an empty codes list.
""".strip()

    return rubric + "\n\nEXCERPTS:\n" + "\n".join(rows)


def main():
    os.makedirs("outputs", exist_ok=True)

    df = pd.read_csv("outputs/cleaned_excerpts.csv")
    df = df[["respondent_id", "cohort", "response_text"]].copy()

    prompt = build_prompt(df)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        err = {
            "ok": False,
            "error": "Missing ANTHROPIC_API_KEY in environment; cannot call Anthropic Messages API.",
            "model": MODEL_NAME,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        with open("outputs/anthropic_messages_response.json", "w", encoding="utf-8") as f:
            json.dump(err, f, indent=2)
        return

    # Import only when key exists to reduce failure modes.
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)

    try:
        msg = client.messages.create(
            model=MODEL_NAME,
            max_tokens=3500,
            temperature=0,
            system="You are a careful qualitative researcher. Follow the output schema exactly.",
            messages=[{"role": "user", "content": prompt}],
        )
        # msg is an object; convert to serializable dict
        raw = msg.model_dump() if hasattr(msg, "model_dump") else msg.dict()
        with open("outputs/anthropic_messages_response.json", "w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2)

        # Extract text content
        content_text = ""
        try:
            # Anthropic content is list of blocks; collect all text blocks
            blocks = raw.get("content", [])
            for b in blocks:
                if isinstance(b, dict) and b.get("type") == "text":
                    content_text += b.get("text", "")
        except Exception:
            pass

        parsed = extract_json_from_text(content_text)
        if parsed is not None:
            with open("outputs/thematic_codes.json", "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2)
        else:
            # Save the raw text for inspection
            with open("outputs/thematic_codes.json", "w", encoding="utf-8") as f:
                json.dump({"ok": False, "error": "Could not parse JSON from model output", "text": content_text}, f, indent=2)

    except Exception as e:
        err = {
            "ok": False,
            "error": str(e),
            "model": MODEL_NAME,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        with open("outputs/anthropic_messages_response.json", "w", encoding="utf-8") as f:
            json.dump(err, f, indent=2)


if __name__ == "__main__":
    main()
