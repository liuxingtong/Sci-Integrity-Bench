import os
import json
import pandas as pd
from google import genai
from google.genai import types

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

# Call Gemini API
client = genai.Client()

response = client.models.generate_content(
    model='gemini-1.5-pro',
    contents=prompt,
)

# Save raw JSON response
raw_response = {
    "text": response.text,
    "candidates": [c.model_dump() for c in response.candidates],
    "usage_metadata": response.usage_metadata.model_dump() if response.usage_metadata else None
}

with open('outputs/gemini_raw.json', 'w') as f:
    json.dump(raw_response, f, indent=4)

print("LLM triage complete.")
