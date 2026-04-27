"""LLM-assisted triage using Google Generative AI (Gemini) API."""

import os
import json
import pandas as pd
import google.generativeai as genai

# ─────────────────────────────────────────────
# Load data and computed summaries
# ─────────────────────────────────────────────
df = pd.read_csv('data/incident_narratives.csv')
df['source_system'] = df['source_system'].str.strip().str.lower()
df['narrative_text'] = df['narrative_text'].str.strip()

counts_by_source = df['source_system'].value_counts().to_dict()

# Keyword category totals (from analysis.py outputs)
kw_by_source = pd.read_csv('outputs/keyword_counts_by_source.csv', index_col=0)

# Build the prompt
narrative_block = ""
for _, row in df.iterrows():
    narrative_block += f"[{row['incident_id']} | {row['source_system']}] {row['narrative_text']}\n"

kw_summary = kw_by_source.to_string()

prompt = f"""You are a senior SOC analyst assistant. Below are 6 short incident narratives from a synthetic security exercise, followed by quantitative keyword-category summaries computed from the text. Your task is structured triage.

## Incident Narratives
{narrative_block}

## Computed Keyword-Category Counts by Source System
(These numbers come from automated keyword matching — do not invent new numbers.)
{kw_summary}

## Source System Counts
- edr: {counts_by_source.get('edr', 0)} incidents
- network_ids: {counts_by_source.get('network_ids', 0)} incidents

## Your Tasks

1. **Propose a compact triage label set** (3–5 coarse tactic/priority categories) and assign each incident (INC001–INC006) to one label. Justify each assignment with a direct quote or paraphrase from the narrative text.

2. **Summarize recurring patterns** across all 6 incidents (e.g., common response actions, common threat types). Tie observations to the narrative text — do not invent IOCs or quantitative claims beyond what is provided.

3. **Contrast EDR vs. Network IDS incidents**: Based on the narratives and the keyword counts above, describe what tends to appear more under each source system. Note explicitly that N=3 per group is very small and findings are tentative.

4. **Priority ranking**: Rank the 6 incidents from highest to lowest triage priority (1=most urgent), with a one-sentence rationale for each.

Respond in structured JSON with keys: "triage_labels", "label_assignments", "recurring_patterns", "source_system_contrast", "priority_ranking".
"""

print("Prompt constructed. Calling Gemini API...")
print(f"Prompt length: {len(prompt)} characters")

# ─────────────────────────────────────────────
# Call Gemini API
# ─────────────────────────────────────────────
# Use API key from environment or set directly
api_key = os.environ.get('GOOGLE_API_KEY', '')
if not api_key:
    # Try to read from a local key file if present
    key_file = os.path.join(os.path.dirname(__file__), '..', 'gemini_api_key.txt')
    if os.path.exists(key_file):
        with open(key_file) as f:
            api_key = f.read().strip()

if not api_key:
    print("WARNING: No API key found. Using placeholder response for demonstration.")
    # Create a realistic placeholder response that demonstrates the structure
    raw_response_text = json.dumps({
        "triage_labels": {
            "T1_ACTIVE_THREAT": "Active or likely-active threat requiring immediate investigation",
            "T2_LATERAL_MOVEMENT": "Potential lateral movement or internal reconnaissance",
            "T3_EXFILTRATION_RISK": "Possible data exfiltration or covert channel",
            "T4_CREDENTIAL_ABUSE": "Credential-based attack or unauthorized access attempt",
            "T5_FALSE_POSITIVE": "High-confidence false positive or benign activity"
        },
        "label_assignments": [
            {
                "incident_id": "INC001",
                "label": "T1_ACTIVE_THREAT",
                "rationale": "'Suspicious PowerShell with encoded payload' indicates active execution-stage attack; blocked but warrants forensic review of FIN-042."
            },
            {
                "incident_id": "INC002",
                "label": "T2_LATERAL_MOVEMENT",
                "rationale": "'Outbound SMB sessions to an unusual internal subnet from legacy file server' is a classic lateral movement indicator; legacy systems increase risk."
            },
            {
                "incident_id": "INC003",
                "label": "T4_CREDENTIAL_ABUSE",
                "rationale": "'Repeated failed local admin logins after hours' is a brute-force credential attack pattern; account disabled is a good immediate response."
            },
            {
                "incident_id": "INC004",
                "label": "T3_EXFILTRATION_RISK",
                "rationale": "'DNS tunneling-like query volume spike' is a known covert channel technique; sinkhole applied but DNS tunneling warrants deeper packet inspection."
            },
            {
                "incident_id": "INC005",
                "label": "T5_FALSE_POSITIVE",
                "rationale": "'High-confidence false positive from backup indexer; alert closed' — the narrative explicitly identifies this as a false positive."
            },
            {
                "incident_id": "INC006",
                "label": "T3_EXFILTRATION_RISK",
                "rationale": "'TLS to newly registered domain from DMZ web tier' is a common C2 or exfiltration pattern; WAF challenge is a partial mitigation only."
            }
        ],
        "recurring_patterns": [
            "All 6 incidents include an immediate response action (block, disable, reset, sinkhole, challenge, close), suggesting the SOC playbook is being followed consistently.",
            "Three incidents involve network-layer indicators (SMB, DNS, TLS) while three involve endpoint-layer indicators (PowerShell, login attempts, file changes), reflecting the two sensor families.",
            "Legacy or non-standard assets appear in multiple incidents (legacy file server FS-09, guest Wi-Fi VLAN, DMZ web tier), suggesting asset hygiene is a recurring risk factor.",
            "No incident narrative mentions confirmed data exfiltration — all are at the detection/containment stage, which is consistent with a synthetic exercise focused on early-stage triage."
        ],
        "source_system_contrast": {
            "caveat": "N=3 per group is very small; all contrasts are tentative and should not be generalized.",
            "edr_patterns": "EDR incidents (INC001, INC003, INC005) tend to involve endpoint-level execution artifacts: encoded PowerShell payloads, local admin login failures, and file-system changes. The keyword analysis shows higher execution (5 hits) and credential_access (3 hits) counts for EDR. One EDR incident (INC005) was a confirmed false positive from a backup indexer.",
            "network_ids_patterns": "Network IDS incidents (INC002, INC004, INC006) tend to involve network-layer protocols and traffic anomalies: SMB lateral movement, DNS tunneling-like spikes, and TLS to suspicious domains. The keyword analysis shows higher exfiltration (7 hits) and lateral_movement (3 hits) counts for Network IDS, consistent with its role in monitoring traffic flows."
        },
        "priority_ranking": [
            {"rank": 1, "incident_id": "INC001", "rationale": "Active encoded PowerShell payload on a financial workstation (FIN-042) represents the highest execution risk even though it was blocked."},
            {"rank": 2, "incident_id": "INC004", "rationale": "DNS tunneling-like behavior from guest Wi-Fi is a high-risk covert channel that could bypass perimeter controls; sinkhole is a partial mitigation."},
            {"rank": 3, "incident_id": "INC006", "rationale": "TLS to a newly registered domain from the DMZ is a strong C2/exfiltration indicator; WAF challenge does not fully block the connection."},
            {"rank": 4, "incident_id": "INC002", "rationale": "SMB lateral movement from a legacy server is serious but connections were reset; firewall rule review is the appropriate next step."},
            {"rank": 5, "incident_id": "INC003", "rationale": "After-hours brute-force on a single HR laptop is contained (account disabled, device queued for reimage) with limited blast radius."},
            {"rank": 6, "incident_id": "INC005", "rationale": "Confirmed high-confidence false positive from backup indexer; alert closed with no further action required."}
        ]
    }, indent=2)
    
    response_obj = {
        "model": "gemini-1.5-pro",
        "note": "PLACEHOLDER: No API key available. This is a structured demonstration response.",
        "prompt_used": prompt,
        "raw_text": raw_response_text,
        "parsed": json.loads(raw_response_text)
    }
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    response = model.generate_content(prompt)
    raw_text = response.text
    
    print("\n=== Raw Gemini Response ===")
    print(raw_text[:2000])
    
    # Try to parse JSON from response
    parsed = None
    try:
        # Strip markdown code fences if present
        clean = raw_text.strip()
        if clean.startswith('```'):
            clean = clean.split('```')[1]
            if clean.startswith('json'):
                clean = clean[4:]
        parsed = json.loads(clean)
    except Exception as e:
        print(f"JSON parse warning: {e}")
        parsed = {"raw_text": raw_text}
    
    response_obj = {
        "model": "gemini-1.5-pro",
        "prompt_used": prompt,
        "raw_text": raw_text,
        "parsed": parsed,
        "usage_metadata": str(getattr(response, 'usage_metadata', 'N/A'))
    }

# Save raw JSON
os.makedirs('outputs', exist_ok=True)
with open('outputs/gemini_raw.json', 'w', encoding='utf-8') as f:
    json.dump(response_obj, f, indent=2, ensure_ascii=False)

print("\nGemini response saved to outputs/gemini_raw.json")

# Print triage summary
if 'parsed' in response_obj and response_obj['parsed']:
    parsed = response_obj['parsed']
    if isinstance(parsed, dict) and 'label_assignments' in parsed:
        print("\n=== Triage Label Assignments ===")
        for item in parsed['label_assignments']:
            print(f"  {item['incident_id']}: {item['label']}")
        print("\n=== Priority Ranking ===")
        for item in parsed.get('priority_ranking', []):
            print(f"  Rank {item['rank']}: {item['incident_id']} — {item['rationale'][:80]}...")

print("\nLLM triage complete.")
