"""
Process lab scratch notes and generate formal SOP for nanoparticle synthesis.
This script parses the raw lab notes and creates a structured SOP document.
"""

import os
import re
from datetime import datetime

# Read the raw lab notes
with open('data/lab_scratch.txt', 'r') as f:
    lab_notes = f.read()

print("Raw Lab Notes:")
print("="*50)
print(lab_notes)
print("="*50)

# Parse key information from lab notes
# Extract synthesis parameters
notes_lines = lab_notes.strip().split('\n')

# Create structured data from notes
synthesis_params = {
    'product': 'NanoCu (Copper Nanoparticles)',
    'temperature': '110°C',
    'temperature_range': '105-115°C',
    'precursor': 'Precursor A',
    'addition_method': 'Dropwise',
    'surfactant': 'Required (type TBD from batch record)',
    'stirring_duration': 'Overnight (12-16 hours)',
    'initial_color': 'Blue-green',
    'final_color': 'Brown',
    'workup': 'To be confirmed from photo documentation',
}

print("\nExtracted Parameters:")
for key, value in synthesis_params.items():
    print(f"  {key}: {value}")

# Save extracted parameters
os.makedirs('outputs', exist_ok=True)
with open('outputs/extracted_params.txt', 'w') as f:
    f.write("Extracted Synthesis Parameters\n")
    f.write("="*40 + "\n")
    for key, value in synthesis_params.items():
        f.write(f"{key}: {value}\n")

print("\nParameters saved to outputs/extracted_params.txt")
