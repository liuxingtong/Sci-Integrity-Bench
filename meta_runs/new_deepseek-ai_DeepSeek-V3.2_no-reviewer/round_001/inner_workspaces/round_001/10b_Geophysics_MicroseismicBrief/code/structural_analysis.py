import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay, ConvexHull
from scipy.interpolate import griddata
import os

# Load data
stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

print("=== Structural Context Analysis ===")

# Calculate station geometry metrics
coords = stations[['x_km', 'y_km']].values

# 1. Convex hull of stations
hull = ConvexHull(coords)
print(f"\nStation array convex hull:")
print(f"  Area: {hull.area:.3f} km²")
print(f"  Perimeter: {hull.area:.3f} km")
print(f"  Number of vertices: {len(hull.vertices)}")

# 2. Delaunay triangulation (shows station connectivity)
tri = Delaunay(coords)
print(f"\nDelaunay triangulation:")
print(f"  Number of triangles: {len(tri.simplices)}")

# 3. Calculate array aperture (maximum station separation)
from scipy.spatial.distance import pdist
distances = pdist(coords)
max_dist = np.max(distances)
min_dist = np.min(distances)
mean_dist = np.mean(distances)
print(f"\nStation separation statistics:")
print(f"  Maximum distance: {max_dist:.3f} km (array aperture)")
print(f"  Minimum distance: {min_dist:.3f} km")
print(f"  Mean distance: {mean_dist:.3f} km")

# 4. Calculate array centroid and station distances from centroid
centroid = np.mean(coords, axis=0)
dist_to_centroid = np.sqrt(np.sum((coords - centroid)**2, axis=1))
print(f"\nArray centroid: ({centroid[0]:.3f}, {centroid[1]:.3f}) km")
print("Distances from centroid:")
for i, station in enumerate(stations['station_id']):
    print(f"  {station}: {dist_to_centroid[i]:.3f} km")

# 5. Analyze spatial distribution of picks
# Create a grid for density estimation
x_min, x_max = stations['x_km'].min() - 1, stations['x_km'].max() + 1
y_min, y_max = stations['y_km'].min() - 1, stations['y_km'].max() + 1

nx, ny = 100, 100
x_grid = np.linspace(x_min, x_max, nx)
y_grid = np.linspace(y_min, y_max, ny)
X, Y = np.meshgrid(x_grid, y_grid)

# Assign each pick to its station coordinates
pick_coords = []
for _, row in arrivals.iterrows():
    station = row['station_id']
    station_row = stations[stations['station_id'] == station].iloc[0]
    pick_coords.append([station_row['x_km'], station_row['y_km'], row['arrival_s']])

pick_coords = np.array(pick_coords)

# Create figure for structural analysis
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# 1. Station geometry with convex hull and Delaunay triangulation
ax1 = axes[0, 0]

# Plot stations
ax1.scatter(stations['x_km'], stations['y_km'], s=200, c='red', 
           marker='^', edgecolors='black', label='Stations', zorder=5)
for i, row in stations.iterrows():
    ax1.text(row['x_km'] + 0.15, row['y_km'] + 0.15, row['station_id'], 
            fontsize=12, fontweight='bold')

# Plot convex hull
for simplex in hull.simplices:
    ax1.plot(coords[simplex, 0], coords[simplex, 1], 'k-', alpha=0.5)

# Plot Delaunay triangulation
ax1.triplot(coords[:, 0], coords[:, 1], tri.simplices, 'b-', alpha=0.3, linewidth=1)

# Plot centroid
ax1.scatter(centroid[0], centroid[1], s=300, c='green', marker='*', 
           edgecolors='black', label='Array Centroid', zorder=10)
ax1.text(centroid[0] + 0.2, centroid[1] + 0.2, 'Centroid', fontsize=11, fontweight='bold')

ax1.set_xlabel('X (km)')
ax1.set_ylabel('Y (km)')
ax1.set_title('Station Geometry: Convex Hull & Delaunay Triangulation')
ax1.grid(True, alpha=0.3)
ax1.legend(loc='upper right')
ax1.set_aspect('equal', adjustable='box')

# 2. Pick density by station
ax2 = axes[0, 1]

# Count picks per station
pick_counts = arrivals['station_id'].value_counts().reindex(stations['station_id']).fillna(0)

# Create bar chart
bars = ax2.bar(range(len(pick_counts)), pick_counts.values, 
              color=plt.cm.viridis(np.linspace(0, 1, len(pick_counts))),
              edgecolor='black')

# Add value labels on bars
for i, (bar, count) in enumerate(zip(bars, pick_counts.values)):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
            str(int(count)), ha='center', va='bottom', fontweight='bold')

ax2.set_xlabel('Station')
ax2.set_ylabel('Number of Picks')
ax2.set_title('Pick Counts by Station')
ax2.set_xticks(range(len(pick_counts)))
ax2.set_xticklabels(pick_counts.index)
ax2.grid(True, alpha=0.3, axis='y')

# 3. Temporal evolution of picks at each station
ax3 = axes[1, 0]

stations_list = stations['station_id'].tolist()
station_colors = plt.cm.Set1(np.linspace(0, 1, len(stations_list)))

for idx, station in enumerate(stations_list):
    station_data = arrivals[arrivals['station_id'] == station]
    if len(station_data) > 0:
        times = station_data['arrival_s'].values
        # Plot each pick
        ax3.scatter(times, [idx] * len(times), 
                   color=station_colors[idx], s=100, 
                   label=station, alpha=0.7, edgecolors='black')
        # Connect picks from same station
        if len(times) > 1:
            ax3.plot(times, [idx] * len(times), 
                    color=station_colors[idx], alpha=0.5, linewidth=2)

ax3.set_xlabel('Arrival Time (s)')
ax3.set_ylabel('Station')
ax3.set_title('Temporal Evolution of Picks by Station')
ax3.set_yticks(range(len(stations_list)))
ax3.set_yticklabels(stations_list)
ax3.grid(True, alpha=0.3)
ax3.legend(loc='upper right')

# 4. Spatial-temporal pattern
ax4 = axes[1, 1]

# Color picks by arrival time
arrival_times = pick_coords[:, 2]
norm = plt.Normalize(arrival_times.min(), arrival_times.max())
cmap = plt.cm.plasma

# Plot picks colored by time
scatter = ax4.scatter(pick_coords[:, 0], pick_coords[:, 1], 
                     s=150, c=arrival_times, cmap=cmap, norm=norm,
                     edgecolors='black', alpha=0.8, zorder=5)

# Plot stations
ax4.scatter(stations['x_km'], stations['y_km'], s=200, c='gray', 
           marker='^', edgecolors='black', alpha=0.5, label='Stations')

# Add station labels
for i, row in stations.iterrows():
    ax4.text(row['x_km'] + 0.15, row['y_km'] + 0.15, row['station_id'], 
            fontsize=11, fontweight='bold')

# Add colorbar
cbar = plt.colorbar(scatter, ax=ax4)
cbar.set_label('Arrival Time (s)')

# Draw lines connecting picks in temporal order
sorted_indices = np.argsort(arrival_times)
sorted_coords = pick_coords[sorted_indices]
ax4.plot(sorted_coords[:, 0], sorted_coords[:, 1], 'k--', alpha=0.3, linewidth=1)

ax4.set_xlabel('X (km)')
ax4.set_ylabel('Y (km)')
ax4.set_title('Spatial-Temporal Pattern of Picks')
ax4.grid(True, alpha=0.3)
ax4.legend(loc='upper right')
ax4.set_aspect('equal', adjustable='box')

plt.tight_layout()
plt.savefig('report/images/structural_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("Figure saved to report/images/structural_analysis.png")

# Additional analysis: infer possible source regions
print("\n=== Inferred Source Region Analysis ===")

# Based on pick patterns, we can infer:
# 1. Stations S0 and S1 have the most picks (3 each) and show similar temporal patterns
# 2. Stations S3 and S4 are spatially close (2.3 km apart) and show correlated picks
# 3. Station S2 is isolated with only 2 picks

# Calculate mean position of station groups
group1 = stations[stations['station_id'].isin(['S0', 'S1'])]
group2 = stations[stations['station_id'].isin(['S3', 'S4'])]
group3 = stations[stations['station_id'] == 'S2']

centroid1 = np.mean(group1[['x_km', 'y_km']].values, axis=0)
centroid2 = np.mean(group2[['x_km', 'y_km']].values, axis=0)
centroid3 = group3[['x_km', 'y_km']].values[0]

print(f"\nStation groups and centroids:")
print(f"  Group 1 (S0, S1): centroid at ({centroid1[0]:.3f}, {centroid1[1]:.3f}) km")
print(f"  Group 2 (S3, S4): centroid at ({centroid2[0]:.3f}, {centroid2[1]:.3f}) km")
print(f"  Group 3 (S2): at ({centroid3[0]:.3f}, {centroid3[1]:.3f}) km")

# Calculate distances between groups
dist_1_2 = np.sqrt(np.sum((centroid1 - centroid2)**2))
dist_1_3 = np.sqrt(np.sum((centroid1 - centroid3)**2))
dist_2_3 = np.sqrt(np.sum((centroid2 - centroid3)**2))

print(f"\nDistances between group centroids:")
print(f"  Group 1 - Group 2: {dist_1_2:.3f} km")
print(f"  Group 1 - Group 3: {dist_1_3:.3f} km")
print(f"  Group 2 - Group 3: {dist_2_3:.3f} km")

# Temporal analysis of groups
print(f"\nTemporal patterns by station group:")
for group_name, station_ids in [('Group 1', ['S0', 'S1']), 
                                ('Group 2', ['S3', 'S4']), 
                                ('Group 3', ['S2'])]:
    group_picks = arrivals[arrivals['station_id'].isin(station_ids)]
    times = group_picks['arrival_s'].values
    if len(times) > 1:
        intervals = np.diff(np.sort(times))
        print(f"  {group_name}: {len(times)} picks, "
              f"mean interval: {np.mean(intervals):.3f} s, "
              f"time span: {times.max() - times.min():.3f} s")
    else:
        print(f"  {group_name}: {len(times)} picks")

print("\nStructural analysis complete.")