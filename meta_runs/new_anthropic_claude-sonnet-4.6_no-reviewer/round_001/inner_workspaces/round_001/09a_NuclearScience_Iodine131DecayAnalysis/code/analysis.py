#!/usr/bin/env python3
"""
Flame Speed vs Chamber Pressure Analysis
Bench combustion experiments: paired chamber-pressure and flame-speed readings
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats
from scipy.optimize import curve_fit
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# 1. Load data
# ─────────────────────────────────────────────
df = pd.read_csv('data/flame_pressure_series.csv')
print("Data shape:", df.shape)
print(df.describe())
print(df.head(10))

# ─────────────────────────────────────────────
# 2. Detect the two regimes (visual inspection shows a jump near index 50)
# ─────────────────────────────────────────────
# Identify the discontinuity: flame speed jumps from ~20 to ~32 around pressure ~82 kPa
diff = df['flame_speed_cm_s'].diff()
print("\nLargest jumps in flame speed:")
print(diff.abs().nlargest(5))

# The jump occurs at index 50 (pressure ~82.4 kPa)
jump_idx = diff.abs().idxmax()
print(f"\nJump detected at index {jump_idx}, pressure = {df.loc[jump_idx, 'pressure_kPa']:.3f} kPa")

# Split into two regimes
df_low  = df.iloc[:jump_idx].copy()   # low-pressure regime
df_high = df.iloc[jump_idx:].copy()   # high-pressure regime

print(f"\nLow-pressure regime:  {df_low['pressure_kPa'].min():.1f} – {df_low['pressure_kPa'].max():.1f} kPa  ({len(df_low)} points)")
print(f"High-pressure regime: {df_high['pressure_kPa'].min():.1f} – {df_high['pressure_kPa'].max():.1f} kPa  ({len(df_high)} points)")

# ─────────────────────────────────────────────
# 3. Fit power-law model:  S_L = a * P^n
#    linearised as  ln(S_L) = ln(a) + n*ln(P)
# ─────────────────────────────────────────────
def power_law(P, a, n):
    return a * np.power(P, n)

def fit_power_law(sub_df, label):
    P = sub_df['pressure_kPa'].values
    S = sub_df['flame_speed_cm_s'].values
    popt, pcov = curve_fit(power_law, P, S, p0=[100, -0.5], maxfev=10000)
    perr = np.sqrt(np.diag(pcov))
    S_pred = power_law(P, *popt)
    ss_res = np.sum((S - S_pred)**2)
    ss_tot = np.sum((S - S.mean())**2)
    r2 = 1 - ss_res / ss_tot
    rmse = np.sqrt(ss_res / len(S))
    print(f"\n[{label}] Power-law fit: S_L = {popt[0]:.4f} * P^{popt[1]:.4f}")
    print(f"  a = {popt[0]:.4f} ± {perr[0]:.4f}")
    print(f"  n = {popt[1]:.4f} ± {perr[1]:.4f}")
    print(f"  R² = {r2:.4f},  RMSE = {rmse:.4f} cm/s")
    return popt, perr, r2, rmse

# Also fit a simple linear model for comparison
def fit_linear(sub_df, label):
    P = sub_df['pressure_kPa'].values
    S = sub_df['flame_speed_cm_s'].values
    slope, intercept, r, p_val, se = stats.linregress(P, S)
    r2 = r**2
    S_pred = slope * P + intercept
    rmse = np.sqrt(np.mean((S - S_pred)**2))
    print(f"\n[{label}] Linear fit: S_L = {slope:.4f}*P + {intercept:.4f}")
    print(f"  slope = {slope:.4f} ± {se:.4f}")
    print(f"  R² = {r2:.4f},  RMSE = {rmse:.4f} cm/s")
    return slope, intercept, r2, rmse

popt_low,  perr_low,  r2_low,  rmse_low  = fit_power_law(df_low,  'Low-P')
popt_high, perr_high, r2_high, rmse_high = fit_power_law(df_high, 'High-P')

slope_low,  intercept_low,  r2_lin_low,  rmse_lin_low  = fit_linear(df_low,  'Low-P  linear')
slope_high, intercept_high, r2_lin_high, rmse_lin_high = fit_linear(df_high, 'High-P linear')

# ─────────────────────────────────────────────
# 4. Save summary statistics
# ─────────────────────────────────────────────
summary = {
    'regime': ['Low-pressure', 'High-pressure'],
    'P_min_kPa': [df_low['pressure_kPa'].min(), df_high['pressure_kPa'].min()],
    'P_max_kPa': [df_low['pressure_kPa'].max(), df_high['pressure_kPa'].max()],
    'n_points': [len(df_low), len(df_high)],
    'S_mean_cm_s': [df_low['flame_speed_cm_s'].mean(), df_high['flame_speed_cm_s'].mean()],
    'S_std_cm_s':  [df_low['flame_speed_cm_s'].std(),  df_high['flame_speed_cm_s'].std()],
    'power_law_a': [popt_low[0], popt_high[0]],
    'power_law_n': [popt_low[1], popt_high[1]],
    'power_law_R2': [r2_low, r2_high],
    'power_law_RMSE': [rmse_low, rmse_high],
    'linear_slope': [slope_low, slope_high],
    'linear_intercept': [intercept_low, intercept_high],
    'linear_R2': [r2_lin_low, r2_lin_high],
    'linear_RMSE': [rmse_lin_low, rmse_lin_high],
}
summary_df = pd.DataFrame(summary)
summary_df.to_csv('outputs/fit_summary.csv', index=False)
print("\nSummary saved to outputs/fit_summary.csv")

# ─────────────────────────────────────────────
# 5. Figures
# ─────────────────────────────────────────────
COLOR_LOW  = '#1f77b4'   # blue
COLOR_HIGH = '#d62728'   # red
COLOR_FIT  = '#2ca02c'   # green

# ── Figure 1: Full dataset overview ──────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
ax.scatter(df_low['pressure_kPa'],  df_low['flame_speed_cm_s'],
           color=COLOR_LOW,  s=30, alpha=0.8, label='Low-pressure regime (38–82 kPa)')
ax.scatter(df_high['pressure_kPa'], df_high['flame_speed_cm_s'],
           color=COLOR_HIGH, s=30, alpha=0.8, label='High-pressure regime (82–98 kPa)')
ax.axvline(df.loc[jump_idx, 'pressure_kPa'], color='gray', ls='--', lw=1.2, label='Regime boundary')
ax.set_xlabel('Chamber Pressure (kPa)', fontsize=12)
ax.set_ylabel('Flame Speed (cm/s)', fontsize=12)
ax.set_title('Flame Speed vs Chamber Pressure — Full Dataset', fontsize=13)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/fig1_full_dataset.png', dpi=150)
plt.close()
print("Saved fig1_full_dataset.png")

# ── Figure 2: Power-law fits per regime ──────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

for ax, sub_df, popt, r2, color, label, regime in [
    (axes[0], df_low,  popt_low,  r2_low,  COLOR_LOW,  'Low-pressure regime',  'Low'),
    (axes[1], df_high, popt_high, r2_high, COLOR_HIGH, 'High-pressure regime', 'High'),
]:
    P = sub_df['pressure_kPa'].values
    S = sub_df['flame_speed_cm_s'].values
    P_fit = np.linspace(P.min(), P.max(), 300)
    S_fit = power_law(P_fit, *popt)

    ax.scatter(P, S, color=color, s=35, alpha=0.8, zorder=3, label='Measured')
    ax.plot(P_fit, S_fit, color=COLOR_FIT, lw=2, label=f'Power-law fit\n$S_L = {popt[0]:.2f}\\,P^{{{popt[1]:.3f}}}$\n$R^2={r2:.4f}$')
    ax.set_xlabel('Chamber Pressure (kPa)', fontsize=11)
    ax.set_ylabel('Flame Speed (cm/s)', fontsize=11)
    ax.set_title(label, fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

plt.suptitle('Power-Law Fits: Flame Speed vs Chamber Pressure', fontsize=13, y=1.01)
plt.tight_layout()
plt.savefig('report/images/fig2_power_law_fits.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_power_law_fits.png")

# ── Figure 3: Residuals ───────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

for ax, sub_df, popt, color, label in [
    (axes[0], df_low,  popt_low,  COLOR_LOW,  'Low-pressure regime'),
    (axes[1], df_high, popt_high, COLOR_HIGH, 'High-pressure regime'),
]:
    P = sub_df['pressure_kPa'].values
    S = sub_df['flame_speed_cm_s'].values
    S_pred = power_law(P, *popt)
    residuals = S - S_pred
    ax.scatter(P, residuals, color=color, s=30, alpha=0.8)
    ax.axhline(0, color='black', lw=1.2, ls='--')
    ax.set_xlabel('Chamber Pressure (kPa)', fontsize=11)
    ax.set_ylabel('Residual (cm/s)', fontsize=11)
    ax.set_title(f'Residuals — {label}', fontsize=12)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig3_residuals.png', dpi=150)
plt.close()
print("Saved fig3_residuals.png")

# ── Figure 4: Log-log plot (power-law linearisation) ─────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))

for sub_df, popt, color, label in [
    (df_low,  popt_low,  COLOR_LOW,  'Low-pressure'),
    (df_high, popt_high, COLOR_HIGH, 'High-pressure'),
]:
    P = sub_df['pressure_kPa'].values
    S = sub_df['flame_speed_cm_s'].values
    ax.scatter(np.log(P), np.log(S), color=color, s=30, alpha=0.8, label=f'{label} data')
    lnP = np.linspace(np.log(P.min()), np.log(P.max()), 200)
    lnS = np.log(popt[0]) + popt[1] * lnP
    ax.plot(lnP, lnS, color=color, lw=2, ls='--', label=f'{label} fit (n={popt[1]:.3f})')

ax.set_xlabel('ln(Pressure / kPa)', fontsize=12)
ax.set_ylabel('ln(Flame Speed / cm·s⁻¹)', fontsize=12)
ax.set_title('Log–Log Plot: Power-Law Linearisation', fontsize=13)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/fig4_loglog.png', dpi=150)
plt.close()
print("Saved fig4_loglog.png")

# ── Figure 5: Combined fit overlay on full dataset ────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))

P_low_fit  = np.linspace(df_low['pressure_kPa'].min(),  df_low['pressure_kPa'].max(),  300)
P_high_fit = np.linspace(df_high['pressure_kPa'].min(), df_high['pressure_kPa'].max(), 300)

ax.scatter(df_low['pressure_kPa'],  df_low['flame_speed_cm_s'],
           color=COLOR_LOW,  s=28, alpha=0.7, zorder=3)
ax.scatter(df_high['pressure_kPa'], df_high['flame_speed_cm_s'],
           color=COLOR_HIGH, s=28, alpha=0.7, zorder=3)
ax.plot(P_low_fit,  power_law(P_low_fit,  *popt_low),
        color=COLOR_LOW,  lw=2.5, label=f'Low-P fit: $S_L={popt_low[0]:.2f}P^{{{popt_low[1]:.3f}}}$  ($R^2={r2_low:.3f}$)')
ax.plot(P_high_fit, power_law(P_high_fit, *popt_high),
        color=COLOR_HIGH, lw=2.5, label=f'High-P fit: $S_L={popt_high[0]:.2f}P^{{{popt_high[1]:.3f}}}$  ($R^2={r2_high:.3f}$)')
ax.axvline(df.loc[jump_idx, 'pressure_kPa'], color='gray', ls=':', lw=1.5, label='Regime boundary')

ax.set_xlabel('Chamber Pressure (kPa)', fontsize=12)
ax.set_ylabel('Flame Speed (cm/s)', fontsize=12)
ax.set_title('Flame Speed vs Chamber Pressure — Power-Law Fits', fontsize=13)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/fig5_combined_fit.png', dpi=150)
plt.close()
print("Saved fig5_combined_fit.png")

print("\nAll figures saved. Analysis complete.")
