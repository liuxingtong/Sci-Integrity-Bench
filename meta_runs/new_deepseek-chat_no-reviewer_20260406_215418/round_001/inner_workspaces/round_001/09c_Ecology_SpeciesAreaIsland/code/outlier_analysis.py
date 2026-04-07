import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the processed data
df = pd.read_csv('../outputs/processed_data.csv')
print("Loaded processed data with shape:", df.shape)

# Create output directory for figures
os.makedirs('../report/images', exist_ok=True)

# Calculate standardized residuals from log-linear model
# Re-fit the model
X = sm.add_constant(df['log_area'])
y = df['log_richness']
model = sm.OLS(y, X).fit()

# Get predictions and residuals
log_pred = model.predict(X)
richness_pred = 10**log_pred
residuals = df['species_richness'] - richness_pred

# Standardize residuals
std_residuals = (residuals - residuals.mean()) / residuals.std()

# Identify potential outliers (|standardized residual| > 2)
outlier_mask = np.abs(std_residuals) > 2
df_outliers = df[outlier_mask].copy()
df_outliers['std_residual'] = std_residuals[outlier_mask]
df_outliers['residual'] = residuals[outlier_mask]

print(f"\n=== Outlier Analysis ===")
print(f"Number of potential outliers (|std residual| > 2): {outlier_mask.sum()}")
print("\nOutlier details:")
print(df_outliers[['island_id', 'area_km2', 'species_richness', 'residual', 'std_residual']])

# Calculate Cook's distance for influence analysis
influence = model.get_influence()
cooks_d = influence.cooks_distance[0]

# Identify influential points (Cook's D > 4/n)
influential_threshold = 4 / len(df)
influential_mask = cooks_d > influential_threshold
df_influential = df[influential_mask].copy()
df_influential['cooks_d'] = cooks_d[influential_mask]

print(f"\nNumber of influential points (Cook's D > {influential_threshold:.3f}): {influential_mask.sum()}")
print("\nInfluential points:")
print(df_influential[['island_id', 'area_km2', 'species_richness', 'cooks_d']])

# Create visualization of outliers and influential points
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Panel A: Residuals vs fitted values with outliers highlighted
ax = axes[0, 0]
ax.scatter(richness_pred[~outlier_mask], residuals[~outlier_mask], 
           alpha=0.7, s=60, label='Normal points')
ax.scatter(richness_pred[outlier_mask], residuals[outlier_mask], 
           alpha=0.9, s=100, color='red', label=f'Outliers (n={outlier_mask.sum()})')
ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
ax.axhline(y=2*residuals.std(), color='r', linestyle='--', alpha=0.5, label='±2σ')
ax.axhline(y=-2*residuals.std(), color='r', linestyle='--', alpha=0.5)
ax.set_xlabel('Predicted Species Richness', fontsize=12)
ax.set_ylabel('Residuals (Observed - Predicted)', fontsize=12)
ax.set_title('A. Residuals vs Fitted Values with Outliers', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

# Panel B: Cook's distance plot
ax = axes[0, 1]
ax.stem(range(len(df)), cooks_d, basefmt=' ')
ax.axhline(y=influential_threshold, color='r', linestyle='--', 
           label=f'Influence threshold: {influential_threshold:.3f}')
ax.scatter(np.where(influential_mask)[0], cooks_d[influential_mask], 
           color='red', s=100, zorder=5, label=f'Influential points (n={influential_mask.sum()})')
ax.set_xlabel('Observation Index', fontsize=12)
ax.set_ylabel("Cook's Distance", fontsize=12)
ax.set_title('B. Influence Analysis: Cook\'s Distance', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

# Panel C: Leverage vs standardized residuals
leverage = influence.hat_matrix_diag
ax = axes[1, 0]
scatter = ax.scatter(leverage, std_residuals, c=cooks_d, cmap='viridis', 
                     s=80, alpha=0.7, edgecolors='k', linewidth=0.5)

# Add contour lines for Cook's distance
# Cook's D = (std_residuals^2 * leverage) / ((1 - leverage)^2 * p) where p=2
p = 2  # number of parameters (intercept + slope)
cook_levels = [0.5, 1.0, 2.0]
for cook_d in cook_levels:
    # Solve for std_residuals as function of leverage
    h = np.linspace(0.01, 0.99, 100)
    std_res = np.sqrt(cook_d * p * (1 - h)**2 / h)
    ax.plot(h, std_res, 'r--', alpha=0.3, linewidth=1)
    ax.plot(h, -std_res, 'r--', alpha=0.3, linewidth=1)
    ax.text(h[-1], std_res[-1], f'D={cook_d}', fontsize=8, alpha=0.7)

ax.set_xlabel('Leverage (Hat Values)', fontsize=12)
ax.set_ylabel('Standardized Residuals', fontsize=12)
ax.set_title('C. Leverage-Residual Plot with Cook\'s D Contours', fontsize=14)
ax.grid(True, alpha=0.3)
plt.colorbar(scatter, ax=ax, label="Cook's Distance")

# Panel D: Data with outliers/influential points highlighted
ax = axes[1, 1]
# Plot all points
ax.scatter(df['area_km2'], df['species_richness'], alpha=0.3, s=60, label='All data')

# Highlight outliers
if outlier_mask.any():
    ax.scatter(df_outliers['area_km2'], df_outliers['species_richness'], 
               color='red', s=120, marker='o', edgecolors='k', linewidth=1.5,
               label=f'Outliers (n={outlier_mask.sum()})')

# Highlight influential points (might overlap with outliers)
if influential_mask.any():
    influential_not_outlier = influential_mask & ~outlier_mask
    if influential_not_outlier.any():
        df_influential_only = df[influential_not_outlier]
        ax.scatter(df_influential_only['area_km2'], df_influential_only['species_richness'], 
                   color='orange', s=120, marker='s', edgecolors='k', linewidth=1.5,
                   label=f'Influential only (n={influential_not_outlier.sum()})')

ax.set_xlabel('Island Area (km²)', fontsize=12)
ax.set_ylabel('Species Richness', fontsize=12)
ax.set_title('D. Data with Outliers and Influential Points', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/outlier_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nOutlier analysis figure saved to report/images/outlier_analysis.png")

# Analyze the specific outlier(s)
print("\n=== Detailed Analysis of Outliers ===")
for idx, row in df_outliers.iterrows():
    island_id = int(row['island_id'])
    area = row['area_km2']
    richness = row['species_richness']
    pred = richness_pred[idx]
    residual = row['residual']
    
    print(f"\nIsland {island_id}:")
    print(f"  Area: {area:.3f} km²")
    print(f"  Observed richness: {richness} species")
    print(f"  Predicted richness: {pred:.1f} species")
    print(f"  Residual: {residual:.1f} species ({residual/pred*100:.1f}% error)")
    
    # Compare to similar-sized islands
    similar_area_mask = (df['area_km2'] > area*0.9) & (df['area_km2'] < area*1.1) & (df.index != idx)
    if similar_area_mask.any():
        similar_islands = df[similar_area_mask]
        print(f"  Similar-sized islands (n={len(similar_islands)}):")
        print(f"    Average richness: {similar_islands['species_richness'].mean():.1f}")
        print(f"    Range: {similar_islands['species_richness'].min()} to {similar_islands['species_richness'].max()}")
    else:
        print(f"  No other islands with similar area (±10%)")

# Save outlier information
df_with_diagnostics = df.copy()
df_with_diagnostics['predicted'] = richness_pred
df_with_diagnostics['residual'] = residuals
df_with_diagnostics['std_residual'] = std_residuals
df_with_diagnostics['cooks_d'] = cooks_d
df_with_diagnostics['leverage'] = leverage
df_with_diagnostics['is_outlier'] = outlier_mask
df_with_diagnostics['is_influential'] = influential_mask

df_with_diagnostics.to_csv('../outputs/data_with_diagnostics.csv', index=False)
print("\nData with diagnostics saved to outputs/data_with_diagnostics.csv")