import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import os

# Create directories if they don't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('data/island_species.csv')

# Log-transform the data
df['log_area'] = np.log(df['area_km2'])
df['log_species'] = np.log(df['species_richness'])

# Perform linear regression on log-transformed data
X = sm.add_constant(df['log_area'])
y = df['log_species']
model = sm.OLS(y, X).fit()

# Save model summary
with open('outputs/model_summary.txt', 'w') as f:
    f.write(model.summary().as_text())

# Extract parameters
log_c, z = model.params
c = np.exp(log_c)

# Plot 1: Log-Log Plot
plt.figure(figsize=(8, 6))
sns.scatterplot(x='log_area', y='log_species', data=df, label='Data')
plt.plot(df['log_area'], model.predict(X), color='red', label=f'Fit: log(S) = {log_c:.2f} + {z:.2f}*log(A)')
plt.xlabel('Log(Area [km²])')
plt.ylabel('Log(Species Richness)')
plt.title('Species-Area Relationship (Log-Log Scale)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('report/images/log_log_plot.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: Original Scale Plot
plt.figure(figsize=(8, 6))
sns.scatterplot(x='area_km2', y='species_richness', data=df, label='Data')

# Generate points for the fitted curve
area_range = np.linspace(df['area_km2'].min(), df['area_km2'].max(), 100)
fitted_species = c * (area_range ** z)

plt.plot(area_range, fitted_species, color='red', label=f'Fit: S = {c:.2f} * A^{z:.2f}')
plt.xlabel('Area (km²)')
plt.ylabel('Species Richness')
plt.title('Species-Area Relationship (Original Scale)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('report/images/original_scale_plot.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 3: Residuals Plot
plt.figure(figsize=(8, 6))
sns.residplot(x=model.predict(X), y=model.resid, lowess=True, line_kws={'color': 'red', 'lw': 1})
plt.xlabel('Fitted Values (Log Scale)')
plt.ylabel('Residuals')
plt.title('Residuals vs Fitted Values')
plt.grid(True, alpha=0.3)
plt.savefig('report/images/residuals_plot.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"Model parameters: c = {c:.4f}, z = {z:.4f}")
print(f"R-squared: {model.rsquared:.4f}")
