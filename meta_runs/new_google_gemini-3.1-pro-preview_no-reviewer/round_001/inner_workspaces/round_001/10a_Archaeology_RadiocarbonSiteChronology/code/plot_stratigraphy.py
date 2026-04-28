import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from iosacal import R
import os

df = pd.read_csv('outputs/processed_data.csv')

trench3 = df[df['stratigraphic_unit'].str.contains('Trench3')].copy()
trench3['layer_num'] = trench3['stratigraphic_unit'].str.extract(r'L(\d+)').astype(int)
trench3 = trench3.sort_values('layer_num', ascending=False) # L6 at bottom, L1 at top

fig, ax = plt.subplots(figsize=(10, 8))

# Plot age vs layer
ax.errorbar(trench3['age_BP_int'], trench3['layer_num'], xerr=trench3['sigma_BP_int'], fmt='o', capsize=5, color='black')

# Add labels
for idx, row in trench3.iterrows():
    ax.text(row['age_BP_int'] + 1000, row['layer_num'], f"{row['artifact_id']} ({row['material']})", va='center')

ax.set_yticks(trench3['layer_num'])
ax.set_yticklabels(trench3['stratigraphic_unit'])
ax.set_xlabel('Conventional Radiocarbon Age (BP)')
ax.set_ylabel('Stratigraphic Unit')
ax.set_title('Trench 3 Stratigraphy vs Radiocarbon Age')
ax.invert_yaxis() # L1 at top

plt.tight_layout()
plt.savefig('report/images/trench3_stratigraphy.png')
plt.close()
