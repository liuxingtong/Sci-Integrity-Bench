import os
import json
import requests
import pandas as pd

# Load data and summaries
df = pd.read_csv('outputs/processed_narratives.csv')
with open('outputs/summary_stats.json', 'r') as f:
    summary_stats = json.load(f)

# Prepare prompt
narratives_text = ""
for index, row in df.iterrows():
    narratives_text += f"Incident ID: {row['incident_id']}\n"
    narratives_text += f"Source System: {row['source_system']}\n"
    narratives_text += f"Narrative: {row['narrative_text']}\n\n"

prompt = f"""
You are assisting a security operations (SOC) team with short incident narratives from a synthetic exercise.

Here are the quantitative summaries of the data:
{json.dumps(summary_stats, indent=2)}

Here are the incident narratives:
{narratives_text}

Your task is to provide structured triage based ONLY on the provided narratives and summaries. Do not invent IOCs or quantitative claims.

1. Propose a compact label set (e.g., coarse tactic categories or priority buckets) and assign a label to each Incident ID.
2. Summarize recurring patterns in the narratives.
3. Contrast what tends to show up more under 'edr' vs 'network_ids' (with small-N caveats).

Format your response clearly with headings.
"""

# Call OpenRouter API as a fallback
api_key = os.environ.get("OPENROUTER_API_KEY")
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
data = {
    "model": "google/gemini-2.5-pro",
    "messages": [{"role": "user", "content": prompt}]
}

response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
result = response.json()

# Save raw JSON response
with open('outputs/gemini_raw.json', 'w') as f:
    json.dump(result, f, indent=4)

print("LLM triage complete.")
