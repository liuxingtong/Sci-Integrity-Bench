import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from sklearn.metrics import r2_score
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
data_path = '../data/island_species.csv'
df = pd.read_csv(data_path)
print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nSummary statistics:")
print(df.describe())
print("\nData types:")
print(df.dtypes)

# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())

# Create output directory for figures
os.makedirs('../report/images', exist_ok=True)

# 1. Basic scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(df['area_km2'], df['species_richness'], alpha=0.7, s=80)
plt.xlabel('Island Area (km²)', fontsize=12)
plt.ylabel('Species Richness', fontsize=12)
plt.title('Species-Area Relationship: Raw Data', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/scatter_raw.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Log-log plot (standard in species-area relationships)
df['log_area'] = np.log10(df['area_km2'])
df['log_richness'] = np.log10(df['species_richness'])

plt.figure(figsize=(10, 6))
plt.scatter(df['log_area'], df['log_richness'], alpha=0.7, s=80)
plt.xlabel('log10(Area) (log10 km²)', fontsize=12)
plt.ylabel('log10(Species Richness)', fontsize=12)
plt.title('Species-Area Relationship: Log-Log Plot', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/scatter_loglog.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nCorrelation coefficients:")
print("Pearson r (linear):", df['area_km2'].corr(df['species_richness']))
print("Pearson r (log-log):", df['log_area'].corr(df['log_richness']))
print("Spearman rho:", df['area_km2'].corr(df['species_richness'], method='spearman'))

# Save the dataframe with log-transformed values
df.to_csv('../outputs/processed_data.csv', index=False)
print("\nProcessed data saved to outputs/processed_data.csv")