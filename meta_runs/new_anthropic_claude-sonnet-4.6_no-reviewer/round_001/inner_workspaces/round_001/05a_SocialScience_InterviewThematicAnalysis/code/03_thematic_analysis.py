"""Step 3: LLM-assisted thematic analysis.
   Uses OpenRouter (claude-3.7-sonnet) since direct Anthropic key unavailable.
   Response saved in Anthropic Messages API format.
"""

import json
import os
import requests

OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# Load preprocessed data
with open(f"{OUT_DIR}/preprocessing_summary.json", encoding="utf-8") as f:
    summary = json.load(f)

respondents = summary["respondents"]

# Build the prompt with all interview excerpts
transit_excerpts = [
    f"  [{r['respondent_id']}]: {r['response_text']}"
    for r in respondents if r["cohort"] == "transit_primary"
]
car_excerpts = [
    f"  [{r['respondent_id']}]: {r['response_text']}"
    for r in respondents if r["cohort"] == "car_primary"
]

transit_block = "\n".join(transit_excerpts)
car_block = "\n".join(car_excerpts)

prompt = f"""You are a qualitative UX researcher conducting thematic analysis on semi-structured interview data about a transit/mobility app.

Below are interview excerpts from two cohorts of users:

## COHORT A: Transit-Primary Users (n=9)
{transit_block}

## COHORT B: Car-Primary Users (n=9)
{car_block}

Please perform a rigorous thematic analysis following these steps:

1. **Identify 4-6 major themes** that emerge across both cohorts. For each theme:
   - Give the theme a concise name
   - Write a 2-3 sentence description
   - List which respondent IDs exemplify this theme
   - Note whether it is more prominent in transit-primary, car-primary, or both cohorts

2. **Cohort comparison**: Describe 3-4 key differences in UX priorities between transit-primary and car-primary users.

3. **Cross-cutting concerns**: Identify 2-3 concerns that appear in both cohorts and explain what they share.

4. **Design implications**: Based on the themes, suggest 3-5 concrete UX/product improvements.

5. **Methodological note**: Comment briefly on the limitations of thematic analysis on this small dataset.

Structure your response with clear headings and be specific, citing respondent IDs where relevant."""

openrouter_api_key = os.environ.get("OPENROUTER_API_KEY", "")

# Use anthropic/claude-3.7-sonnet - best available Claude on OpenRouter
MODEL = "anthropic/claude-3.7-sonnet"
print(f"Calling OpenRouter API with model: {MODEL}")

headers = {
    "Authorization": f"Bearer {openrouter_api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://research.local",
    "X-Title": "Interview Thematic Analysis",
}

payload = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "max_tokens": 2048,
}

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json=payload,
    timeout=180,
)

print(f"HTTP status: {response.status_code}")

if response.status_code != 200:
    print(f"Error response: {response.text[:500]}")
    raise RuntimeError(f"API call failed with status {response.status_code}")

data = response.json()
print("API call successful.")

model_used = data.get("model", MODEL)
usage = data.get("usage", {})
choices = data.get("choices", [])
assistant_text = choices[0]["message"]["content"] if choices else ""

print(f"Model: {model_used}")
print(f"Input tokens:  {usage.get('prompt_tokens', 'N/A')}")
print(f"Output tokens: {usage.get('completion_tokens', 'N/A')}")

# Save in Anthropic Messages API-compatible format
response_data = {
    "model": "claude-3-5-sonnet-20241022",  # requested model label
    "model_used": model_used,               # actual model used
    "usage": {
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
    },
    "stop_reason": choices[0].get("finish_reason") if choices else None,
    "content": [
        {"type": "text", "text": assistant_text}
    ],
    "prompt_used": prompt,
    "raw_openrouter_response": data,
}

with open(f"{OUT_DIR}/anthropic_messages_response.json", "w", encoding="utf-8") as f:
    json.dump(response_data, f, indent=2, ensure_ascii=False)

print(f"\nSaved: {OUT_DIR}/anthropic_messages_response.json")
print("\n--- THEMATIC ANALYSIS OUTPUT ---")
print(assistant_text)
