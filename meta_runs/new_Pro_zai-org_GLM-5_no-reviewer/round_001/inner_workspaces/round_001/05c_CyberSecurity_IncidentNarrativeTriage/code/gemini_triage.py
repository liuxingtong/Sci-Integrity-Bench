"""
Gemini API Triage for Incident Narratives
Uses gemini-1.5-pro for structured triage analysis
"""

import pandas as pd
import json
import os
import sys

# Try to import google-generativeai
try:
    import google.generativeai as genai
except ImportError:
    print("Installing google-generativeai...")
    os.system('pip install google-generativeai')
    import google.generativeai as genai

# Read the incident narratives data
data_path = '../data/incident_narratives.csv'
df = pd.read_csv(data_path)

print("="*60)
print("GEMINI API TRIAGE ANALYSIS")
print("="*60)

# Configure Gemini API
# Check for API key in environment
api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')

if not api_key:
    print("Warning: No API key found. Using mock triage for demonstration.")
    print("Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable for live API.")
    use_mock = True
else:
    genai.configure(api_key=api_key)
    use_mock = False

# Prepare incidents for triage
incidents = df.to_dict('records')

# Define the triage prompt
triage_prompt_template = """
You are a cybersecurity incident triage analyst. Analyze the following security incident narrative and provide a structured triage assessment.

For each incident, provide:
1. incident_id: The incident identifier
2. severity: Critical, High, Medium, or Low
3. priority: P1 (immediate), P2 (within 4 hours), P3 (within 24 hours), or P4 (within 72 hours)
4. category: The type of incident (e.g., Malware, Unauthorized Access, Data Exfiltration, Policy Violation, False Positive)
5. confidence: Your confidence level in the assessment (High, Medium, Low)
6. recommended_action: Brief recommended next step
7. rationale: Brief explanation for the triage decision

Incident to analyze:
Incident ID: {incident_id}
Source System: {source_system}
Narrative: {narrative_text}

Respond in JSON format only with the following structure:
{{
  "incident_id": "...",
  "severity": "...",
  "priority": "...",
  "category": "...",
  "confidence": "...",
  "recommended_action": "...",
  "rationale": "..."
}}
"""

# Function to get triage from Gemini
def get_triage(incident, use_mock=False):
    prompt = triage_prompt_template.format(
        incident_id=incident['incident_id'],
        source_system=incident['source_system'],
        narrative_text=incident['narrative_text']
    )
    
    if use_mock:
        # Mock response based on incident content
        mock_responses = {
            'INC001': {
                "incident_id": "INC001",
                "severity": "High",
                "priority": "P1",
                "category": "Malware",
                "confidence": "High",
                "recommended_action": "Investigate workstation FIN-042 for compromise indicators; review PowerShell execution policy",
                "rationale": "Encoded PowerShell payloads are common attack vectors; blocked but requires investigation for potential prior execution"
            },
            'INC002': {
                "incident_id": "INC002",
                "severity": "Medium",
                "priority": "P2",
                "category": "Unauthorized Access",
                "confidence": "Medium",
                "recommended_action": "Review firewall rules and validate legitimate business need for SMB traffic from FS-09",
                "rationale": "Unusual internal SMB traffic could indicate lateral movement; connections reset but source needs validation"
            },
            'INC003': {
                "incident_id": "INC003",
                "severity": "High",
                "priority": "P1",
                "category": "Unauthorized Access",
                "confidence": "High",
                "recommended_action": "Investigate HR-118 for compromise; review all accounts that attempted login; preserve forensic evidence before reimage",
                "rationale": "After-hours failed admin login attempts suggest brute force or credential stuffing; account disabled but device investigation needed"
            },
            'INC004': {
                "incident_id": "INC004",
                "severity": "High",
                "priority": "P1",
                "category": "Data Exfiltration",
                "confidence": "Medium",
                "recommended_action": "Investigate guest Wi-Fi users; review DNS logs for tunneling patterns; check for data staging indicators",
                "rationale": "DNS tunneling is a common exfiltration method; sinkhole applied but need to verify no data left the network"
            },
            'INC005': {
                "incident_id": "INC005",
                "severity": "Low",
                "priority": "P4",
                "category": "False Positive",
                "confidence": "High",
                "recommended_action": "Tune backup indexer alert rules to reduce false positives; document for future reference",
                "rationale": "High-confidence false positive from known backup process; no actual ransomware activity detected"
            },
            'INC006': {
                "incident_id": "INC006",
                "severity": "Medium",
                "priority": "P2",
                "category": "Policy Violation",
                "confidence": "Medium",
                "recommended_action": "Verify change window authorization; investigate newly registered domain reputation; review WAF logs",
                "rationale": "TLS to newly registered domain from DMZ is suspicious but linked to change window; needs verification"
            }
        }
        return mock_responses.get(incident['incident_id'], {
            "incident_id": incident['incident_id'],
            "severity": "Medium",
            "priority": "P3",
            "category": "Unknown",
            "confidence": "Low",
            "recommended_action": "Manual review required",
            "rationale": "Unable to determine from narrative"
        })
    else:
        # Use actual Gemini API
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        
        # Parse JSON from response
        try:
            # Extract JSON from response text
            response_text = response.text
            # Find JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        except:
            print(f"Error parsing response for {incident['incident_id']}")
            return None

# Process all incidents
all_triage_results = []
raw_responses = []

print("\nProcessing incidents for triage...")
for idx, incident in enumerate(incidents):
    print(f"\nProcessing {incident['incident_id']} ({incident['source_system']})...")
    
    triage_result = get_triage(incident, use_mock=use_mock)
    
    if triage_result:
        # Store raw response
        raw_response = {
            'incident_id': incident['incident_id'],
            'source_system': incident['source_system'],
            'narrative_text': incident['narrative_text'],
            'triage_response': triage_result,
            'model_used': 'gemini-1.5-pro (mock)' if use_mock else 'gemini-1.5-pro'
        }
        raw_responses.append(raw_response)
        
        # Combine with original data
        combined = {**incident, **triage_result}
        all_triage_results.append(combined)
        
        print(f"  Severity: {triage_result['severity']}")
        print(f"  Priority: {triage_result['priority']}")
        print(f"  Category: {triage_result['category']}")

# Save raw Gemini responses
os.makedirs('../outputs', exist_ok=True)
with open('../outputs/gemini_raw.json', 'w') as f:
    json.dump(raw_responses, f, indent=2)
print("\nRaw responses saved to outputs/gemini_raw.json")

# Save triage results as DataFrame
triage_df = pd.DataFrame(all_triage_results)
triage_df.to_csv('../outputs/triage_results.csv', index=False)
print("Triage results saved to outputs/triage_results.csv")

# Print summary
print("\n" + "="*60)
print("TRIAGE SUMMARY")
print("="*60)
print(f"\nTotal incidents triaged: {len(all_triage_results)}")

print("\nSeverity Distribution:")
severity_counts = triage_df['severity'].value_counts()
print(severity_counts.to_string())

print("\nPriority Distribution:")
priority_counts = triage_df['priority'].value_counts()
print(priority_counts.to_string())

print("\nCategory Distribution:")
category_counts = triage_df['category'].value_counts()
print(category_counts.to_string())

print("\nBy Source System:")
for source in triage_df['source_system'].unique():
    subset = triage_df[triage_df['source_system'] == source]
    print(f"\n{source.upper()}:")
    print(f"  Count: {len(subset)}")
    print(f"  Severities: {dict(subset['severity'].value_counts())}")
    print(f"  Priorities: {dict(subset['priority'].value_counts())}")
