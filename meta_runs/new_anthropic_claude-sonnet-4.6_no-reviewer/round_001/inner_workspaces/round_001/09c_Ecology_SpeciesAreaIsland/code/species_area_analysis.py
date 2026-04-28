#!/usr/bin/env python3
"""
Species-Area Relationship (SAR) Analysis
Island Biogeography: S = c * A^z
log(S) = log(c) + z * log(A)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
import warnings
warnings.filterwarnings('ignore')

# ── 0. Setup ──────────────────────────────────────────────────────────────────
np.random.seed(42)
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'figure.dpi': 150,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# ── 1. Load Data ──────────────────────────────────────────────────────────────
df = pd.read_csv('data/island_species.csv')
print("Data loaded:")
print(df.head(10))
print(f"\nShape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nDescriptive statistics:")
print(df.describe())

# Identify area and species columns
area_col = [c for c in df.columns if 'area' in c.lower() or 'Area' in c][0]
species_col = [c for c in df.columns if 'species' in c.lower() or 'richness' in c.lower() or 'Species' in c][0]
print(f"\nArea column: {area_col}")
print(f"Species column: {species_col}")

A = df[area_col].values.astype(float)
S = df[species_col].values.astype(float)

# Remove any NaN or non-positive values
mask = (A > 0) & (S > 0) & np.isfinite(A) & np.isfinite(S)
A = A[mask]
S = S[mask]
df_clean = df[mask].copy()
print(f"\nClean data points: {len(A)}")

# ── 2. Log-Log Transformation & OLS Regression ────────────────────────────────
logA = np.log10(A)
logS = np.log10(S)

# OLS linear regression on log-log scale
slope, intercept, r_value, p_value, se = stats.linregress(logA, logS)
z = slope
c = 10**intercept
r2 = r_value**2

print(f"\n=== Power-Law SAR: S = c * A^z ===")
print(f"  z (slope)     = {z:.4f}  (SE={se:.4f})")
print(f"  c (intercept) = {c:.4f}  (10^{intercept:.4f})")
print(f"  R²            = {r2:.4f}")
print(f"  p-value       = {p_value:.4e}")

# Confidence intervals for slope (95%)
t_crit = stats.t.ppf(0.975, df=len(logA)-2)
z_ci_low = z - t_crit * se
z_ci_high = z + t_crit * se
print(f"  95% CI for z  = [{z_ci_low:.4f}, {z_ci_high:.4f}]")

# ── 3. Alternative Models ─────────────────────────────────────────────────────
# 3a. Logarithmic model: S = a + b*log(A)
slope_log, intercept_log, r_log, p_log, se_log = stats.linregress(np.log(A), S)
S_pred_log = intercept_log + slope_log * np.log(A)
r2_log = r2_score(S, S_pred_log)

# 3b. Power law (non-linear least squares)
def power_law(A, c, z):
    return c * A**z

try:
    popt, pcov = curve_fit(power_law, A, S, p0=[1, 0.25], maxfev=10000)
    c_nls, z_nls = popt
    S_pred_nls = power_law(A, c_nls, z_nls)
    r2_nls = r2_score(S, S_pred_nls)
except Exception as e:
    print(f"NLS failed: {e}")
    c_nls, z_nls, r2_nls = c, z, r2
    S_pred_nls = c_nls * A**z_nls

print(f"\n=== Model Comparison ===")
print(f"  Power-law (OLS log-log): z={z:.4f}, c={c:.4f}, R²={r2:.4f}")
print(f"  Power-law (NLS):         z={z_nls:.4f}, c={c_nls:.4f}, R²={r2_nls:.4f}")
print(f"  Logarithmic:             b={slope_log:.4f}, a={intercept_log:.4f}, R²={r2_log:.4f}")

# ── 4. Residual Analysis ──────────────────────────────────────────────────────
logS_pred = intercept + z * logA
residuals = logS - logS_pred

# Shapiro-Wilk test on residuals
shapiro_stat, shapiro_p = stats.shapiro(residuals)
print(f"\nShapiro-Wilk test on residuals: W={shapiro_stat:.4f}, p={shapiro_p:.4f}")

# ── 5. Conservation Scenarios ─────────────────────────────────────────────────
# Predict species loss from habitat reduction
print("\n=== Conservation Implications ===")
print("Predicted species retention when habitat is reduced:")
for pct_retained in [90, 75, 50, 25, 10]:
    frac = pct_retained / 100
    species_retained = frac**z
    species_lost_pct = (1 - species_retained) * 100
    print(f"  {pct_retained:3d}% habitat retained → {species_retained*100:.1f}% species retained "
          f"({species_lost_pct:.1f}% lost)")

# Minimum area to preserve X% of species
print("\nMinimum area fraction to preserve X% of species:")
for pct_species in [90, 80, 70, 50]:
    frac_species = pct_species / 100
    frac_area = frac_species**(1/z)
    print(f"  Preserve {pct_species}% of species → need {frac_area*100:.1f}% of original area")

# ── 6. Save Numerical Results ─────────────────────────────────────────────────
results = {
    'n_islands': len(A),
    'area_min': A.min(), 'area_max': A.max(),
    'species_min': S.min(), 'species_max': S.max(),
    'z_ols': z, 'c_ols': c, 'r2_ols': r2, 'p_value': p_value,
    'z_ci_low': z_ci_low, 'z_ci_high': z_ci_high,
    'z_nls': z_nls, 'c_nls': c_nls, 'r2_nls': r2_nls,
    'r2_log': r2_log,
    'shapiro_p': shapiro_p,
}
import json
with open('outputs/results_summary.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nResults saved to outputs/results_summary.json")

# ── 7. Figures ────────────────────────────────────────────────────────────────

# Figure 1: Main SAR plot (raw + log-log)
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

# Panel A: Raw scale
ax = axes[0]
A_range = np.linspace(A.min(), A.max(), 300)
S_fit = c * A_range**z
ax.scatter(A, S, color='steelblue', edgecolors='white', s=70, alpha=0.85, zorder=3, label='Islands')
ax.plot(A_range, S_fit, 'r-', lw=2.2, label=f'$S = {c:.2f}\\cdot A^{{{z:.3f}}}$\n$R^2={r2:.3f}$')
ax.set_xlabel('Island Area')
ax.set_ylabel('Species Richness')
ax.set_title('A  Species–Area Relationship (Raw Scale)')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# Panel B: Log-log scale
ax = axes[1]
logA_range = np.linspace(logA.min(), logA.max(), 300)
logS_fit = intercept + z * logA_range
ax.scatter(logA, logS, color='steelblue', edgecolors='white', s=70, alpha=0.85, zorder=3, label='Islands')
ax.plot(logA_range, logS_fit, 'r-', lw=2.2,
        label=f'$\\log S = {intercept:.3f} + {z:.3f}\\cdot\\log A$\n$R^2={r2:.3f}$, $p={p_value:.2e}$')
# 95% prediction band
n = len(logA)
logA_mean = logA.mean()
SS_xx = np.sum((logA - logA_mean)**2)
se_pred = se * np.sqrt(1 + 1/n + (logA_range - logA_mean)**2 / SS_xx)
ax.fill_between(logA_range,
                logS_fit - t_crit * se_pred,
                logS_fit + t_crit * se_pred,
                alpha=0.15, color='red', label='95% prediction band')
ax.set_xlabel('log₁₀(Island Area)')
ax.set_ylabel('log₁₀(Species Richness)')
ax.set_title('B  Species–Area Relationship (Log–Log Scale)')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig1_sar_main.png', bbox_inches='tight')
plt.close()
print("Saved fig1_sar_main.png")

# Figure 2: Residual diagnostics
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

# Residuals vs fitted
ax = axes[0]
ax.scatter(logS_pred, residuals, color='steelblue', edgecolors='white', s=60, alpha=0.8)
ax.axhline(0, color='red', lw=1.5, ls='--')
ax.set_xlabel('Fitted log₁₀(S)')
ax.set_ylabel('Residuals')
ax.set_title('A  Residuals vs Fitted')
ax.grid(True, alpha=0.3)

# Q-Q plot
ax = axes[1]
stats.probplot(residuals, dist='norm', plot=ax)
ax.set_title('B  Normal Q–Q Plot of Residuals')
ax.get_lines()[0].set(color='steelblue', markersize=5, alpha=0.8)
ax.get_lines()[1].set(color='red', lw=1.5)
ax.grid(True, alpha=0.3)

# Histogram of residuals
ax = axes[2]
ax.hist(residuals, bins=15, color='steelblue', edgecolor='white', alpha=0.85)
x_norm = np.linspace(residuals.min(), residuals.max(), 200)
y_norm = stats.norm.pdf(x_norm, residuals.mean(), residuals.std()) * len(residuals) * (residuals.max()-residuals.min())/15
ax.plot(x_norm, y_norm, 'r-', lw=2)
ax.set_xlabel('Residuals')
ax.set_ylabel('Count')
ax.set_title(f'C  Residual Distribution\n(Shapiro-Wilk p={shapiro_p:.3f})')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig2_residuals.png', bbox_inches='tight')
plt.close()
print("Saved fig2_residuals.png")

# Figure 3: Model comparison
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

# Panel A: Three models on raw scale
ax = axes[0]
A_range2 = np.linspace(A.min(), A.max(), 300)
S_power = c * A_range2**z
S_power_nls = c_nls * A_range2**z_nls
S_log_model = intercept_log + slope_log * np.log(A_range2)

ax.scatter(A, S, color='steelblue', edgecolors='white', s=70, alpha=0.85, zorder=3, label='Data')
ax.plot(A_range2, S_power, 'r-', lw=2, label=f'Power-law OLS ($R^2$={r2:.3f})')
ax.plot(A_range2, S_power_nls, 'g--', lw=2, label=f'Power-law NLS ($R^2$={r2_nls:.3f})')
ax.plot(A_range2, S_log_model, 'm:', lw=2.5, label=f'Logarithmic ($R^2$={r2_log:.3f})')
ax.set_xlabel('Island Area')
ax.set_ylabel('Species Richness')
ax.set_title('A  Model Comparison (Raw Scale)')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Panel B: Observed vs Predicted
ax = axes[1]
S_pred_power = c * A**z
max_val = max(S.max(), S_pred_power.max())
ax.scatter(S, S_pred_power, color='steelblue', edgecolors='white', s=70, alpha=0.85, label='Power-law OLS')
ax.plot([0, max_val], [0, max_val], 'r--', lw=1.5, label='1:1 line')
ax.set_xlabel('Observed Species Richness')
ax.set_ylabel('Predicted Species Richness')
ax.set_title(f'B  Observed vs Predicted\n($R^2$={r2:.3f})')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig3_model_comparison.png', bbox_inches='tight')
plt.close()
print("Saved fig3_model_comparison.png")

# Figure 4: Conservation implications
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

# Panel A: Species retained vs habitat retained
ax = axes[0]
habitat_pct = np.linspace(1, 100, 300)
species_pct = (habitat_pct/100)**z * 100
ax.plot(habitat_pct, species_pct, 'steelblue', lw=2.5)
ax.plot([0, 100], [0, 100], 'gray', lw=1.5, ls='--', label='1:1 (linear)')
# Mark key points
for hp in [10, 25, 50, 75, 90]:
    sp = (hp/100)**z * 100
    ax.scatter([hp], [sp], color='red', s=80, zorder=5)
    ax.annotate(f'{sp:.0f}%', (hp, sp), textcoords='offset points',
                xytext=(5, 5), fontsize=9, color='red')
ax.set_xlabel('Habitat Retained (%)')
ax.set_ylabel('Species Retained (%)')
ax.set_title(f'A  Species Retention vs Habitat Loss\n(z = {z:.3f})')
ax.legend(fontsize=10)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3)

# Panel B: Area needed to preserve X% of species
ax = axes[1]
species_target = np.linspace(10, 100, 300)
area_needed = (species_target/100)**(1/z) * 100
ax.plot(species_target, area_needed, 'steelblue', lw=2.5)
ax.plot([0, 100], [0, 100], 'gray', lw=1.5, ls='--', label='1:1 (linear)')
for sp_t in [50, 70, 80, 90]:
    an = (sp_t/100)**(1/z) * 100
    ax.scatter([sp_t], [an], color='red', s=80, zorder=5)
    ax.annotate(f'{an:.0f}%', (sp_t, an), textcoords='offset points',
                xytext=(5, -12), fontsize=9, color='red')
ax.set_xlabel('Species Target (%)')
ax.set_ylabel('Area Required (% of original)')
ax.set_title(f'B  Area Required to Meet Species Target\n(z = {z:.3f})')
ax.legend(fontsize=10)
ax.set_xlim(10, 100)
ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig4_conservation.png', bbox_inches='tight')
plt.close()
print("Saved fig4_conservation.png")

# Figure 5: Data distribution overview
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

ax = axes[0]
ax.hist(A, bins=20, color='steelblue', edgecolor='white', alpha=0.85)
ax.set_xlabel('Island Area')
ax.set_ylabel('Count')
ax.set_title('A  Distribution of Island Areas')
ax.grid(True, alpha=0.3)

ax = axes[1]
ax.hist(S, bins=20, color='coral', edgecolor='white', alpha=0.85)
ax.set_xlabel('Species Richness')
ax.set_ylabel('Count')
ax.set_title('B  Distribution of Species Richness')
ax.grid(True, alpha=0.3)

ax = axes[2]
ax.hist(logA, bins=20, color='steelblue', edgecolor='white', alpha=0.85, label='log₁₀(Area)')
ax.hist(logS, bins=20, color='coral', edgecolor='white', alpha=0.6, label='log₁₀(Species)')
ax.set_xlabel('log₁₀ value')
ax.set_ylabel('Count')
ax.set_title('C  Log-Transformed Distributions')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig5_data_overview.png', bbox_inches='tight')
plt.close()
print("Saved fig5_data_overview.png")

print("\n=== Analysis Complete ===")
print(f"All figures saved to report/images/")
print(f"Results saved to outputs/results_summary.json")
