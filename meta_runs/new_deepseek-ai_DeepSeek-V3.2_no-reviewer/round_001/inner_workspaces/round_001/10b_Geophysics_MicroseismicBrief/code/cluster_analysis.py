import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN
from scipy.spatial.distance import cdist
import os

# Load data
stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

print("=== Microseismic Cluster Analysis ===")

# Create a feature matrix for clustering
# We'll use arrival time and station position as features
station_coords = {row['station_id']: (row['x_km'], row['y_km']) 
                  for _, row in stations.iterrows()}

# Create feature vectors: [arrival_time, x_station, y_station]
features = []
for _, row in arrivals.iterrows():
    station = row['station_id']
    x, y = station_coords[station]
    features.append([row['arrival_s'], x, y])

features = np.array(features)
print(f"Feature matrix shape: {features.shape}")

# Normalize features
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

# Try K-means clustering
print("\n=== K-means Clustering ===")
for n_clusters in [2, 3, 4, 5]:
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(features_scaled)
    
    print(f"\nK-means with {n_clusters} clusters:")
    for i in range(n_clusters):
        cluster_mask = cluster_labels == i
        cluster_size = np.sum(cluster_mask)
        cluster_times = features[cluster_mask, 0]
        cluster_stations = arrivals['station_id'].iloc[np.where(cluster_mask)[0]].tolist()
        print(f"  Cluster {i}: {cluster_size} picks, time range: {cluster_times.min():.3f}-{cluster_times.max():.3f} s")
        print(f"    Stations: {cluster_stations}")

# Try DBSCAN with different parameters
print("\n=== DBSCAN Clustering ===")
dbscan = DBSCAN(eps=0.8, min_samples=2)
dbscan_labels = dbscan.fit_predict(features_scaled)
n_clusters = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)
n_noise = list(dbscan_labels).count(-1)
print(f"DBSCAN results: {n_clusters} clusters, {n_noise} noise points")
for i in set(dbscan_labels):
    if i == -1:
        continue
    cluster_mask = dbscan_labels == i
    cluster_size = np.sum(cluster_mask)
    cluster_times = features[cluster_mask, 0]
    cluster_stations = arrivals['station_id'].iloc[np.where(cluster_mask)[0]].tolist()
    print(f"  Cluster {i}: {cluster_size} picks, time range: {cluster_times.min():.3f}-{cluster_times.max():.3f} s")
    print(f"    Stations: {cluster_stations}")

# Visualize clustering results
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# 1. Station locations with pick times as color
ax1 = axes[0, 0]
scatter1 = ax1.scatter(stations['x_km'], stations['y_km'], 
                      s=200, c='gray', marker='^', edgecolors='black', label='Stations')
for i, row in stations.iterrows():
    ax1.text(row['x_km'] + 0.15, row['y_km'] + 0.15, row['station_id'], 
            fontsize=11, fontweight='bold')

# Plot picks colored by arrival time
arrival_times = arrivals['arrival_s'].values
norm = plt.Normalize(arrival_times.min(), arrival_times.max())
cmap = plt.cm.viridis

for _, row in arrivals.iterrows():
    station = row['station_id']
    x, y = station_coords[station]
    color = cmap(norm(row['arrival_s']))
    ax1.scatter(x, y, s=100, color=color, alpha=0.7, edgecolors='black')

# Add colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax1)
cbar.set_label('Arrival Time (s)')

ax1.set_xlabel('X (km)')
ax1.set_ylabel('Y (km)')
ax1.set_title('Station Locations with Arrival Times')
ax1.grid(True, alpha=0.3)
ax1.set_aspect('equal', adjustable='box')

# 2. K-means clustering (using 3 clusters)
ax2 = axes[0, 1]
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(features_scaled)

colors = ['red', 'blue', 'green', 'orange', 'purple']
for i in range(3):
    cluster_mask = cluster_labels == i
    cluster_data = features[cluster_mask]
    if len(cluster_data) > 0:
        ax2.scatter(cluster_data[:, 1], cluster_data[:, 2], 
                   s=100, color=colors[i], alpha=0.7, 
                   edgecolors='black', label=f'Cluster {i}')

# Plot stations
ax2.scatter(stations['x_km'], stations['y_km'], 
           s=200, c='gray', marker='^', edgecolors='black', alpha=0.5)
for i, row in stations.iterrows():
    ax2.text(row['x_km'] + 0.15, row['y_km'] + 0.15, row['station_id'], 
            fontsize=11, fontweight='bold')

ax2.set_xlabel('X (km)')
ax2.set_ylabel('Y (km)')
ax2.set_title('K-means Clustering (3 clusters)')
ax2.grid(True, alpha=0.3)
ax2.legend()
ax2.set_aspect('equal', adjustable='box')

# 3. Arrival time sequence with clustering
ax3 = axes[1, 0]
for i in range(3):
    cluster_mask = cluster_labels == i
    cluster_indices = np.where(cluster_mask)[0]
    cluster_times = features[cluster_mask, 0]
    cluster_event_ids = arrivals['event_id'].iloc[cluster_indices]
    
    ax3.scatter(cluster_event_ids, cluster_times, 
               s=100, color=colors[i], alpha=0.7, 
               edgecolors='black', label=f'Cluster {i}')

ax3.set_xlabel('Event ID')
ax3.set_ylabel('Arrival Time (s)')
ax3.set_title('Temporal Pattern with Clustering')
ax3.grid(True, alpha=0.3)
ax3.legend()

# 4. Inter-event time analysis by station
ax4 = axes[1, 1]
stations_list = stations['station_id'].tolist()
station_colors = plt.cm.tab10(np.linspace(0, 1, len(stations_list)))

for idx, station in enumerate(stations_list):
    station_data = arrivals[arrivals['station_id'] == station]
    if len(station_data) > 1:
        times = station_data['arrival_s'].values
        event_ids = station_data['event_id'].values
        
        # Plot arrival times
        ax4.scatter(event_ids, times, 
                   color=station_colors[idx], s=80, 
                   label=station, alpha=0.7)
        
        # Connect points with lines
        ax4.plot(event_ids, times, 
                color=station_colors[idx], alpha=0.5, linestyle='-', linewidth=1)

ax4.set_xlabel('Event ID')
ax4.set_ylabel('Arrival Time (s)')
ax4.set_title('Station-specific Temporal Patterns')
ax4.grid(True, alpha=0.3)
ax4.legend()

plt.tight_layout()
plt.savefig('report/images/cluster_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nFigure saved to report/images/cluster_analysis.png")

# Analyze temporal patterns
print("\n=== Temporal Pattern Analysis ===")
# Calculate average time between picks at each station
for station in stations_list:
    station_data = arrivals[arrivals['station_id'] == station]
    if len(station_data) > 1:
        times = station_data['arrival_s'].values
        intervals = np.diff(times)
        print(f"Station {station}: {len(station_data)} picks, "
              f"avg interval: {np.mean(intervals):.3f} s, "
              f"std: {np.std(intervals):.3f} s")

# Look for periodicity
print("\n=== Periodicity Analysis ===")
all_times = arrivals['arrival_s'].values
all_times_sorted = np.sort(all_times)
intervals_all = np.diff(all_times_sorted)
print(f"All picks: mean interval = {np.mean(intervals_all):.3f} s, "
      f"std = {np.std(intervals_all):.3f} s")
print(f"Coefficient of variation: {np.std(intervals_all)/np.mean(intervals_all):.3f}")

# Check if intervals are multiples of a base period
base_period = np.mean(intervals_all)
print(f"\nBase period (mean interval): {base_period:.3f} s")
print("Checking if intervals are multiples of base period:")
for i, interval in enumerate(intervals_all):
    multiple = interval / base_period
    nearest_int = round(multiple)
    error = abs(multiple - nearest_int)
    print(f"  Interval {i}: {interval:.3f} s = {multiple:.2f} × base, "
          f"nearest integer: {nearest_int}, error: {error:.3f}")

print("\nCluster analysis complete.")