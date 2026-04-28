import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from iosacal import R
import os

df = pd.read_csv('outputs/processed_data.csv')

# We have dates spanning from 48000 BCE to 1000 CE. 
# Plotting them all on one axis makes it hard to see.
# Let's create separate plots for different periods or a multi-panel plot.

# Group by age
# AC-109, AC-110: > 40,000 BP
# AC-111, AC-112: ~ 12,000 BP
# AC-113: ~ 6,400 BP
# AC-108: ~ 3,500 BP
# AC-114: ~ 2,000 BP
# AC-107: ~ 1,000 BP

fig, axes = plt.subplots(3, 1, figsize=(12, 15))

colors = sns.color_palette("husl", len(df))

for idx, row in df.iterrows():
    try:
        r = R(row['age_BP_int'], row['sigma_BP_int'], row['artifact_id'])
        cal = r.calibrate('intcal20')
        
        cal_array = np.array(cal)
        years_bp = cal_array[:, 0]
        probs = cal_array[:, 1]
        years_ce = 1950 - years_bp
        
        if row['age_BP_int'] > 30000:
            ax = axes[2]
        elif row['age_BP_int'] > 10000:
            ax = axes[1]
        else:
            ax = axes[0]
            
        ax.plot(years_ce, probs, label=f"{row['artifact_id']} ({row['stratigraphic_unit']})", color=colors[idx])
        ax.fill_between(years_ce, 0, probs, alpha=0.3, color=colors[idx])
        
    except Exception as e:
        print(f"Error plotting {row['artifact_id']}: {e}")

axes[0].set_title('Holocene Dates (< 10,000 BP)')
axes[0].set_xlabel('Year (CE/BCE)')
axes[0].set_ylabel('Probability')
axes[0].legend()

axes[1].set_title('Terminal Pleistocene Dates (~ 12,000 BP)')
axes[1].set_xlabel('Year (CE/BCE)')
axes[1].set_ylabel('Probability')
axes[1].legend()

axes[2].set_title('Late Pleistocene Dates (> 40,000 BP)')
axes[2].set_xlabel('Year (CE/BCE)')
axes[2].set_ylabel('Probability')
axes[2].legend()

plt.tight_layout()
plt.savefig('report/images/split_dates_dist.png')
plt.close()
