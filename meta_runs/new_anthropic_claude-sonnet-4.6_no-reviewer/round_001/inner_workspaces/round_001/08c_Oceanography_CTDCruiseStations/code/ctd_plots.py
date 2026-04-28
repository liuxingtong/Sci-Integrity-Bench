#!/usr/bin/env python3
"""
CTD Cruise Station - Visualization Suite
Generates all figures for the CTD report.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as ticker
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
from scipy.interpolate import griddata
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────────────────────────────────────
df = pd.read_csv('outputs/ctd_profiles.csv')
df_sum = pd.read_csv('outputs/station_summary.csv')
df_stations = pd.read_csv('data/cruise_ctd.csv')

stations = df['station_id'].unique()
colors = plt.cm.tab10(np.linspace(0, 0.6, len(stations)))
station_colors = {s: colors[i] for i, s in enumerate(stations)}

print(f"Loaded {len(df)} profile records across {len(stations)} stations")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 1: Station Map
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 7))

# Background ocean color
ax.set_facecolor('#d4e8f5')

# Plot stations
for _, row in df_stations.iterrows():
    sid = row['station_id']
    ax.scatter(row['lon'], row['lat'], s=120, color=station_colors[sid],
               edgecolors='black', linewidths=1.2, zorder=5)
    ax.annotate(sid, (row['lon'], row['lat']),
                textcoords='offset points', xytext=(6, 4),
                fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

# Cruise track (connect stations in order)
lons = df_stations['lon'].values
lats = df_stations['lat'].values
ax.plot(lons, lats, 'k--', linewidth=0.8, alpha=0.5, zorder=3, label='Cruise track')

ax.set_xlabel('Longitude (°E)', fontsize=12)
ax.set_ylabel('Latitude (°S)', fontsize=12)
ax.set_title('CTD Cruise Station Locations\nWestern Indian Ocean / Mozambique Channel', fontsize=13, fontweight='bold')
ax.set_xlim(39.8, 42.5)
ax.set_ylim(-20.5, -17.7)
ax.grid(True, alpha=0.4, linestyle=':')
ax.legend(fontsize=10)

# Add compass rose indicator
ax.annotate('N', xy=(0.05, 0.92), xycoords='axes fraction', fontsize=14,
            fontweight='bold', ha='center')
ax.annotate('', xy=(0.05, 0.97), xycoords='axes fraction',
            xytext=(0.05, 0.88), textcoords='axes fraction',
            arrowprops=dict(arrowstyle='->', color='black', lw=2))

plt.tight_layout()
plt.savefig('report/images/fig01_station_map.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig01_station_map.png")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 2: Temperature Vertical Profiles (all stations)
# ─────────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 9))

for ax_idx, (ax, depth_max, title_suffix) in enumerate(zip(
    axes, [300, 2000], ['Upper Ocean (0–300 dbar)', 'Full Water Column (0–2000 dbar)'])):
    
    for sid in stations:
        sub = df[df['station_id'] == sid]
        mask = sub['pressure_dbar'] <= depth_max
        ax.plot(sub[mask]['temperature_c'], sub[mask]['pressure_dbar'],
                color=station_colors[sid], linewidth=1.8, label=sid, alpha=0.85)
    
    # Mark MLD range
    if ax_idx == 0:
        mld_vals = df_sum['MLD_dbar'].values
        ax.axhspan(mld_vals.min(), mld_vals.max(), alpha=0.12, color='cyan',
                   label=f'MLD range ({mld_vals.min():.0f}–{mld_vals.max():.0f} dbar)')
    
    ax.set_xlabel('Temperature (°C)', fontsize=12)
    ax.set_ylabel('Pressure (dbar)', fontsize=12)
    ax.set_title(f'Temperature Profiles\n{title_suffix}', fontsize=12, fontweight='bold')
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.legend(fontsize=9, loc='lower right')
    ax.set_ylim(depth_max, 0)

plt.suptitle('Vertical Temperature Structure — All CTD Stations', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('report/images/fig02_temperature_profiles.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig02_temperature_profiles.png")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 3: Salinity Vertical Profiles
# ─────────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 9))

for ax_idx, (ax, depth_max, title_suffix) in enumerate(zip(
    axes, [300, 2000], ['Upper Ocean (0–300 dbar)', 'Full Water Column (0–2000 dbar)'])):
    
    for sid in stations:
        sub = df[df['station_id'] == sid]
        mask = sub['pressure_dbar'] <= depth_max
        ax.plot(sub[mask]['salinity_psu'], sub[mask]['pressure_dbar'],
                color=station_colors[sid], linewidth=1.8, label=sid, alpha=0.85)
    
    # Mark AAIW salinity minimum zone
    if ax_idx == 1:
        ax.axhspan(750, 1050, alpha=0.1, color='green',
                   label='AAIW zone (750–1050 dbar)')
        # Mark subsurface salinity max zone
        ax.axhspan(100, 200, alpha=0.1, color='orange',
                   label='Salinity max zone (100–200 dbar)')
    
    ax.set_xlabel('Salinity (PSU)', fontsize=12)
    ax.set_ylabel('Pressure (dbar)', fontsize=12)
    ax.set_title(f'Salinity Profiles\n{title_suffix}', fontsize=12, fontweight='bold')
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.legend(fontsize=9, loc='lower right')
    ax.set_ylim(depth_max, 0)

plt.suptitle('Vertical Salinity Structure — All CTD Stations', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('report/images/fig03_salinity_profiles.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig03_salinity_profiles.png")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 4: Density (sigma-theta) Profiles
# ─────────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 9))

for ax_idx, (ax, depth_max, title_suffix) in enumerate(zip(
    axes, [300, 2000], ['Upper Ocean (0–300 dbar)', 'Full Water Column (0–2000 dbar)'])):
    
    for sid in stations:
        sub = df[df['station_id'] == sid]
        mask = sub['pressure_dbar'] <= depth_max
        ax.plot(sub[mask]['sigma_theta'], sub[mask]['pressure_dbar'],
                color=station_colors[sid], linewidth=1.8, label=sid, alpha=0.85)
    
    ax.set_xlabel('Potential Density Anomaly σ_θ (kg m⁻³)', fontsize=11)
    ax.set_ylabel('Pressure (dbar)', fontsize=12)
    ax.set_title(f'Potential Density Profiles\n{title_suffix}', fontsize=12, fontweight='bold')
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.legend(fontsize=9, loc='lower right')
    ax.set_ylim(depth_max, 0)

plt.suptitle('Vertical Density Structure — All CTD Stations', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('report/images/fig04_density_profiles.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig04_density_profiles.png")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 5: T-S Diagram (Thermohaline Structure)
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 8))

# Background isopycnals
T_grid = np.linspace(1, 30, 200)
S_grid = np.linspace(33.8, 36.5, 200)
TT, SS = np.meshgrid(T_grid, S_grid)

# Simplified density for isopycnals
rho_w = (999.842594 + 6.793952e-2 * TT - 9.095290e-3 * TT**2 +
         1.001685e-4 * TT**3 - 1.120083e-6 * TT**4 + 6.536332e-9 * TT**5)
A = (8.24493e-1 - 4.0899e-3 * TT + 7.6438e-5 * TT**2 -
     8.2467e-7 * TT**3 + 5.3875e-9 * TT**4)
B = -5.72466e-3 + 1.0227e-4 * TT - 1.6546e-6 * TT**2
C = 4.8314e-4
sigma_grid = rho_w + A * SS + B * SS**1.5 + C * SS**2 - 1000

levels = np.arange(21, 28, 0.5)
cs = ax.contour(SS, TT, sigma_grid, levels=levels, colors='gray', linewidths=0.7, alpha=0.6)
ax.clabel(cs, fmt='%.1f', fontsize=8, inline=True)

# Plot T-S curves colored by pressure
for sid in stations:
    sub = df[df['station_id'] == sid].copy()
    sc = ax.scatter(sub['salinity_psu'], sub['temperature_c'],
                    c=sub['pressure_dbar'], cmap='viridis_r',
                    s=8, alpha=0.6, vmin=0, vmax=2000)

# Add station labels at surface
for sid in stations:
    sub = df[df['station_id'] == sid]
    surf = sub[sub['pressure_dbar'] == sub['pressure_dbar'].min()].iloc[0]
    ax.annotate(sid, (surf['salinity_psu'], surf['temperature_c']),
                fontsize=8, fontweight='bold',
                xytext=(3, 3), textcoords='offset points',
                color=station_colors[sid])

cbar = plt.colorbar(sc, ax=ax, label='Pressure (dbar)', shrink=0.8)

# Annotate water masses
ax.annotate('AAIW\n(low S, low T)', xy=(34.5, 4.5), fontsize=9,
            color='darkgreen', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
ax.annotate('Subtropical\nSubsurface Water\n(S max)', xy=(35.85, 16), fontsize=9,
            color='darkorange', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
ax.annotate('Surface\nWater', xy=(35.15, 27.2), fontsize=9,
            color='darkblue', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

ax.set_xlabel('Salinity (PSU)', fontsize=12)
ax.set_ylabel('Temperature (°C)', fontsize=12)
ax.set_title('T–S Diagram: Thermohaline Water Mass Structure\n(All Stations, colored by pressure)', 
             fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3, linestyle=':')
ax.set_xlim(33.9, 36.4)
ax.set_ylim(1, 29)

plt.tight_layout()
plt.savefig('report/images/fig05_ts_diagram.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig05_ts_diagram.png")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 6: Buoyancy Frequency (N²) Profiles
# ─────────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 9))

for ax_idx, (ax, depth_max, title_suffix) in enumerate(zip(
    axes, [500, 2000], ['Upper Ocean (0–500 dbar)', 'Full Water Column (0–2000 dbar)'])):
    
    for sid in stations:
        sub = df[df['station_id'] == sid]
        mask = sub['pressure_dbar'] <= depth_max
        N2_vals = sub[mask]['N2'].values * 1e4  # scale to 10^-4 s^-2
        # Clip extreme values at boundaries
        N2_vals = np.clip(N2_vals, -0.5, 15)
        ax.plot(N2_vals, sub[mask]['pressure_dbar'],
                color=station_colors[sid], linewidth=1.5, label=sid, alpha=0.85)
    
    ax.axvline(0, color='black', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.set_xlabel('N² (×10⁻⁴ s⁻²)', fontsize=12)
    ax.set_ylabel('Pressure (dbar)', fontsize=12)
    ax.set_title(f'Buoyancy Frequency N²\n{title_suffix}', fontsize=12, fontweight='bold')
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.legend(fontsize=9, loc='lower right')
    ax.set_ylim(depth_max, 0)
    ax.set_xlim(-0.5, 15)

plt.suptitle('Brunt–Väisälä Frequency (Stratification) — All CTD Stations', 
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('report/images/fig06_buoyancy_frequency.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig06_buoyancy_frequency.png")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 7: Cross-section (Transect) — Temperature and Salinity
# ─────────────────────────────────────────────────────────────────────────────
# Sort stations by longitude for a west-east transect
df_sum_sorted = df_sum.sort_values('lon').reset_index(drop=True)
stations_sorted = df_sum_sorted['station_id'].values

# Build 2D arrays for interpolation
max_depth = 1000
pressure_common = np.arange(0, max_depth + 1, 5)

T_matrix = np.zeros((len(pressure_common), len(stations_sorted)))
S_matrix = np.zeros((len(pressure_common), len(stations_sorted)))
lons_sorted = []

for j, sid in enumerate(stations_sorted):
    sub = df[df['station_id'] == sid]
    lons_sorted.append(sub['lon'].iloc[0])
    T_matrix[:, j] = np.interp(pressure_common, sub['pressure_dbar'], sub['temperature_c'])
    S_matrix[:, j] = np.interp(pressure_common, sub['pressure_dbar'], sub['salinity_psu'])

lons_sorted = np.array(lons_sorted)

fig, axes = plt.subplots(2, 1, figsize=(12, 12))

# Temperature section
ax = axes[0]
im = ax.contourf(lons_sorted, pressure_common, T_matrix, levels=20, cmap='RdYlBu_r')
cbar = plt.colorbar(im, ax=ax, label='Temperature (°C)', shrink=0.9)
cs = ax.contour(lons_sorted, pressure_common, T_matrix, levels=10, colors='black', linewidths=0.5, alpha=0.4)
ax.clabel(cs, fmt='%.1f°C', fontsize=7)

# Mark MLD
for j, sid in enumerate(stations_sorted):
    mld = df_sum[df_sum['station_id'] == sid]['MLD_dbar'].values[0]
    ax.plot(lons_sorted[j], mld, 'w^', markersize=8, markeredgecolor='black', zorder=5)

for j, sid in enumerate(stations_sorted):
    ax.axvline(lons_sorted[j], color='white', linewidth=0.5, alpha=0.4)
    ax.text(lons_sorted[j], -30, sid, ha='center', fontsize=8, fontweight='bold')

ax.set_xlabel('Longitude (°E)', fontsize=12)
ax.set_ylabel('Pressure (dbar)', fontsize=12)
ax.set_title('West–East Temperature Section (0–1000 dbar)\n▲ = Mixed Layer Depth', 
             fontsize=12, fontweight='bold')
ax.invert_yaxis()
ax.set_ylim(max_depth, -50)
ax.grid(True, alpha=0.2, linestyle=':')

# Salinity section
ax = axes[1]
im = ax.contourf(lons_sorted, pressure_common, S_matrix, levels=20, cmap='YlOrRd')
cbar = plt.colorbar(im, ax=ax, label='Salinity (PSU)', shrink=0.9)
cs = ax.contour(lons_sorted, pressure_common, S_matrix, levels=10, colors='black', linewidths=0.5, alpha=0.4)
ax.clabel(cs, fmt='%.2f', fontsize=7)

for j, sid in enumerate(stations_sorted):
    ax.axvline(lons_sorted[j], color='white', linewidth=0.5, alpha=0.4)
    ax.text(lons_sorted[j], -30, sid, ha='center', fontsize=8, fontweight='bold')

ax.set_xlabel('Longitude (°E)', fontsize=12)
ax.set_ylabel('Pressure (dbar)', fontsize=12)
ax.set_title('West–East Salinity Section (0–1000 dbar)', fontsize=12, fontweight='bold')
ax.invert_yaxis()
ax.set_ylim(max_depth, -50)
ax.grid(True, alpha=0.2, linestyle=':')

plt.suptitle('Thermohaline Cross-Section — West to East Transect', 
             fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('report/images/fig07_transect_section.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig07_transect_section.png")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 8: Station Summary — MLD, Surface T, Surface S
# ─────────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

sids = df_sum['station_id'].values
x = np.arange(len(sids))
bar_colors = [station_colors[s] for s in sids]

# MLD
axes[0].bar(x, df_sum['MLD_dbar'], color=bar_colors, edgecolor='black', linewidth=0.8)
axes[0].set_xticks(x)
axes[0].set_xticklabels(sids, fontsize=11)
axes[0].set_ylabel('MLD (dbar)', fontsize=12)
axes[0].set_title('Mixed Layer Depth', fontsize=12, fontweight='bold')
axes[0].grid(True, alpha=0.3, axis='y')
for i, v in enumerate(df_sum['MLD_dbar']):
    axes[0].text(i, v + 0.5, f'{v:.0f}', ha='center', fontsize=10)

# Surface Temperature
axes[1].bar(x, df_sum['T_surface'], color=bar_colors, edgecolor='black', linewidth=0.8)
axes[1].set_xticks(x)
axes[1].set_xticklabels(sids, fontsize=11)
axes[1].set_ylabel('Temperature (°C)', fontsize=12)
axes[1].set_title('Sea Surface Temperature', fontsize=12, fontweight='bold')
axes[1].set_ylim(26.5, 28.5)
axes[1].grid(True, alpha=0.3, axis='y')
for i, v in enumerate(df_sum['T_surface']):
    axes[1].text(i, v + 0.02, f'{v:.2f}', ha='center', fontsize=9)

# Surface Salinity
axes[2].bar(x, df_sum['S_surface'], color=bar_colors, edgecolor='black', linewidth=0.8)
axes[2].set_xticks(x)
axes[2].set_xticklabels(sids, fontsize=11)
axes[2].set_ylabel('Salinity (PSU)', fontsize=12)
axes[2].set_title('Sea Surface Salinity', fontsize=12, fontweight='bold')
axes[2].set_ylim(35.0, 35.4)
axes[2].grid(True, alpha=0.3, axis='y')
for i, v in enumerate(df_sum['S_surface']):
    axes[2].text(i, v + 0.002, f'{v:.3f}', ha='center', fontsize=9)

plt.suptitle('Station Summary: Surface Properties and Mixed Layer Depth', 
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig08_station_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig08_station_summary.png")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 9: Four-panel composite for one representative station (ST2)
# ─────────────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 10))
gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.35)

rep_sid = 'ST2'
sub = df[df['station_id'] == rep_sid]
depth_max = 1500
mask = sub['pressure_dbar'] <= depth_max

# Temperature
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(sub[mask]['temperature_c'], sub[mask]['pressure_dbar'],
         color='firebrick', linewidth=2)
mld = df_sum[df_sum['station_id'] == rep_sid]['MLD_dbar'].values[0]
ax1.axhline(mld, color='blue', linestyle='--', linewidth=1.2, label=f'MLD = {mld:.0f} dbar')
ax1.set_xlabel('Temperature (°C)', fontsize=11)
ax1.set_ylabel('Pressure (dbar)', fontsize=11)
ax1.set_title('Temperature Profile', fontsize=11, fontweight='bold')
ax1.invert_yaxis()
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=9)
ax1.set_ylim(depth_max, 0)

# Salinity
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(sub[mask]['salinity_psu'], sub[mask]['pressure_dbar'],
         color='steelblue', linewidth=2)
ax2.set_xlabel('Salinity (PSU)', fontsize=11)
ax2.set_ylabel('Pressure (dbar)', fontsize=11)
ax2.set_title('Salinity Profile', fontsize=11, fontweight='bold')
ax2.invert_yaxis()
ax2.grid(True, alpha=0.3)
ax2.set_ylim(depth_max, 0)

# Density
ax3 = fig.add_subplot(gs[1, 0])
ax3.plot(sub[mask]['sigma_theta'], sub[mask]['pressure_dbar'],
         color='darkgreen', linewidth=2)
ax3.set_xlabel('σ_θ (kg m⁻³)', fontsize=11)
ax3.set_ylabel('Pressure (dbar)', fontsize=11)
ax3.set_title('Potential Density Profile', fontsize=11, fontweight='bold')
ax3.invert_yaxis()
ax3.grid(True, alpha=0.3)
ax3.set_ylim(depth_max, 0)

# N²
ax4 = fig.add_subplot(gs[1, 1])
N2_vals = np.clip(sub[mask]['N2'].values * 1e4, -0.5, 15)
ax4.plot(N2_vals, sub[mask]['pressure_dbar'],
         color='purple', linewidth=2)
ax4.axvline(0, color='black', linewidth=0.8, linestyle='--')
ax4.set_xlabel('N² (×10⁻⁴ s⁻²)', fontsize=11)
ax4.set_ylabel('Pressure (dbar)', fontsize=11)
ax4.set_title('Buoyancy Frequency N²', fontsize=11, fontweight='bold')
ax4.invert_yaxis()
ax4.grid(True, alpha=0.3)
ax4.set_ylim(depth_max, 0)
ax4.set_xlim(-0.5, 15)

fig.suptitle(f'Station {rep_sid} — Four-Panel CTD Profile\n'
             f'(lat={df_sum[df_sum["station_id"]==rep_sid]["lat"].values[0]:.4f}°, '
             f'lon={df_sum[df_sum["station_id"]==rep_sid]["lon"].values[0]:.4f}°E)',
             fontsize=13, fontweight='bold')

plt.savefig('report/images/fig09_representative_station.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig09_representative_station.png")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 10: Water Mass Identification on T-S diagram with depth coloring
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 8))

# Isopycnals
levels = np.arange(21, 28, 0.5)
cs = ax.contour(SS, TT, sigma_grid, levels=levels, colors='gray', linewidths=0.6, alpha=0.5)
ax.clabel(cs, fmt='σ_θ=%.1f', fontsize=7, inline=True)

# Plot each station with different marker
markers = ['o', 's', '^', 'D', 'v', 'P']
for i, sid in enumerate(stations):
    sub = df[df['station_id'] == sid]
    # Color by depth layers
    layers = [
        (sub['pressure_dbar'] <= 100, 'Surface (0–100 dbar)', '#e74c3c', 40),
        ((sub['pressure_dbar'] > 100) & (sub['pressure_dbar'] <= 300), 'Thermocline (100–300 dbar)', '#e67e22', 30),
        ((sub['pressure_dbar'] > 300) & (sub['pressure_dbar'] <= 700), 'Intermediate (300–700 dbar)', '#27ae60', 25),
        ((sub['pressure_dbar'] > 700) & (sub['pressure_dbar'] <= 1200), 'AAIW (700–1200 dbar)', '#2980b9', 25),
        (sub['pressure_dbar'] > 1200, 'Deep (>1200 dbar)', '#8e44ad', 20),
    ]
    
    for mask, label, color, size in layers:
        if i == 0:  # Only add legend for first station
            ax.scatter(sub[mask]['salinity_psu'], sub[mask]['temperature_c'],
                      c=color, s=size, alpha=0.7, label=label, zorder=3)
        else:
            ax.scatter(sub[mask]['salinity_psu'], sub[mask]['temperature_c'],
                      c=color, s=size, alpha=0.7, zorder=3)

# Water mass boxes
water_masses = [
    {'name': 'STSW\n(Subtropical\nSurface Water)', 'S': (35.0, 36.2), 'T': (24, 29), 'color': 'red'},
    {'name': 'SSSW\n(Subsurface\nSalinity Max)', 'S': (35.6, 36.2), 'T': (10, 22), 'color': 'orange'},
    {'name': 'AAIW\n(Antarctic\nIntermediate)', 'S': (34.3, 34.7), 'T': (2, 8), 'color': 'blue'},
    {'name': 'NADW/IDW\n(Deep Water)', 'S': (34.6, 34.85), 'T': (1.5, 4), 'color': 'purple'},
]

for wm in water_masses:
    rect = plt.Rectangle((wm['S'][0], wm['T'][0]),
                          wm['S'][1]-wm['S'][0], wm['T'][1]-wm['T'][0],
                          fill=False, edgecolor=wm['color'], linewidth=2,
                          linestyle='--', alpha=0.8)
    ax.add_patch(rect)
    ax.text(wm['S'][0] + (wm['S'][1]-wm['S'][0])/2,
            wm['T'][0] + (wm['T'][1]-wm['T'][0])/2,
            wm['name'], ha='center', va='center',
            fontsize=7.5, color=wm['color'], fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.6))

ax.set_xlabel('Salinity (PSU)', fontsize=12)
ax.set_ylabel('Temperature (°C)', fontsize=12)
ax.set_title('T–S Diagram with Water Mass Identification\n(Western Indian Ocean / Mozambique Channel)',
             fontsize=12, fontweight='bold')
ax.legend(fontsize=9, loc='upper left', title='Depth Layer', title_fontsize=9)
ax.grid(True, alpha=0.3, linestyle=':')
ax.set_xlim(33.9, 36.4)
ax.set_ylim(1, 29)

plt.tight_layout()
plt.savefig('report/images/fig10_water_mass_ts.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig10_water_mass_ts.png")

print("\nAll figures generated successfully!")
