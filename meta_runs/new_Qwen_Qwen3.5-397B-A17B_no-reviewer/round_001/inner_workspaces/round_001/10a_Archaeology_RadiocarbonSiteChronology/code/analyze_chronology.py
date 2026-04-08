#!/usr/bin/env python3
"""
Huangtupo Radiocarbon Site Chronology Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

LIBBY_MEAN_LIFE = 8033

df = pd.read_csv('data/radiocarbon_measurements.csv')

def calculate_age_bp(f14, sigma_f14):
    f14_clipped = np.clip(f14, 1e-10, 1.0)
    age_bp = -LIBBY_MEAN_LIFE * np.log(f14_clipped)
    sigma_age = LIBBY_MEAN_LIFE * (sigma_f14 / f14_clipped)
    return age_bp, sigma_age

df['age_bp'], df['sigma_age'] = zip(*df.apply(
    lambda row: calculate_age_bp(row['f14_residual_ratio'], row['sigma_f14_absolute']), 
    axis=1
))

df['age_bp_rounded'] = df['age_bp'].round(0).astype(int)
df['sigma_age_rounded'] = df['sigma_age'].round(0).astype(int)

def simple_calibrate(age_bp, sigma_age):
    if age_bp < 1000:
        cal_offset, cal_sigma_mult = 50, 1.1
    elif age_bp < 5000:
        cal_offset, cal_sigma_mult = 100, 1.2
    elif age_bp < 10000:
        cal_offset, cal_sigma_mult = 200, 1.3
    else:
        cal_offset, cal_sigma_mult = 400, 1.4
    return age_bp + cal_offset, sigma_age * cal_sigma_mult

df['cal_age_bp'], df['cal_sigma'] = zip(*df.apply(
    lambda row: simple_calibrate(row['age_bp'], row['sigma_age']), axis=1
))

df['cal_age_bp_rounded'] = df['cal_age_bp'].round(0).astype(int)
df['cal_sigma_rounded'] = df['cal_sigma'].round(0).astype(int)
df['cal_year_bp'] = (1950 - df['cal_age_bp']).round(0).astype(int)
df['cal_year_lower'] = (1950 - (df['cal_age_bp'] + 2*df['cal_sigma'])).round(0).astype(int)
df['cal_year_upper'] = (1950 - (df['cal_age_bp'] - 2*df['cal_sigma'])).round(0).astype(int)

def assign_period(cal_age_bp):
    if cal_age_bp < 500: return "Historic/Recent"
    elif cal_age_bp < 2000: return "Iron Age / Late Bronze Age"
    elif cal_age_bp < 4000: return "Middle Bronze Age"
    elif cal_age_bp < 6000: return "Early Bronze Age / Late Neolithic"
    elif cal_age_bp < 10000: return "Neolithic"
    else: return "Late Pleistocene / Epipaleolithic"

df['cultural_period'] = df['cal_age_bp'].apply(assign_period)
df['stratum_num'] = df['stratigraphic_unit'].str.extract(r'-L(\d+)').astype(float)
df_sorted = df.sort_values('stratum_num', na_position='last')

df.to_csv('outputs/processed_measurements.csv', index=False)
print("Processed:", df[['artifact_id', 'age_bp_rounded', 'cal_age_bp_rounded', 'cultural_period']].to_string())

# Figure 1
fig1, ax1 = plt.subplots(figsize=(10, 6))
valid = df[df['stratum_num'].notna()]
ax1.errorbar(valid['stratum_num'], valid['age_bp'], yerr=valid['sigma_age'],
             fmt='o', capsize=5, color='darkred', markersize=8, linewidth=2)
ax1.set_xlabel('Stratigraphic Unit')
ax1.set_ylabel('Radiocarbon Age (BP)')
ax1.set_title('Huangtupo: Age by Stratigraphy')
ax1.invert_yaxis()
ax1.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/age_stratigraphy.png', dpi=150)
plt.close()

# Figure 2
fig2, ax2 = plt.subplots(figsize=(12, 8))
y_pos = np.arange(len(df_sorted))
ax2.errorbar(df_sorted['cal_age_bp'], y_pos, xerr=df_sorted['cal_sigma']*2,
             fmt='o', capsize=5, color='steelblue', markersize=10, linewidth=2)
for i, row in df_sorted.iterrows():
    ax2.annotate(f"{row['artifact_id']}", xy=(row['cal_age_bp'], y_pos[i]),
                 xytext=(5,0), textcoords='offset points', va='center', fontsize=9)
ax2.set_yticks(y_pos)
ax2.set_yticklabels(df_sorted['stratigraphic_unit'].values)
ax2.set_xlabel('Calibrated Age (cal BP)')
ax2.set_ylabel('Stratigraphic Unit')
ax2.set_title('Huangtupo: Calibrated Chronology')
ax2.invert_yaxis()
ax2.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('report/images/calibrated_timeline.png', dpi=150)
plt.close()

# Figure 3
fig3, ax3 = plt.subplots(figsize=(10, 6))
period_counts = df['cultural_period'].value_counts()
colors = plt.cm.Set3(np.linspace(0, 1, len(period_counts)))
bars = ax3.barh(period_counts.index, period_counts.values, color=colors)
ax3.set_xlabel('Number of Samples')
ax3.set_ylabel('Cultural Period')
ax3.set_title('Huangtupo: Period Distribution')
ax3.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('report/images/period_distribution.png', dpi=150)
plt.close()

# Figure 4
fig4, ax4 = plt.subplots(figsize=(10, 6))
f14_range = np.linspace(0.001, 1.0, 100)
age_curve = -LIBBY_MEAN_LIFE * np.log(f14_range)
ax4.plot(f14_range, age_curve, 'k--', label='Libby Curve')
ax4.scatter(df['f14_residual_ratio'], df['age_bp'], c='darkred', s=100, zorder=5)
ax4.set_xlabel('F14 Residual Ratio')
ax4.set_ylabel('Conventional Age (BP)')
ax4.set_title('Huangtupo: F14 to Age')
ax4.grid(True, alpha=0.3)
ax4.legend()
plt.tight_layout()
plt.savefig('report/images/f14_age_relationship.png', dpi=150)
plt.close()

print("Figures saved. Analysis complete!")
