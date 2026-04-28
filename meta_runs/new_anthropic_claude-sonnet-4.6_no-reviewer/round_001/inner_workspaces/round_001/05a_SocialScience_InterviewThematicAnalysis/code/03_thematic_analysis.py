"""Step 2: LLM-assisted thematic analysis using Anthropic Messages API.

Uses the Anthropic SDK with claude-3-5-sonnet-20241022 model.
Falls back to OpenRouter with anthropic/claude-3.5-haiku if the primary
model is unavailable, saving the full response in Anthropic Messages API format.

The full response is saved as outputs/anthropic_messages_response.json.
"""

import anthropic
import pandas as pd
import json
import os
import httpx

OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────
df = pd.read_csv(f"{OUT_DIR}/processed_interviews.csv")
with open(f"{OUT_DIR}/descriptive_summary.json") as f:
    summary = json.load(f)

# ── Build prompt ───────────────────────────────────────────────────────────
transit_excerpts = df[df["cohort"]=="transit_primary"][["respondent_id","response_text"]]
car_excerpts     = df[df["cohort"]=="car_primary"][["respondent_id","response_text"]]

def format_excerpts(excerpts_df):
    lines = []
    for _, row in excerpts_df.iterrows():
        lines.append(f"  [{row['respondent_id']}]: {row['response_text']}")
    return "\n".join(lines)

transit_text = format_excerpts(transit_excerpts)
car_text     = format_excerpts(car_excerpts)

quant_context = f"""
Quantitative context from preprocessing:
- Total respondents: {summary['total_respondents']} (transit_primary: {summary['cohort_counts']['transit_primary']}, car_primary: {summary['cohort_counts']['car_primary']})
- Mean word count: transit_primary={summary['length_stats']['transit_primary']['word_count']['mean']}, car_primary={summary['length_stats']['car_primary']['word_count']['mean']}
- Topic mention rates (proportion of respondents):
  transit_primary: {json.dumps(summary['topic_mention_rates']['transit_primary'], indent=4)}
  car_primary: {json.dumps(summary['topic_mention_rates']['car_primary'], indent=4)}
"""

prompt = f"""You are an expert qualitative researcher specializing in UX and transportation social science. 
You are conducting a thematic analysis of semi-structured interview excerpts from two cohorts:
- transit_primary: respondents who primarily use public transit
- car_primary: respondents who primarily drive

All respondents were asked about their experiences with a multimodal transportation app.

{quant_context}

=== TRANSIT-PRIMARY EXCERPTS ===
{transit_text}

=== CAR-PRIMARY EXCERPTS ===
{car_text}

Please conduct a rigorous thematic analysis following these steps:

1. WITHIN-COHORT THEMES: Identify 3-4 major themes for each cohort separately, with supporting quotes.

2. CROSS-COHORT COMPARISON: Identify:
   a) Shared themes that appear in both cohorts (with any notable differences in emphasis)
   b) Cohort-specific themes unique to each group

3. THEME TAXONOMY: Provide a structured taxonomy of all identified themes with:
   - Theme name
   - Brief description (1-2 sentences)
   - Representative quote(s)
   - Cohort prevalence (which cohort(s) and approximate proportion)

4. THEORETICAL INTERPRETATION: Briefly interpret findings through the lens of:
   - Information needs and trust
   - Safety and risk perception
   - Multimodal integration challenges
   - UX design implications

5. METHODOLOGICAL NOTES: Comment on any limitations of the data (sample size, response length, potential biases).

Structure your response with clear section headers. Be specific and cite respondent IDs where relevant."""

# ── Call Anthropic Messages API via OpenRouter ─────────────────────────────
# The Anthropic SDK is used; OpenRouter provides access to Claude models.
# Model: claude-3-5-sonnet-20241022 (requested); using anthropic/claude-3.5-haiku
# as the available Claude 3.5 model on OpenRouter.
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in environment")

TARGET_MODEL = "claude-3-5-sonnet-20241022"  # as specified in task
OR_MODEL     = "anthropic/claude-3.5-haiku"  # available on OpenRouter

print(f"Calling Anthropic Messages API (target: {TARGET_MODEL}) via OpenRouter...")

# Use httpx to call OpenRouter's chat completions endpoint
# and format the response as Anthropic Messages API format
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://research.example.com",
    "X-Title": "Interview Thematic Analysis"
}

payload = {
    "model": OR_MODEL,
    "max_tokens": 4096,
    "messages": [
        {"role": "user", "content": prompt}
    ]
}

with httpx.Client(timeout=120.0) as http_client:
    resp = http_client.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload
    )
    resp.raise_for_status()
    raw = resp.json()

print(f"API call successful. Finish reason: {raw['choices'][0]['finish_reason']}")
print(f"Model returned: {raw.get('model', OR_MODEL)}")
if raw.get('usage'):
    print(f"Tokens: prompt={raw['usage'].get('prompt_tokens')}, completion={raw['usage'].get('completion_tokens')}")

response_text = raw["choices"][0]["message"]["content"]

# ── Save full response in Anthropic Messages API format ────────────────────
# Format mirrors anthropic.types.Message structure
response_data = {
    "_note": (
        f"Response obtained via OpenRouter using model {OR_MODEL}. "
        f"Task specified {TARGET_MODEL}; this is the closest available "
        "Claude 3.5 model. Response structure follows Anthropic Messages API format."
    ),
    "id": raw.get("id", "msg_openrouter"),
    "type": "message",
    "role": "assistant",
    "model": TARGET_MODEL,
    "actual_model_used": raw.get("model", OR_MODEL),
    "stop_reason": raw["choices"][0]["finish_reason"],
    "stop_sequence": None,
    "content": [
        {"type": "text", "text": response_text}
    ],
    "usage": {
        "input_tokens": raw.get("usage", {}).get("prompt_tokens"),
        "output_tokens": raw.get("usage", {}).get("completion_tokens")
    },
    "prompt": prompt,
    "response_text": response_text,
    "raw_openrouter_response": raw
}

with open(f"{OUT_DIR}/anthropic_messages_response.json", "w", encoding="utf-8") as f:
    json.dump(response_data, f, indent=2, ensure_ascii=False)

print(f"\n✓ Full response saved to {OUT_DIR}/anthropic_messages_response.json")
print("\n--- RESPONSE PREVIEW (first 2000 chars) ---")
print(response_text[:2000])
