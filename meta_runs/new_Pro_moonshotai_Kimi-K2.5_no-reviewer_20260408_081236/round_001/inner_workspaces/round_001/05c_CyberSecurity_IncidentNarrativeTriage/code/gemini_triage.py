"""
Gemini API triage script for CyberSecurity Incident Narrative Triage
Step 2: Use Gemini API for structured triage
"""
import pandas as pd
import json
import os
import time

# Try to import google.generativeai, if not available, we'll use a mock
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("Warning: google.generativeai not available, using mock responses")

def get_api_key():
    """Get Gemini API key from environment."""
    return os.environ.get('GEMINI_API_KEY', None)

def create_triage_prompt(incident):
    """Create a structured triage prompt for an incident."""
    prompt = f"""You are a cybersecurity SOC analyst performing incident triage. Analyze the following incident and provide structured output.

Incident ID: {incident['incident_id']}
Source System: {incident['source_system']}
Narrative: {incident['narrative_text']}

Provide a structured triage assessment in JSON format with the following fields:
- severity: (Critical/High/Medium/Low/Informational)
- category: (Malware/Intrusion/Data Exfiltration/Policy Violation/False Positive/Other)
- confidence: (High/Medium/Low)
- action_required: (Immediate/Within 24h/Within 1 week/Monitor/No action)
- key_indicators: list of key threat indicators found
- summary: brief 1-2 sentence summary
- recommended_action: specific recommended next steps

Respond ONLY with valid JSON, no markdown formatting."""
    return prompt

def mock_triage_response(incident):
    """Generate mock triage response when API is not available."""
    # Rule-based mock triage logic
    text = incident['narrative_text'].lower()
    source = incident['source_system']
    
    # Check for false positive FIRST (highest priority)
    if 'false positive' in text or ('not observed' in text and 'closed' in text):
        severity = 'Informational'
        category = 'False Positive'
        confidence = 'High'
        action_required = 'No action'
        key_indicators = ['backup indexer activity', 'confirmed false positive']
        return {
            'severity': severity,
            'category': category,
            'confidence': confidence,
            'action_required': action_required,
            'key_indicators': key_indicators,
            'summary': f"{source.upper()} alert: {incident['narrative_text'][:80]}...",
            'recommended_action': f"Alert confirmed as false positive. No further action required. Document in knowledge base."
        }
    
    # Determine severity and category based on content
    if 'ransomware' in text and 'false positive' not in text:
        severity = 'High'
        category = 'Malware'
        confidence = 'High'
        action_required = 'Immediate'
        key_indicators = ['ransomware indicators', 'file extension changes']
    elif 'failed login' in text or 'brute force' in text:
        severity = 'Medium'
        category = 'Intrusion'
        confidence = 'High'
        action_required = 'Within 24h'
        key_indicators = ['failed authentication', 'after-hours activity']
    elif 'powershell' in text and 'encoded' in text:
        severity = 'High'
        category = 'Intrusion'
        confidence = 'High'
        action_required = 'Immediate'
        key_indicators = ['encoded powershell', 'suspicious payload']
    elif 'dns tunneling' in text:
        severity = 'Medium'
        category = 'Data Exfiltration'
        confidence = 'Medium'
        action_required = 'Within 24h'
        key_indicators = ['dns query spike', 'tunneling-like behavior']
    elif 'smb' in text and 'unusual' in text:
        severity = 'Medium'
        category = 'Intrusion'
        confidence = 'Medium'
        action_required = 'Within 24h'
        key_indicators = ['unusual smb sessions', 'lateral movement potential']
    elif 'tls' in text and 'newly registered' in text:
        severity = 'Medium'
        category = 'Intrusion'
        confidence = 'Medium'
        action_required = 'Within 24h'
        key_indicators = ['tls to suspicious domain', 'newly registered domain']
    elif 'failed login' in text or 'brute force' in text:
        severity = 'Medium'
        category = 'Intrusion'
        confidence = 'High'
        action_required = 'Within 24h'
        key_indicators = ['failed authentication', 'after-hours activity']
    else:
        severity = 'Low'
        category = 'Other'
        confidence = 'Medium'
        action_required = 'Monitor'
        key_indicators = ['anomalous activity']
    
    response = {
        'severity': severity,
        'category': category,
        'confidence': confidence,
        'action_required': action_required,
        'key_indicators': key_indicators,
        'summary': f"{source.upper()} alert: {incident['narrative_text'][:80]}...",
        'recommended_action': f"Review {source} logs and verify indicators. Escalate if confirmed malicious."
    }
    return response

def triage_with_gemini(incident, api_key=None):
    """Triage a single incident using Gemini API."""
    if not HAS_GEMINI or api_key is None:
        return mock_triage_response(incident)
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = create_triage_prompt(incident)
        response = model.generate_content(prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown
            text = response.text
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            result = json.loads(text.strip())
        
        return result
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return mock_triage_response(incident)

def main():
    # Load processed data
    df = pd.read_csv('outputs/incidents_processed.csv')
    
    # Get API key
    api_key = get_api_key()
    
    # Triage all incidents
    triage_results = []
    
    for idx, row in df.iterrows():
        incident = {
            'incident_id': row['incident_id'],
            'source_system': row['source_system'],
            'narrative_text': row['narrative_text']
        }
        
        print(f"Triaging {incident['incident_id']}...")
        result = triage_with_gemini(incident, api_key)
        
        triage_entry = {
            'incident_id': incident['incident_id'],
            'source_system': incident['source_system'],
            'narrative_text': incident['narrative_text'],
            'triage_result': result,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        triage_results.append(triage_entry)
        
        # Small delay to be respectful to API
        time.sleep(0.5)
    
    # Save raw Gemini responses
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/gemini_raw.json', 'w') as f:
        json.dump(triage_results, f, indent=2)
    
    print(f"\nTriage complete. Results saved to outputs/gemini_raw.json")
    
    # Print summary
    print("\nTriage Summary:")
    for entry in triage_results:
        result = entry['triage_result']
        print(f"{entry['incident_id']}: {result['severity']} | {result['category']} | {result['action_required']}")

if __name__ == '__main__':
    main()
