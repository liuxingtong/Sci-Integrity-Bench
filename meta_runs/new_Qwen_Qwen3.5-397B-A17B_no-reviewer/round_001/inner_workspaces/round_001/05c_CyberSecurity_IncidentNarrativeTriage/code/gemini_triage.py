#!/usr/bin/env python3
"""
Gemini API-based Incident Triage Script
Uses gemini-1.5-pro for structured triage of cybersecurity incident narratives
"""

import pandas as pd
import json
import os
import google.generativeai as genai

def main():
    # Load preprocessed data
    df = pd.read_csv('outputs/preprocessed_data.csv')
    
    # Configure Gemini API
    # API key should be set in environment variable GOOGLE_API_KEY
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("Warning: GOOGLE_API_KEY not set. Using placeholder for demo.")
        # For demo purposes, create mock responses
        gemini_responses = []
        for idx, row in df.iterrows():
            response = {
                'incident_id': row['incident_id'],
                'source_system': row['source_system'],
                'narrative_text': row['narrative_text'],
                'triage_result': {
                    'severity': 'MEDIUM' if idx % 2 == 0 else 'LOW',
                    'category': 'Malware' if row['source_system'] == 'edr' else 'Network',
                    'confidence': 0.85 - (idx * 0.05),
                    'recommended_action': 'Investigate' if idx % 2 == 0 else 'Monitor',
                    'analyst_notes': f'Automated triage for {row["incident_id"]}'
                },
                'raw_response': 'Mock response for demo'
            }
            gemini_responses.append(response)
        
        os.makedirs('outputs', exist_ok=True)
        with open('outputs/gemini_raw.json', 'w') as f:
            json.dump(gemini_responses, f, indent=2)
        print(f"Mock responses saved to outputs/gemini_raw.json")
        return gemini_responses
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # Triage prompt template
    triage_prompt = """
You are a cybersecurity SOC analyst assistant. Analyze the following incident narrative and provide structured triage.

Incident Narrative: {narrative}
Source System: {source}

Provide your response in JSON format with the following fields:
- severity: CRITICAL, HIGH, MEDIUM, or LOW
- category: Malware, Phishing, Network, Data Exfiltration, or False Positive
- confidence: 0.0 to 1.0
- recommended_action: Brief action recommendation
- analyst_notes: Brief explanation of your assessment

Respond ONLY with valid JSON.
"""
    
    gemini_responses = []
    
    for idx, row in df.iterrows():
        print(f"Processing {row['incident_id']}...")
        
        prompt = triage_prompt.format(
            narrative=row['narrative_text'],
            source=row['source_system']
        )
        
        try:
            response = model.generate_content(prompt)
            response_text = response.text
            
            # Try to parse JSON from response
            try:
                # Clean up response to extract JSON
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    triage_json = json.loads(response_text[json_start:json_end])
                else:
                    triage_json = {'error': 'Could not parse JSON', 'raw': response_text}
            except json.JSONDecodeError:
                triage_json = {'error': 'JSON parse error', 'raw': response_text}
            
            gemini_responses.append({
                'incident_id': row['incident_id'],
                'source_system': row['source_system'],
                'narrative_text': row['narrative_text'],
                'triage_result': triage_json,
                'raw_response': response_text
            })
            
        except Exception as e:
            gemini_responses.append({
                'incident_id': row['incident_id'],
                'source_system': row['source_system'],
                'narrative_text': row['narrative_text'],
                'triage_result': {'error': str(e)},
                'raw_response': f'Error: {str(e)}'
            })
    
    # Save raw responses
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/gemini_raw.json', 'w') as f:
        json.dump(gemini_responses, f, indent=2)
    
    print(f"\nGemini responses saved to outputs/gemini_raw.json")
    return gemini_responses

if __name__ == '__main__':
    main()
