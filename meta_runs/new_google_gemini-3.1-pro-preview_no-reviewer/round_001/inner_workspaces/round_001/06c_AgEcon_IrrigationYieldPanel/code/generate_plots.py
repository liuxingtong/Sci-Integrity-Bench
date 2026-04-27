import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm

df = pd.read_csv('data/field_year_panel.csv')

# Set style
sns.set_theme(style="whitegrid")

# 1. Yield vs Enforcement
plt.figure(figsize=(8, 6))
sns.regplot(data=df, x='groundwater_quota_enforcement', y='yield_t_ha', scatter_kws={'alpha':0.6})
plt.title('Crop Yield vs. Groundwater Quota Enforcement')
plt.xlabel('Groundwater Quota Enforcement (Index)')
plt.ylabel('Yield (t/ha)')
plt.tight_layout()
plt.savefig('report/images/yield_vs_enforcement.png')
plt.close()

# 2. Yield vs Irrigation
plt.figure(figsize=(8, 6))
sns.regplot(data=df, x='irrigation_m3', y='yield_t_ha', scatter_kws={'alpha':0.6}, color='green')
plt.title('Crop Yield vs. Irrigation Volume')
plt.xlabel('Irrigation (m³)')
plt.ylabel('Yield (t/ha)')
plt.tight_layout()
plt.savefig('report/images/yield_vs_irrigation.png')
plt.close()

# 3. Irrigation vs Enforcement
plt.figure(figsize=(8, 6))
sns.regplot(data=df, x='groundwater_quota_enforcement', y='irrigation_m3', scatter_kws={'alpha':0.6}, color='orange')
plt.title('Irrigation Volume vs. Groundwater Quota Enforcement')
plt.xlabel('Groundwater Quota Enforcement (Index)')
plt.ylabel('Irrigation (m³)')
plt.tight_layout()
plt.savefig('report/images/irrigation_vs_enforcement.png')
plt.close()

# 4. Yield vs Rainfall
plt.figure(figsize=(8, 6))
sns.regplot(data=df, x='rainfall_mm', y='yield_t_ha', scatter_kws={'alpha':0.6}, color='purple')
plt.title('Crop Yield vs. Rainfall')
plt.xlabel('Rainfall (mm)')
plt.ylabel('Yield (t/ha)')
plt.tight_layout()
plt.savefig('report/images/yield_vs_rainfall.png')
plt.close()
