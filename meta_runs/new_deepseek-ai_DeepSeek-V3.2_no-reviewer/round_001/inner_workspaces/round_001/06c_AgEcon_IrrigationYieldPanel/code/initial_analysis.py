import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read the data
data_path = '../data/field_year_panel.csv'
df = pd.read_csv(data_path)

print("=== AGRICULTURAL ECONOMICS: IRRIGATION PROGRAM ANALYSIS ===")
print(f"Dataset contains {len(df)} plot-year observations")
print()

# 1. Correlation analysis
print("1. CORRELATION ANALYSIS")
corr_matrix = df.drop('plot_id', axis=1).corr()
print("Correlation matrix:")
print(corr_matrix.round(3))
print()

# 2. Visualize relationships
print("2. CREATING VISUALIZATIONS...")

# Create figure with subplots
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Agricultural Field-Year Panel: Variable Relationships', fontsize=16)

# Yield vs Irrigation
axes[0, 0].scatter(df['irrigation_m3'], df['yield_t_ha'], alpha=0.7)
axes[0, 0].set_xlabel('Irrigation (m³)')
axes[0, 0].set_ylabel('Yield (t/ha)')
axes[0, 0].set_title('Yield vs Irrigation')

# Yield vs Fertilizer
axes[0, 1].scatter(df['fertilizer_kg'], df['yield_t_ha'], alpha=0.7)
axes[0, 1].set_xlabel('Fertilizer (kg)')
axes[0, 1].set_ylabel('Yield (t/ha)')
axes[0, 1].set_title('Yield vs Fertilizer')

# Yield vs Rainfall
axes[0, 2].scatter(df['rainfall_mm'], df['yield_t_ha'], alpha=0.7)
axes[0, 2].set_xlabel('Rainfall (mm)')
axes[0, 2].set_ylabel('Yield (t/ha)')
axes[0, 2].set_title('Yield vs Rainfall')

# Irrigation vs Groundwater quota enforcement
axes[1, 0].scatter(df['groundwater_quota_enforcement'], df['irrigation_m3'], alpha=0.7)
axes[1, 0].set_xlabel('Groundwater Quota Enforcement')
axes[1, 0].set_ylabel('Irrigation (m³)')
axes[1, 0].set_title('Irrigation vs Quota Enforcement')

# Distribution of yields
axes[1, 1].hist(df['yield_t_ha'], bins=15, edgecolor='black', alpha=0.7)
axes[1, 1].set_xlabel('Yield (t/ha)')
axes[1, 1].set_ylabel('Frequency')
axes[1, 1].set_title('Distribution of Yields')

# Distribution of groundwater quota enforcement
axes[1, 2].hist(df['groundwater_quota_enforcement'], bins=15, edgecolor='black', alpha=0.7)
axes[1, 2].set_xlabel('Groundwater Quota Enforcement')
axes[1, 2].set_ylabel('Frequency')
axes[1, 2].set_title('Distribution of Quota Enforcement')

plt.tight_layout()
plt.savefig('../report/images/initial_relationships.png', dpi=300, bbox_inches='tight')
print("Saved: ../report/images/initial_relationships.png")

# 3. Heatmap of correlations
plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f', 
            square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
plt.title('Correlation Matrix of Agricultural Variables')
plt.tight_layout()
plt.savefig('../report/images/correlation_heatmap.png', dpi=300, bbox_inches='tight')
print("Saved: ../report/images/correlation_heatmap.png")

# 4. Preliminary regression analysis
print("\n3. PRELIMINARY REGRESSION ANALYSIS")
print("Model: yield = β0 + β1*irrigation + β2*fertilizer + β3*rainfall + β4*quota_enforcement")

# Prepare data for regression
X = df[['irrigation_m3', 'fertilizer_kg', 'rainfall_mm', 'groundwater_quota_enforcement']]
X = sm.add_constant(X)  # Add constant term
Y = df['yield_t_ha']

# Fit OLS model
model = sm.OLS(Y, X).fit()
print(model.summary())

# Save regression results
with open('../outputs/preliminary_regression.txt', 'w') as f:
    f.write(str(model.summary()))

print("\n4. INTERACTION EFFECTS ANALYSIS")
# Check interaction between irrigation and quota enforcement
print("Testing interaction: irrigation × quota_enforcement")
df['irrigation_x_quota'] = df['irrigation_m3'] * df['groundwater_quota_enforcement']

X_interaction = df[['irrigation_m3', 'fertilizer_kg', 'rainfall_mm', 
                    'groundwater_quota_enforcement', 'irrigation_x_quota']]
X_interaction = sm.add_constant(X_interaction)
model_interaction = sm.OLS(Y, X_interaction).fit()

print("\nInteraction model results:")
print(model_interaction.summary().tables[1])

# Save interaction model results
with open('../outputs/interaction_regression.txt', 'w') as f:
    f.write(str(model_interaction.summary()))

# 5. Create irrigation program effectiveness visualization
print("\n5. IRRIGATION PROGRAM EFFECTIVENESS ANALYSIS")
# Create categories based on groundwater quota enforcement
quota_bins = pd.qcut(df['groundwater_quota_enforcement'], q=3, labels=['Low', 'Medium', 'High'])
df['quota_category'] = quota_bins

# Calculate average yields by quota enforcement level
quota_summary = df.groupby('quota_category').agg({
    'yield_t_ha': 'mean',
    'irrigation_m3': 'mean',
    'fertilizer_kg': 'mean',
    'rainfall_mm': 'mean',
    'groundwater_quota_enforcement': 'mean'
}).round(3)

print("\nSummary by Groundwater Quota Enforcement Level:")
print(quota_summary)

# Save quota summary
quota_summary.to_csv('../outputs/quota_enforcement_summary.csv')

# Visualize yield by quota enforcement category
plt.figure(figsize=(10, 6))
sns.boxplot(x='quota_category', y='yield_t_ha', data=df)
plt.xlabel('Groundwater Quota Enforcement Level')
plt.ylabel('Yield (t/ha)')
plt.title('Crop Yield by Groundwater Quota Enforcement Level')
plt.tight_layout()
plt.savefig('../report/images/yield_by_quota_level.png', dpi=300, bbox_inches='tight')
print("Saved: ../report/images/yield_by_quota_level.png")

# 6. Marginal effects visualization
print("\n6. MARGINAL EFFECTS VISUALIZATION")
# Create grid for marginal effects
irrigation_range = np.linspace(df['irrigation_m3'].min(), df['irrigation_m3'].max(), 50)
quota_low = df['groundwater_quota_enforcement'].quantile(0.25)
quota_med = df['groundwater_quota_enforcement'].median()
quota_high = df['groundwater_quota_enforcement'].quantile(0.75)

# Use median values for other variables
median_fertilizer = df['fertilizer_kg'].median()
median_rainfall = df['rainfall_mm'].median()

# Predict yields for different quota levels
predictions = []
for quota_val, label in [(quota_low, 'Low'), (quota_med, 'Medium'), (quota_high, 'High')]:
    X_pred = pd.DataFrame({
        'const': 1,
        'irrigation_m3': irrigation_range,
        'fertilizer_kg': median_fertilizer,
        'rainfall_mm': median_rainfall,
        'groundwater_quota_enforcement': quota_val,
        'irrigation_x_quota': irrigation_range * quota_val
    })
    y_pred = model_interaction.predict(X_pred)
    predictions.append((label, irrigation_range, y_pred))

# Plot marginal effects
plt.figure(figsize=(10, 6))
for label, x_vals, y_vals in predictions:
    plt.plot(x_vals, y_vals, label=f'Quota Enforcement: {label}', linewidth=2.5)

plt.xlabel('Irrigation (m³)')
plt.ylabel('Predicted Yield (t/ha)')
plt.title('Marginal Effect of Irrigation on Yield at Different Quota Enforcement Levels')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/marginal_effects_irrigation.png', dpi=300, bbox_inches='tight')
print("Saved: ../report/images/marginal_effects_irrigation.png")

print("\n=== ANALYSIS COMPLETE ===")
print("All outputs saved to outputs/ and report/images/ directories.")