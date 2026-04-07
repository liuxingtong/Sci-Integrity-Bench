#!/usr/bin/env python3
"""
Generate a sample manifest with multiple samples for simulation.
"""

import pandas as pd
import os

# Create a sample manifest with multiple samples
samples = []
for i in range(1, 11):  # Create 10 samples
    sample_id = f"S{i:03d}"
    cram_path = f"./data/crams/{sample_id}.cram"
    samples.append({
        'sample_id': sample_id,
        'cram_path': cram_path
    })

# Create DataFrame and save
manifest_df = pd.DataFrame(samples)

# Create directory for manifest
os.makedirs('data/crams', exist_ok=True)

# Save the manifest
manifest_df.to_csv('data/sample_manifest_expanded.csv', index=False)

print(f"Generated manifest with {len(samples)} samples:")
print(manifest_df.to_string())
print(f"\nSaved to: data/sample_manifest_expanded.csv")