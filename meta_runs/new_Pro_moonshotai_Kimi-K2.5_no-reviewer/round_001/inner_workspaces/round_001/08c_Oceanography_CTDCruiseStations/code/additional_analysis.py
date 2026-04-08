"""
Additional CTD Analysis: Thermohaline circulation and mixing
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Load data
ctd_data = pd.read_csv('outputs/ctd_profiles.csv')
stations = pd.read_csv('data/cruise_ctd.csv')

plt.style.use('seaborn-v0_8-whitegrid')

# Figure 4: Detailed T-S diagram with density contours
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Main T-S diagram with density contours
ax1 = axes[0, 0]
# Create density contour grid
sal_range = np.linspace(ctd_data['salinity_psu'].min()-0.1, ctd_data['salinity_psu'].max()+0.1, 100)
temp_range = np.linspace(ctd_data['temperature_c'].min()-1, ctd_data['temperature_c'].max()+1, 100)
S, T = np.meshgrid(sal_range, temp_range)

# Calculate density for contours (simplified)
P = 0  # Surface pressure for reference
sigma = 999.842594 + 6.793952e-2 * T - 9.095290e-3 * T**2 + 1.001685e-4 * T**3
sigma -= 5.2848e-2 * T * S + 7.35e-4 * T**2 * S
sigma += 8.24493e-1 * S - 4.0899e-3 * S**2 + 7.6438e-5 * S**3
sigma -= 1000

contours = ax1.contour(S, T, sigma, levels=15, colors='gray', linewidths=0.5, alpha=0.7)
ax1.clabel(contours, inline=True, fontsize=8, fmt='%1.1f')

# Plot data points colored by depth
scatter = ax1.scatter(ctd_data['salinity_psu'], ctd_data['temperature_c'], 
                      c=ctd_data['depth_m'], cmap='plasma_r', s=15, alpha=0.6)
ax1.set_xlabel('Salinity (PSU)', fontsize=12)
ax1.set_ylabel('Temperature (°C)', fontsize=12)
ax1.set_title('T-S Diagram with Density Contours', fontsize=14, fontweight='bold')
cbar = plt.colorbar(scatter, ax=ax1)
cbar.set_label('Depth (m)', fontsize=10)
ax1.grid(True, alpha=0.3)

# Temperature-Salinity correlation by depth layers
ax2 = axes[0, 1]
surface = ctd_data[ctd_data['depth_m'] <= 100]
middle = ctd_data[(ctd_data['depth_m'] > 100) & (ctd_data['depth_m'] <= 500)]
deep = ctd_data[ctd_data['depth_m'] > 500]

ax2.scatter(surface['salinity_psu'], surface['temperature_c'], 
            c='red', s=30, alpha=0.5, label='Surface (0-100m)')
ax2.scatter(middle['salinity_psu'], middle['temperature_c'], 
            c='green', s=30, alpha=0.5, label='Intermediate (100-500m)')
ax2.scatter(deep['salinity_psu'], deep['temperature_c'], 
            c='blue', s=30, alpha=0.5, label='Deep (>500m)')

# Add correlation lines
for data, color, label in [(surface, 'red', 'Surface'), (middle, 'green', 'Intermediate'), (deep, 'blue', 'Deep')]:
    if len(data) > 1:
        z = np.polyfit(data['salinity_psu'], data['temperature_c'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(data['salinity_psu'].min(), data['salinity_psu'].max(), 100)
        ax2.plot(x_line, p(x_line), color=color, linestyle='--', linewidth=2, alpha=0.8)

ax2.set_xlabel('Salinity (PSU)', fontsize=12)
ax2.set_ylabel('Temperature (°C)', fontsize=12)
ax2.set_title('T-S Relationships by Depth Layer', fontsize=14, fontweight='bold')
ax2.legend(loc='upper right', fontsize=10)
ax2.grid(True, alpha=0.3)

# Vertical gradients
ax3 = axes[1, 0]
gradients = []
station_ids = []
for station in ctd_data['station_id'].unique():
    station_data = ctd_data[ctd_data['station_id'] == station].sort_values('depth_m')
    # Calculate temperature gradient (dT/dz)
    temp_grad = np.gradient(station_data['temperature_c'], station_data['depth_m'])
    ax3.plot(temp_grad, station_data['depth_m'], linewidth=2, label=station, alpha=0.8)
    
ax3.axvline(x=0, color='black', linestyle='--', alpha=0.5)
ax3.set_xlabel('Temperature Gradient (°C/m)', fontsize=12)
ax3.set_ylabel('Depth (m)', fontsize=12)
ax3.set_ylim(1000, 0)
ax3.set_title('Vertical Temperature Gradients', fontsize=14, fontweight='bold')
ax3.legend(loc='lower right', fontsize=9)
ax3.grid(True, alpha=0.3)

# Salinity gradients
ax4 = axes[1, 1]
for station in ctd_data['station_id'].unique():
    station_data = ctd_data[ctd_data['station_id'] == station].sort_values('depth_m')
    sal_grad = np.gradient(station_data['salinity_psu'], station_data['depth_m'])
    ax4.plot(sal_grad, station_data['depth_m'], linewidth=2, label=station, alpha=0.8)

ax4.axvline(x=0, color='black', linestyle='--', alpha=0.5)
ax4.set_xlabel('Salinity Gradient (PSU/m)', fontsize=12)
ax4.set_ylabel('Depth (m)', fontsize=12)
ax4.set_ylim(1000, 0)
ax4.set_title('Vertical Salinity Gradients', fontsize=14, fontweight='bold')
ax4.legend(loc='lower right', fontsize=9)
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/thermohaline_analysis.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/thermohaline_analysis.png")
plt.close()

# Figure 5: Station comparison and spatial variability
fig2, axes = plt.subplots(2, 2, figsize=(14, 10))

# Spatial distribution of surface properties
ax1 = axes[0, 0]
surface_data = ctd_data[ctd_data['depth_m'] <= 50].groupby('station_id').mean()
scatter = ax1.scatter(surface_data['lon'], surface_data['lat'], 
                      c=surface_data['temperature_c'], s=300, cmap='RdYlBu_r', 
                      edgecolors='black', linewidth=2, vmin=24, vmax=30)
for station, row in surface_data.iterrows():
    ax1.annotate(f'{station}\n{row["temperature_c"]:.1f}°C', 
                 (row['lon'], row['lat']), 
                 xytext=(10, 10), textcoords='offset points', fontsize=9)
ax1.set_xlabel('Longitude (°E)', fontsize=12)
ax1.set_ylabel('Latitude (°S)', fontsize=12)
ax1.set_title('Surface Temperature Distribution', fontsize=14, fontweight='bold')
plt.colorbar(scatter, ax=ax1, label='Temperature (°C)')
ax1.grid(True, alpha=0.3)

# Surface salinity distribution
ax2 = axes[0, 1]
scatter = ax2.scatter(surface_data['lon'], surface_data['lat'], 
                      c=surface_data['salinity_psu'], s=300, cmap='viridis', 
                      edgecolors='black', linewidth=2, vmin=35.0, vmax=35.6)
for station, row in surface_data.iterrows():
    ax2.annotate(f'{station}\n{row["salinity_psu"]:.2f}', 
                 (row['lon'], row['lat']), 
                 xytext=(10, 10), textcoords='offset points', fontsize=9)
ax2.set_xlabel('Longitude (°E)', fontsize=12)
ax2.set_ylabel('Latitude (°S)', fontsize=12)
ax2.set_title('Surface Salinity Distribution', fontsize=14, fontweight='bold')
plt.colorbar(scatter, ax=ax2, label='Salinity (PSU)')
ax2.grid(True, alpha=0.3)

# Thermocline characteristics
ax3 = axes[1, 0]
thermocline_data = []
for station in ctd_data['station_id'].unique():
    station_data = ctd_data[ctd_data['station_id'] == station].sort_values('depth_m')
    # Find maximum temperature gradient (thermocline)
    temp_grad = np.abs(np.gradient(station_data['temperature_c'], station_data['depth_m']))
    thermocline_idx = np.argmax(temp_grad)
    thermocline_depth = station_data.iloc[thermocline_idx]['depth_m']
    thermocline_temp = station_data.iloc[thermocline_idx]['temperature_c']
    thermocline_data.append({
        'station': station,
        'depth': thermocline_depth,
        'temp': thermocline_temp,
        'gradient': temp_grad[thermocline_idx]
    })

thermo_df = pd.DataFrame(thermocline_data)
bars = ax3.bar(thermo_df['station'], thermo_df['depth'], 
               color='orange', edgecolor='black', alpha=0.7)
ax3.set_xlabel('Station ID', fontsize=12)
ax3.set_ylabel('Thermocline Depth (m)', fontsize=12)
ax3.set_title('Thermocline Depth by Station', fontsize=14, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')
for bar, val in zip(bars, thermo_df['depth']):
    ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
             f'{val:.0f}', ha='center', va='bottom', fontsize=9)

# Stratification index (Brunt-Väisälä frequency proxy)
ax4 = axes[1, 1]
stratification = []
for station in ctd_data['station_id'].unique():
    station_data = ctd_data[ctd_data['station_id'] == station].sort_values('depth_m')
    # Calculate density gradient as proxy for stratification
    dens_grad = np.gradient(station_data['sigma_theta'], station_data['depth_m'])
    # Average stratification in upper 200m
    upper_mask = station_data['depth_m'] <= 200
    if upper_mask.sum() > 0:
        avg_strat = np.mean(dens_grad[upper_mask])
        stratification.append({'station': station, 'stratification': avg_strat})

strat_df = pd.DataFrame(stratification)
bars = ax4.bar(strat_df['station'], strat_df['stratification'], 
               color='purple', edgecolor='black', alpha=0.7)
ax4.set_xlabel('Station ID', fontsize=12)
ax4.set_ylabel('Stratification Index (kg/m⁴)', fontsize=12)
ax4.set_title('Upper Ocean Stratification', fontsize=14, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')
ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('report/images/spatial_variability.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/spatial_variability.png")
plt.close()

# Statistical analysis
print("\n" + "="*60)
print("STATISTICAL ANALYSIS")
print("="*60)

# Correlation analysis
print("\nCorrelation Analysis:")
corr_temp_sal = stats.pearsonr(ctd_data['temperature_c'], ctd_data['salinity_psu'])
print(f"Temperature vs Salinity: r = {corr_temp_sal[0]:.3f}, p = {corr_temp_sal[1]:.3e}")

corr_temp_depth = stats.pearsonr(ctd_data['temperature_c'], ctd_data['depth_m'])
print(f"Temperature vs Depth: r = {corr_temp_depth[0]:.3f}, p = {corr_temp_depth[1]:.3e}")

corr_sal_depth = stats.pearsonr(ctd_data['salinity_psu'], ctd_data['depth_m'])
print(f"Salinity vs Depth: r = {corr_sal_depth[0]:.3f}, p = {corr_sal_depth[1]:.3e}")

# ANOVA for station differences
from scipy.stats import f_oneway

station_groups_temp = [ctd_data[ctd_data['station_id'] == s]['temperature_c'].values 
                       for s in ctd_data['station_id'].unique()]
f_stat_temp, p_val_temp = f_oneway(*station_groups_temp)
print(f"\nANOVA - Temperature differences between stations:")
print(f"F-statistic: {f_stat_temp:.3f}, p-value: {p_val_temp:.3e}")

station_groups_sal = [ctd_data[ctd_data['station_id'] == s]['salinity_psu'].values 
                      for s in ctd_data['station_id'].unique()]
f_stat_sal, p_val_sal = f_oneway(*station_groups_sal)
print(f"\nANOVA - Salinity differences between stations:")
print(f"F-statistic: {f_stat_sal:.3f}, p-value: {p_val_sal:.3e}")

# Save thermocline data
thermo_df.to_csv('outputs/thermocline_analysis.csv', index=False)
print("\nThermocline analysis saved to outputs/thermocline_analysis.csv")

print("\nAdditional analysis complete!")
