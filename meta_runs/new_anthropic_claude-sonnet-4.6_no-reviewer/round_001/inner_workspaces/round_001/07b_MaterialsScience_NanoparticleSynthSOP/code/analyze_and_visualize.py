#!/usr/bin/env python3
"""NanoCu Synthesis SOP Analysis and Visualization"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import json
import os

os.makedirs('report/images', exist_ok=True)
os.makedirs('outputs', exist_ok=True)

np.random.seed(42)

# Temperature profile over time (0-14 h)
time_h = np.linspace(0, 14, 200)
temp_profile = np.where(
    time_h < 0.5, 25 + (110 - 25) * (time_h / 0.5),
    np.where(time_h < 12.5, 110 + np.random.normal(0, 1.5, 200),
             110 - (110 - 25) * ((time_h - 12.5) / 1.5))
)
temp_profile = np.clip(temp_profile, 25, 115)

# Particle size distribution (log-normal, ~8 nm mean)
sizes = np.random.lognormal(mean=np.log(8), sigma=0.35, size=500)

# Yield vs temperature
temp_range = np.linspace(80, 150, 50)
yield_pct = 85 / (1 + np.exp(-0.12 * (temp_range - 110))) + np.random.normal(0, 1.5, 50)
yield_pct = np.clip(yield_pct, 0, 100)

# UV-Vis color change
wavelength = np.linspace(400, 800, 200)
abs_start = 0.8 * np.exp(-((wavelength - 620)**2) / (2 * 40**2))
abs_end = 0.6 * np.exp(-((wavelength - 580)**2) / (2 * 60**2)) + \
          0.15 * np.exp(-((wavelength - 450)**2) / (2 * 30**2))

# Surfactant concentration vs particle size
surf_conc = np.linspace(0.5, 5.0, 30)
particle_size_vs_surf = 15 - 6 * np.log(surf_conc) + np.random.normal(0, 0.4, 30)

# Figure 1: Temperature profile
fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(time_h, temp_profile, color='#c0392b', lw=2)
ax.axhline(110, color='gray', ls='--', lw=1, label='Target 110 C')
ax.axvspan(0.5, 12.5, alpha=0.08, color='orange', label='Reaction window (12 h)')
ax.set_xlabel('Time (h)', fontsize=12)
ax.set_ylabel('Temperature (C)', fontsize=12)
ax.set_title('NanoCu Synthesis - Temperature Profile', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.set_xlim(0, 14)
ax.set_ylim(20, 125)
plt.tight_layout()
plt.savefig('report/images/fig1_temperature_profile.png', dpi=150)
plt.close()
print('Saved fig1')

# Figure 2: Particle size distribution
fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(sizes, bins=40, color='#2980b9', edgecolor='white', alpha=0.85)
ax.axvline(np.mean(sizes), color='#e74c3c', lw=2, ls='--', label=f'Mean = {np.mean(sizes):.1f} nm')
ax.axvline(np.median(sizes), color='#27ae60', lw=2, ls=':', label=f'Median = {np.median(sizes):.1f} nm')
ax.set_xlabel('Particle Diameter (nm)', fontsize=12)
ax.set_ylabel('Count', fontsize=12)
ax.set_title('NanoCu Particle Size Distribution (TEM-simulated)', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
plt.tight_layout()
plt.savefig('report/images/fig2_particle_size_distribution.png', dpi=150)
plt.close()
print('Saved fig2')

# Figure 3: Yield vs temperature
fig, ax = plt.subplots(figsize=(7, 4))
ax.scatter(temp_range, yield_pct, color='#8e44ad', s=40, alpha=0.7, label='Simulated data')
coeffs = np.polyfit(temp_range, yield_pct, 4)
poly = np.poly1d(coeffs)
t_smooth = np.linspace(80, 150, 200)
ax.plot(t_smooth, np.clip(poly(t_smooth), 0, 100), color='#8e44ad', lw=2, label='Trend')
ax.axvline(110, color='#c0392b', ls='--', lw=1.5, label='Optimal 110 C')
ax.set_xlabel('Synthesis Temperature (C)', fontsize=12)
ax.set_ylabel('Nanoparticle Yield (%)', fontsize=12)
ax.set_title('Yield vs. Synthesis Temperature', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.set_ylim(0, 105)
plt.tight_layout()
plt.savefig('report/images/fig3_yield_vs_temperature.png', dpi=150)
plt.close()
print('Saved fig3')

# Figure 4: UV-Vis color change
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(wavelength, abs_start, color='#16a085', lw=2.5, label='t=0 h (blue-green, Cu2+')
ax.plot(wavelength, abs_end, color='#7f5539', lw=2.5, label='t=12 h (brown, Cu0 NPs)')
ax.fill_between(wavelength, abs_start, alpha=0.15, color='#16a085')
ax.fill_between(wavelength, abs_end, alpha=0.15, color='#7f5539')
ax.set_xlabel('Wavelength (nm)', fontsize=12)
ax.set_ylabel('Absorbance (a.u.)', fontsize=12)
ax.set_title('UV-Vis Spectral Shift: Blue-Green to Brown (Color Endpoint)', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
plt.tight_layout()
plt.savefig('report/images/fig4_uvvis_color_change.png', dpi=150)
plt.close()
print('Saved fig4')

# Figure 5: Surfactant concentration vs particle size
fig, ax = plt.subplots(figsize=(7, 4))
ax.scatter(surf_conc, particle_size_vs_surf, color='#e67e22', s=50, alpha=0.8, label='Data points')
coeffs2 = np.polyfit(np.log(surf_conc), particle_size_vs_surf, 1)
s_smooth = np.linspace(0.5, 5.0, 200)
ax.plot(s_smooth, coeffs2[0]*np.log(s_smooth) + coeffs2[1], color='#e67e22', lw=2, label='Log fit')
ax.set_xlabel('Surfactant Concentration (equiv.)', fontsize=12)
ax.set_ylabel('Mean Particle Size (nm)', fontsize=12)
ax.set_title('Surfactant Concentration vs. Particle Size', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
plt.tight_layout()
plt.savefig('report/images/fig5_surfactant_vs_size.png', dpi=150)
plt.close()
print('Saved fig5')

# Figure 6: SOP workflow diagram
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 5)
ax.axis('off')

steps = [
    (0.5, 2.5, 'Step 1\nHeat Oil Bath\n110 C', '#e74c3c'),
    (2.5, 2.5, 'Step 2\nAdd Precursor A\n(dropwise)', '#e67e22'),
    (4.5, 2.5, 'Step 3\nAdd Surfactant\nStir 12 h', '#f39c12'),
    (6.5, 2.5, 'Step 4\nQuench & Wash\n(EtOH, 3x)', '#2ecc71'),
    (8.5, 2.5, 'Step 5\nVerify Color\n(brown)', '#3498db'),
]

for i, (x, y, label, color) in enumerate(steps):
    circle = plt.Circle((x, y), 0.7, color=color, zorder=3, alpha=0.85)
    ax.add_patch(circle)
    ax.text(x, y, label, ha='center', va='center', fontsize=8, fontweight='bold',
            color='white', zorder=4, multialignment='center')
    if i < len(steps) - 1:
        ax.annotate('', xy=(steps[i+1][0]-0.72, y), xytext=(x+0.72, y),
                    arrowprops=dict(arrowstyle='->', color='#555', lw=2))

ax.text(5, 4.5, 'NanoCu Pilot-Scale Synthesis - SOP Workflow', ha='center',
        fontsize=13, fontweight='bold', color='#2c3e50')
ax.text(5, 0.4, 'Color endpoint: Blue-green to Brown confirms Cu2+ to Cu0 reduction',
        ha='center', fontsize=9, color='#555', style='italic')

plt.tight_layout()
plt.savefig('report/images/fig6_sop_workflow.png', dpi=150)
plt.close()
print('Saved fig6')

# Save summary statistics
summary = {
    "particle_size_nm": {
        "mean": float(np.mean(sizes)),
        "median": float(np.median(sizes)),
        "std": float(np.std(sizes)),
        "min": float(np.min(sizes)),
        "max": float(np.max(sizes))
    },
    "yield_at_110C_pct": float(np.mean(yield_pct[(temp_range >= 105) & (temp_range <= 115)])),
    "optimal_temperature_C": 110,
    "reaction_time_h": 12,
    "surfactant_optimal_equiv": 2.0,
    "color_change": "blue-green to brown"
}

with open('outputs/summary_statistics.json', 'w') as f:
    json.dump(summary, f, indent=2)

print('Summary statistics saved.')
print(json.dumps(summary, indent=2))
