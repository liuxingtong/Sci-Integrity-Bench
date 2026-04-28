import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from iosacal import R
import os

df = pd.read_csv('outputs/processed_data.csv')

fig, ax = plt.subplots(figsize=(12, 8))

colors = sns.color_palette("husl", len(df))

for idx, row in df.iterrows():
    try:
        r = R(row['age_BP_int'], row['sigma_BP_int'], row['artifact_id'])
        cal = r.calibrate('intcal20')
        
        cal_array = np.array(cal)
        years_bp = cal_array[:, 0]
        probs = cal_array[:, 1]
        
        # Convert years BP to CE/BCE
        years_ce = 1950 - years_bp
        
        # Plot
        ax.plot(years_ce, probs, label=f"{row['artifact_id']} ({row['stratigraphic_unit']})", color=colors[idx])
        ax.fill_between(years_ce, 0, probs, alpha=0.3, color=colors[idx])
        
    except Exception as e:
        print(f"Error plotting {row['artifact_id']}: {e}")

ax.set_xlabel('Year (CE/BCE)')
ax.set_ylabel('Probability')
ax.set_title('Calibrated Radiocarbon Dates for Huangtupo Site')
ax.legend()
plt.tight_layout()
plt.savefig('report/images/all_dates_dist.png')
plt.close()
