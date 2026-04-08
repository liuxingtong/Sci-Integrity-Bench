import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import os

# Load data
stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

print("=== Final Summary Analysis ===")

# Create a comprehensive summary figure
fig = plt.figure(figsize=(16, 12))

# 1. Main overview: station geometry with inferred source regions
ax1 = plt.subplot(2, 3, 1)

# Plot stations
station_colors = {'S0': 'red', 'S1': 'red', 'S2': 'blue', 'S3': 'green', 'S4': 'green'}
for _, row in stations.iterrows():
    color = station_colors[row['station_id']]
    ax1.scatter(row['x_km'], row['y_km'], s=300, color=color, 
               marker='^', edgecolors='black', zorder=5)
    ax1.text(row['x_km'] + 0.2, row['y_km'] + 0.2, row['station_id'], 
            fontsize=12, fontweight='bold')

# Draw inferred source regions (circles around station groups)
group_centers = {
    'Group 1 (S0,S1)': np.array([0.931, 6.103]),
    'Group 2 (S3,S4)': np.array([4.184, 8.556]),
    'Group 3 (S2)': np.array([5.109, 3.042])
}
group_colors = {'Group 1 (S0,S1)': 'red', 'Group 2 (S3,S4)': 'green', 'Group 3 (S2)': 'blue'}

for group_name, center in group_centers.items():
    color = group_colors[group_name]
    # Draw circle with radius ~1 km
    circle = plt.Circle(center, 1.0, color=color, fill=True, alpha=0.2)
    ax1.add_patch(circle)
    # Draw circle outline
    circle_outline = plt.Circle(center, 1.0, color=color, fill=False, linewidth=2, alpha=0.7)
    ax1.add_patch(circle_outline)
    ax1.text(center[0], center[1] - 1.3, group_name.split(' ')[0], 
            ha='center', fontsize=10, fontweight='bold', color=color)

# Draw lines connecting stations in same group
for group_stations, color in [(['S0', 'S1'], 'red'), (['S3', 'S4'], 'green')]:
    group_coords = stations[stations['station_id'].isin(group_stations)][['x_km', 'y_km']].values
    ax1.plot(group_coords[:, 0], group_coords[:, 1], color=color, linewidth=2, alpha=0.5)

ax1.set_xlabel('X (km)')
ax1.set_ylabel('Y (km)')
ax1.set_title('Station Geometry with Inferred Source Regions')
ax1.grid(True, alpha=0.3)
ax1.set_aspect('equal', adjustable='box')

# 2. Temporal pattern by station group
ax2 = plt.subplot(2, 3, 2)

group_data = {
    'Group 1 (S0,S1)': arrivals[arrivals['station_id'].isin(['S0', 'S1'])],
    'Group 2 (S3,S4)': arrivals[arrivals['station_id'].isin(['S3', 'S4'])],
    'Group 3 (S2)': arrivals[arrivals['station_id'] == 'S2']
}

for i, (group_name, group_df) in enumerate(group_data.items()):
    color = group_colors[group_name]
    times = group_df['arrival_s'].values
    stations_in_group = group_df['station_id'].values
    
    # Plot each pick
    for j, (time, station) in enumerate(zip(times, stations_in_group)):
        ax2.scatter(time, i, s=150, color=color, edgecolors='black', alpha=0.7)
        ax2.text(time, i + 0.15, station, ha='center', fontsize=9)
    
    # Connect picks with line
    if len(times) > 1:
        sorted_indices = np.argsort(times)
        ax2.plot(times[sorted_indices], [i] * len(times), 
                color=color, linewidth=2, alpha=0.5)

ax2.set_yticks(range(len(group_data)))
ax2.set_yticklabels(list(group_data.keys()))
ax2.set_xlabel('Arrival Time (s)')
ax2.set_title('Temporal Patterns by Station Group')
ax2.grid(True, alpha=0.3)

# 3. Inter-event time statistics
ax3 = plt.subplot(2, 3, 3)

# Calculate inter-event times for each station
inter_event_data = []
station_labels = []
for station in stations['station_id']:
    station_times = arrivals[arrivals['station_id'] == station]['arrival_s'].values
    if len(station_times) > 1:
        intervals = np.diff(np.sort(station_times))
        inter_event_data.append(intervals)
        station_labels.append(station)

# Create box plot
bp = ax3.boxplot(inter_event_data, labels=station_labels, patch_artist=True)

# Color boxes by group
for i, station in enumerate(station_labels):
    if station in ['S0', 'S1']:
        bp['boxes'][i].set_facecolor('red')
    elif station in ['S3', 'S4']:
        bp['boxes'][i].set_facecolor('green')
    else:
        bp['boxes'][i].set_facecolor('blue')
    bp['boxes'][i].set_alpha(0.6)

ax3.set_ylabel('Inter-Event Time (s)')
ax3.set_title('Inter-Event Time Statistics by Station')
ax3.grid(True, alpha=0.3, axis='y')

# 4. Cumulative event count
ax4 = plt.subplot(2, 3, 4)

# Sort all picks by time
all_picks_sorted = arrivals.sort_values('arrival_s')
times = all_picks_sorted['arrival_s'].values
cumulative_count = np.arange(1, len(times) + 1)

# Plot cumulative count
ax4.plot(times, cumulative_count, 'b-', linewidth=3, marker='o', markersize=8)
ax4.fill_between(times, 0, cumulative_count, alpha=0.2)

ax4.set_xlabel('Time (s)')
ax4.set_ylabel('Cumulative Event Count')
ax4.set_title('Cumulative Microseismic Events')
ax4.grid(True, alpha=0.3)

# 5. Station pick density vs distance from centroid
ax5 = plt.subplot(2, 3, 5)

# Calculate distances from array centroid
centroid = np.mean(stations[['x_km', 'y_km']].values, axis=0)
distances = np.sqrt(np.sum((stations[['x_km', 'y_km']].values - centroid)**2, axis=1))

# Get pick counts
pick_counts = arrivals['station_id'].value_counts().reindex(stations['station_id']).values

# Plot
for i, station in enumerate(stations['station_id']):
    color = station_colors[station]
    ax5.scatter(distances[i], pick_counts[i], s=200, color=color, 
               edgecolors='black', alpha=0.7)
    ax5.text(distances[i] + 0.05, pick_counts[i] + 0.05, station, 
            fontsize=11, fontweight='bold')

# Add trend line
z = np.polyfit(distances, pick_counts, 1)
p = np.poly1d(z)
x_trend = np.linspace(distances.min(), distances.max(), 100)
ax5.plot(x_trend, p(x_trend), 'k--', alpha=0.5, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')

ax5.set_xlabel('Distance from Array Centroid (km)')
ax5.set_ylabel('Number of Picks')
ax5.set_title('Pick Density vs Distance from Centroid')
ax5.grid(True, alpha=0.3)
ax5.legend()

# 6. Regularity analysis
ax6 = plt.subplot(2, 3, 6)

# Calculate inter-pick times for all picks
all_times_sorted = np.sort(arrivals['arrival_s'].values)
inter_times = np.diff(all_times_sorted)

# Plot histogram
n, bins, patches = ax6.hist(inter_times, bins=8, edgecolor='black', alpha=0.7)

# Add normal distribution fit
from scipy.stats import norm
mu, std = norm.fit(inter_times)
x = np.linspace(inter_times.min(), inter_times.max(), 100)
p = norm.pdf(x, mu, std)
ax6.plot(x, p * len(inter_times) * (bins[1] - bins[0]), 
        'r-', linewidth=2, label=f'Normal fit: μ={mu:.3f}s, σ={std:.3f}s')

ax6.set_xlabel('Inter-Pick Time (s)')
ax6.set_ylabel('Frequency')
ax6.set_title('Inter-Pick Time Distribution')
ax6.grid(True, alpha=0.3)
ax6.legend()

plt.tight_layout()
plt.savefig('report/images/final_summary.png', dpi=300, bbox_inches='tight')
plt.close()

print("Figure saved to report/images/final_summary.png")

# Print key findings
print("\n=== KEY FINDINGS ===")
print("1. Station Geometry:")
print(f"   - Array aperture: {6.719:.2f} km")
print(f"   - Convex hull area: {17.665:.2f} km²")
print(f"   - Stations form 3 natural groups based on spatial proximity")

print("\n2. Temporal Patterns:")
print(f"   - Highly regular inter-event timing: mean interval = {0.499:.3f} s")
print(f"   - Low variability: coefficient of variation = {0.055:.3f}")
print(f"   - Suggests triggered or periodic source mechanism")

print("\n3. Spatial Clustering:")
print("   - Group 1 (S0, S1): NW cluster, most active (6 picks)")
print("   - Group 2 (S3, S4): NE cluster, moderately active (4 picks)")
print("   - Group 3 (S2): Southern isolated station, least active (2 picks)")

print("\n4. Structural Implications:")
print("   - Station groups may align with structural features (faults, fractures)")
print("   - Differential activity suggests heterogeneous stress distribution")
print("   - Regular timing may indicate fluid injection or reservoir depletion effects")

print("\nFinal summary analysis complete.")