"""
Catalyst-X9 Synthesis SOP Generator
Converts raw lab notebook narrative into structured SOP document
"""

import os
import re
from datetime import datetime, timedelta
import json

# Read the lab notebook
with open('data/lab_notebook_x9.txt', 'r') as f:
    notebook_content = f.read()

print("="*60)
print("LAB NOTEBOOK ANALYSIS")
print("="*60)
print(notebook_content)
print("\n")

# Parse the notebook content
def parse_lab_notebook(content):
    """Extract structured data from narrative lab notebook"""
    
    # Extract metadata
    run_id_match = re.search(r'Run ID:\s*([\w-]+)', content)
    vessel_match = re.search(r'Vessel:\s*([^|]+)', content)
    date_match = re.search(r'Date:\s*([\d-]+)', content)
    
    metadata = {
        'run_id': run_id_match.group(1) if run_id_match else 'Unknown',
        'vessel': vessel_match.group(1).strip() if vessel_match else 'Unknown',
        'date': date_match.group(1) if date_match else 'Unknown'
    }
    
    # Extract time-stamped entries
    time_pattern = r'(\d{1,2}:\d{2})\s*[—–-]\s*(.+?)(?=\d{1,2}:\d{2}|$)'
    entries = re.findall(time_pattern, content, re.DOTALL)
    
    steps = []
    for time, description in entries:
        steps.append({
            'time': time.strip(),
            'description': description.strip()
        })
    
    # Extract parameters
    params = {
        'precursor_a_volume': re.search(r'(\d+)\s*mL\s*Precursor A', content),
        'precursor_a_lot': re.search(r'lot\s*([\w-]+)', content),
        'reagent_b_volume': re.search(r'(\d+)\s*mL\s*Reagent B', content),
        'reagent_b_lot': re.search(r'Reagent B.*?lot\s*([\w-]+)', content),
        'stirring_speed': re.search(r'(\d+)\s*rpm', content),
        'target_temp': re.search(r'(\d+)\s*°C', content),
        'ramp_rate': re.search(r'(\d+)\s*°C/min', content),
        'hold_time': re.search(r'for\s*(\d+)\s*minutes', content),
        'condenser_temp': re.search(r'condenser water\s*(\d+)\s*°C', content),
        'centrifuge_speed': re.search(r'(\d+)\s*RPM', content),
        'centrifuge_time': re.search(r'for\s*(\d+)\s*minutes.*centrifuge', content, re.IGNORECASE)
    }
    
    extracted_params = {}
    for key, match in params.items():
        if match:
            extracted_params[key] = match.group(1) if hasattr(match, 'group') else match
    
    return metadata, steps, extracted_params

metadata, steps, params = parse_lab_notebook(notebook_content)

print("="*60)
print("EXTRACTED METADATA")
print("="*60)
for k, v in metadata.items():
    print(f"{k}: {v}")

print("\n" + "="*60)
print("EXTRACTED STEPS")
print("="*60)
for i, step in enumerate(steps, 1):
    print(f"Step {i} [{step['time']}]: {step['description'][:80]}...")

print("\n" + "="*60)
print("EXTRACTED PARAMETERS")
print("="*60)
for k, v in params.items():
    print(f"{k}: {v}")

# Save parsed data
parsed_data = {
    'metadata': metadata,
    'steps': steps,
    'parameters': params
}

os.makedirs('outputs', exist_ok=True)
with open('outputs/parsed_notebook_data.json', 'w') as f:
    json.dump(parsed_data, f, indent=2)

print("\nParsed data saved to outputs/parsed_notebook_data.json")
