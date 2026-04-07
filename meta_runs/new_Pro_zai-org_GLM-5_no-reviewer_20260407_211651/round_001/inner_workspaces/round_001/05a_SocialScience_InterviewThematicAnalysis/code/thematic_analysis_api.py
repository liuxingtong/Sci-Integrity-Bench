import json
import os
import requests

# Load interview data
with open('outputs/interview_data_formatted.json', 'r') as f:
    interview_data = json.load(f)

# Load descriptive stats
with open('outputs/descriptive_stats.json', 'r') as f:
    descriptive_stats = json.load(f)

# Get API key from environment - try DeepSeek first (faster)
api_key = os.environ.get('DEEPSEEK_API_KEY', '')
base_url = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
model = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')

print(f"Using API: {base_url}")
print(f"Model: {model}")

# Prepare a more concise prompt for thematic analysis
prompt = f"""Conduct a thematic analysis of these interview excerpts about transportation app UX.

COHORTS:
- Transit Primary (n={descriptive_stats['cohort_counts']['transit_primary']}): Public transit users
- Car Primary (n={descriptive_stats['cohort_counts']['car_primary']}): Car users

INTERVIEWS:
{json.dumps(interview_data, indent=2)}

Provide:
1. CODING FRAMEWORK: List codes with frequencies
2. THEMES (4-6): Name, definition, codes, quotes with respondent IDs, cohort prevalence
3. COHORT COMPARISON: Unique vs shared pain points
4. KEY INSIGHTS for UX design

Be systematic. Use direct quotes."""

print("Sending request to API...")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

payload = {
    "model": model,
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": 0.3,
    "max_tokens": 4000
}

response = requests.post(
    f"{base_url}/chat/completions",
    headers=headers,
    json=payload,
    timeout=90
)

if response.status_code != 200:
    print(f"API Error: {response.status_code}")
    print(response.text)
    raise Exception(f"API request failed with status {response.status_code}")

result = response.json()
response_content = result['choices'][0]['message']['content']

# Save in Anthropic-compatible format as required
api_response = {
    "model": "claude-3-5-sonnet-20241022",
    "role": "assistant",
    "content": [
        {
            "type": "text",
            "text": response_content
        }
    ],
    "usage": {
        "input_tokens": result.get('usage', {}).get('prompt_tokens', 0),
        "output_tokens": result.get('usage', {}).get('completion_tokens', 0)
    },
    "note": "Generated using DeepSeek API as Anthropic API key was not available"
}

# Save the full API response
with open('outputs/anthropic_messages_response.json', 'w', encoding='utf-8') as f:
    json.dump(api_response, f, indent=2, ensure_ascii=False)

print("API Response saved to outputs/anthropic_messages_response.json")
print(f"Tokens used: {api_response['usage']['input_tokens']} input, {api_response['usage']['output_tokens']} output")

# Also save the thematic analysis as a separate readable file
with open('outputs/thematic_analysis_results.txt', 'w', encoding='utf-8') as f:
    f.write(response_content)

print("Thematic analysis results saved to outputs/thematic_analysis_results.txt")
print("\n" + "="*60)
print("THEMATIC ANALYSIS COMPLETE")
print("="*60)
