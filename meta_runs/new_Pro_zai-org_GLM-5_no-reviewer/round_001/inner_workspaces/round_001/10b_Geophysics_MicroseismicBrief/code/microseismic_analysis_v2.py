import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
import os
import warnings
warnings.filterwarnings('ignore')

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load data
stations = pd.read_csv('../data/stations.csv')
arrivals = pd.read_csv('../data/arrival_times.csv')

print("="*60)
print("MICROSEISMIC MONITORING ANALYSIS")
print("="*60)
print("\n1. DATA OVERVIEW")
print("-"*40)
print(f"\nNumber of stations: {len(stations)}")
print(f"Number of arrival picks: {len(arrivals)}")

print("\nStation Coordinates:")
print(stations.to_string(index=False))

print("\nArrival Times:")
print(arrivals.to_string(index=False))

# Create station dictionary for easy access
station_coords = {row['station_id']: np.array([row['x_km'], row['y_km'], row['z_km']]) 
                  for _, row in stations.iterrows()}

# P-wave velocity model (typical for sedimentary basin)
V_P = 4.5  # km/s

print(f"\nAssumed P-wave velocity: {V_P} km/s")

# Re-interpret data: Each event is detected by all 5 stations
# The pattern shows 5-station cycles
n_stations = len(stations)
n_picks = len(arrivals)
n_events = n_picks // n_stations

print(f"\nRe-interpreting data structure:")
print(f"  Number of stations: {n_stations}")
print(f"  Total picks: {n_picks}")
print(f"  Inferred number of events: {n_events}")

# Reorganize arrival data by event
events_data = {}
for event_idx in range(n_events):
    start_idx = event_idx * n_stations
    end_idx = start_idx + n_stations
    event_picks = arrivals.iloc[start_idx:end_idx]
    
    events_data[event_idx] = {
        'stations': event_picks['station_id'].tolist(),
        'arrivals': event_picks['arrival_s'].values
    }

print("\nReorganized event data:")
for eid, data in events_data.items():
    print(f"  Event {eid}: stations {data['stations']}")
    print(f"           arrivals {data['arrivals']}")

# Event location using grid search and optimization
def calculate_travel_time(source_pos, station_pos, velocity):
    """Calculate travel time from source to station."""
    distance = np.linalg.norm(source_pos - station_pos)
    return distance / velocity

def location_residual(params, station_ids, arrival_times, station_coords, velocity):
    """Calculate residual for event location optimization."""
    x, y, z, origin_time = params
    source_pos = np.array([x, y, z])
    
    residuals = []
    for i, sta_id in enumerate(station_ids):
        sta_pos = station_coords[sta_id]
        travel_time = calculate_travel_time(source_pos, sta_pos, velocity)
        predicted_arrival = origin_time + travel_time
        residuals.append(arrival_times[i] - predicted_arrival)
    
    return np.sum(np.array(residuals)**2)

def locate_event(station_ids, arrival_times, station_coords, velocity, 
                 x_range=(0, 6), y_range=(0, 12), z_range=(-5, 0)):
    """Locate event using grid search followed by optimization."""
    # Grid search for initial estimate
    best_residual = np.inf
    best_params = None
    
    for x in np.linspace(x_range[0], x_range[1], 30):
        for y in np.linspace(y_range[0], y_range[1], 30):
            for z in np.linspace(z_range[0], z_range[1], 15):
                # Estimate origin time from first arrival
                min_travel = min([calculate_travel_time(np.array([x, y, z]), 
                                                        station_coords[sid], velocity)
                                  for sid in station_ids])
                origin_time = min(arrival_times) - min_travel
                
                params = [x, y, z, origin_time]
                residual = location_residual(params, station_ids, arrival_times, 
                                            station_coords, velocity)
                
                if residual < best_residual:
                    best_residual = residual
                    best_params = params
    
    # Refine with optimization
    result = minimize(location_residual, best_params,
                     args=(station_ids, arrival_times, station_coords, velocity),
                     method='L-BFGS-B',
                     bounds=[(0, 6), (0, 12), (-10, 0), (-10, 20)])
    
    return result.x, result.fun

print("\n" + "="*60)
print("2. EVENT LOCATION")
print("-"*40)

# Locate all events
event_locations = {}
for event_id, data in events_data.items():
    params, residual = locate_event(data['stations'], data['arrivals'], 
                                    station_coords, V_P)
    rms = np.sqrt(residual/len(data['stations']))
    event_locations[event_id] = {
        'x': params[0],
        'y': params[1],
        'z': params[2],
        'origin_time': params[3],
        'residual': residual,
        'rms': rms,
        'n_picks': len(data['stations'])
    }
    print(f"Event {event_id}: x={params[0]:.3f} km, y={params[1]:.3f} km, "
          f"z={params[2]:.3f} km, t0={params[3]:.3f} s, RMS={rms:.4f} s")

# Create DataFrame for event locations
events_df = pd.DataFrame.from_dict(event_locations, orient='index')
events_df.index.name = 'event_id'
events_df.to_csv('../outputs/event_locations.csv')

print("\nEvent locations saved to outputs/event_locations.csv")

# Statistical summary
print("\n" + "="*60)
print("3. SPATIAL STATISTICS")
print("-"*40)
print(f"\nX range: {events_df['x'].min():.3f} - {events_df['x'].max():.3f} km")
print(f"Y range: {events_df['y'].min():.3f} - {events_df['y'].max():.3f} km")
print(f"Z range: {events_df['z'].min():.3f} - {events_df['z'].max():.3f} km")
print(f"\nMean depth: {events_df['z'].mean():.3f} km")
print(f"Depth std: {events_df['z'].std():.3f} km")
print(f"\nMean location RMS: {events_df['rms'].mean():.4f} s")

# Cluster analysis
print("\n" + "="*60)
print("4. CLUSTER ANALYSIS")
print("-"*40)

# Prepare coordinates for clustering
coords = events_df[['x', 'y', 'z']].values

# Hierarchical clustering
linkage_matrix = linkage(coords, method='ward')

# Determine clusters (using distance threshold)
max_d = 0.5  # km threshold
cluster_labels = fcluster(linkage_matrix, max_d, criterion='distance')
events_df['cluster'] = cluster_labels

print(f"\nNumber of clusters identified: {len(np.unique(cluster_labels))}")
for clust in np.unique(cluster_labels):
    cluster_events = events_df[events_df['cluster'] == clust]
    print(f"\nCluster {clust}: {len(cluster_events)} events")
    print(f"  Centroid: ({cluster_events['x'].mean():.3f}, {cluster_events['y'].mean():.3f}, {cluster_events['z'].mean():.3f}) km")
    print(f"  Depth range: {cluster_events['z'].min():.3f} to {cluster_events['z'].max():.3f} km")
    print(f"  X extent: {cluster_events['x'].max() - cluster_events['x'].min():.3f} km")
    print(f"  Y extent: {cluster_events['y'].max() - cluster_events['y'].min():.3f} km")

# Save clustering results
events_df.to_csv('../outputs/event_locations_with_clusters.csv')

# Calculate inter-event distances
distances = pdist(coords)
print(f"\nInter-event distance statistics:")
print(f"  Mean: {np.mean(distances):.3f} km")
print(f"  Median: {np.median(distances):.3f} km")
print(f"  Min: {np.min(distances):.3f} km")
print(f"  Max: {np.max(distances):.3f} km")

# Temporal analysis
print("\n" + "="*60)
print("5. TEMPORAL ANALYSIS")
print("-"*40)

# Sort events by origin time
events_df_sorted = events_df.sort_values('origin_time')
print("\nEvents in chronological order:")
for idx, row in events_df_sorted.iterrows():
    print(f"  Event {idx}: t0 = {row['origin_time']:.4f} s, depth = {row['z']:.3f} km, cluster = {int(row['cluster'])}")

# Calculate time intervals
time_intervals = np.diff(events_df_sorted['origin_time'].values)
print(f"\nTime interval statistics:")
print(f"  Mean interval: {np.mean(time_intervals):.4f} s")
print(f"  Std interval: {np.std(time_intervals):.4f} s")
print(f"  Min interval: {np.min(time_intervals):.4f} s")
print(f"  Max interval: {np.max(time_intervals):.4f} s")

# Generate figures
print("\n" + "="*60)
print("6. GENERATING FIGURES")
print("-"*40)

# Figure 1: Station geometry and event locations (map view)
fig, ax = plt.subplots(figsize=(10, 8))

# Plot stations
ax.scatter(stations['x_km'], stations['y_km'], c='blue', s=200, marker='^', 
           edgecolors='black', linewidths=2, label='Stations', zorder=5)
for _, row in stations.iterrows():
    ax.annotate(row['station_id'], (row['x_km'], row['y_km']), 
                xytext=(5, 5), textcoords='offset points', fontsize=10, fontweight='bold')

# Plot events colored by cluster
colors = plt.cm.Set1(np.linspace(0, 1, len(np.unique(cluster_labels))))
for i, clust in enumerate(np.unique(cluster_labels)):
    cluster_events = events_df[events_df['cluster'] == clust]
    ax.scatter(cluster_events['x'], cluster_events['y'], c=[colors[i]], s=150, 
               marker='o', edgecolors='black', linewidths=1, 
               label=f'Cluster {clust}', alpha=0.8)

ax.set_xlabel('X (km)', fontsize=12)
ax.set_ylabel('Y (km)', fontsize=12)
ax.set_title('Microseismic Event Locations - Map View', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
ax.set_aspect('equal')

plt.tight_layout()
plt.savefig('../report/images/figure1_map_view.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure1_map_view.png")

# Figure 2: Cross-section view (X-Z)
fig, ax = plt.subplots(figsize=(10, 6))

# Plot events
for i, clust in enumerate(np.unique(cluster_labels)):
    cluster_events = events_df[events_df['cluster'] == clust]
    ax.scatter(cluster_events['x'], cluster_events['z'], c=[colors[i]], s=150, 
               marker='o', edgecolors='black', linewidths=1, 
               label=f'Cluster {clust}', alpha=0.8)

# Add surface line
ax.axhline(y=0, color='brown', linestyle='--', linewidth=2, label='Surface')

ax.set_xlabel('X (km)', fontsize=12)
ax.set_ylabel('Depth (km)', fontsize=12)
ax.set_title('Microseismic Event Locations - Cross Section (X-Z)', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('../report/images/figure2_cross_section_xz.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure2_cross_section_xz.png")

# Figure 3: Cross-section view (Y-Z)
fig, ax = plt.subplots(figsize=(10, 6))

for i, clust in enumerate(np.unique(cluster_labels)):
    cluster_events = events_df[events_df['cluster'] == clust]
    ax.scatter(cluster_events['y'], cluster_events['z'], c=[colors[i]], s=150, 
               marker='o', edgecolors='black', linewidths=1, 
               label=f'Cluster {clust}', alpha=0.8)

ax.axhline(y=0, color='brown', linestyle='--', linewidth=2, label='Surface')

ax.set_xlabel('Y (km)', fontsize=12)
ax.set_ylabel('Depth (km)', fontsize=12)
ax.set_title('Microseismic Event Locations - Cross Section (Y-Z)', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('../report/images/figure3_cross_section_yz.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure3_cross_section_yz.png")

# Figure 4: 3D view
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure(figsize=(12, 9))
ax = fig.add_subplot(111, projection='3d')

# Plot stations
ax.scatter(stations['x_km'], stations['y_km'], stations['z_km'], 
           c='blue', s=200, marker='^', edgecolors='black', linewidths=2, label='Stations')

# Plot events
for i, clust in enumerate(np.unique(cluster_labels)):
    cluster_events = events_df[events_df['cluster'] == clust]
    ax.scatter(cluster_events['x'], cluster_events['y'], cluster_events['z'], 
               c=[colors[i]], s=100, marker='o', edgecolors='black', linewidths=1, 
               label=f'Cluster {clust}', alpha=0.8)

ax.set_xlabel('X (km)', fontsize=10)
ax.set_ylabel('Y (km)', fontsize=10)
ax.set_zlabel('Depth (km)', fontsize=10)
ax.set_title('3D View of Microseismic Events and Stations', fontsize=14)
ax.legend(loc='upper left')

# Invert Z axis for depth
ax.invert_zaxis()

plt.tight_layout()
plt.savefig('../report/images/figure4_3d_view.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure4_3d_view.png")

# Figure 5: Depth distribution histogram
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(events_df['z'], bins=10, edgecolor='black', alpha=0.7, color='steelblue')
ax.axvline(x=events_df['z'].mean(), color='red', linestyle='--', linewidth=2, 
           label=f'Mean: {events_df["z"].mean():.3f} km')
ax.set_xlabel('Depth (km)', fontsize=12)
ax.set_ylabel('Number of Events', fontsize=12)
ax.set_title('Event Depth Distribution', fontsize=14)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/figure5_depth_histogram.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure5_depth_histogram.png")

# Figure 6: Temporal evolution
fig, axes = plt.subplots(2, 1, figsize=(10, 8))

# Sort by origin time
events_sorted = events_df.sort_values('origin_time')

# Plot 1: Origin time sequence
ax1 = axes[0]
event_nums = range(len(events_sorted))
scatter1 = ax1.scatter(events_sorted['origin_time'], event_nums, 
                       c=events_sorted['cluster'], cmap='Set1', s=150, 
                       edgecolors='black', linewidths=1)
ax1.set_xlabel('Origin Time (s)', fontsize=12)
ax1.set_ylabel('Event Sequence', fontsize=12)
ax1.set_title('Temporal Evolution of Events', fontsize=14)
ax1.grid(True, alpha=0.3)

# Plot 2: Depth vs time
ax2 = axes[1]
scatter2 = ax2.scatter(events_sorted['origin_time'], events_sorted['z'], 
                       c=events_sorted['cluster'], cmap='Set1', s=150, 
                       edgecolors='black', linewidths=1)
ax2.set_xlabel('Origin Time (s)', fontsize=12)
ax2.set_ylabel('Depth (km)', fontsize=12)
ax2.set_title('Event Depth vs Time', fontsize=14)
ax2.invert_yaxis()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/figure6_temporal_evolution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure6_temporal_evolution.png")

# Figure 7: Cluster dendrogram
fig, ax = plt.subplots(figsize=(10, 6))
dendrogram(linkage_matrix, ax=ax, labels=[f'E{i}' for i in range(len(coords))])
ax.axhline(y=max_d, color='red', linestyle='--', linewidth=2, 
           label=f'Cluster threshold: {max_d} km')
ax.set_xlabel('Event', fontsize=12)
ax.set_ylabel('Distance (km)', fontsize=12)
ax.set_title('Hierarchical Clustering Dendrogram', fontsize=14)
ax.legend()

plt.tight_layout()
plt.savefig('../report/images/figure7_dendrogram.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure7_dendrogram.png")

# Figure 8: Location uncertainty (RMS residual)
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(range(len(events_df)), events_df['rms'], color='steelblue', edgecolor='black')
ax.axhline(y=events_df['rms'].mean(), color='red', linestyle='--', linewidth=2, 
           label=f'Mean RMS: {events_df["rms"].mean():.4f} s')
ax.set_xlabel('Event ID', fontsize=12)
ax.set_ylabel('RMS Residual (s)', fontsize=12)
ax.set_title('Event Location Quality (RMS Residual)', fontsize=14)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/figure8_location_quality.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure8_location_quality.png")

# Figure 9: Spatial distribution with cluster ellipses
fig, ax = plt.subplots(figsize=(10, 8))

# Plot stations
ax.scatter(stations['x_km'], stations['y_km'], c='blue', s=200, marker='^', 
           edgecolors='black', linewidths=2, label='Stations', zorder=5)
for _, row in stations.iterrows():
    ax.annotate(row['station_id'], (row['x_km'], row['y_km']), 
                xytext=(5, 5), textcoords='offset points', fontsize=10, fontweight='bold')

# Plot events with cluster hulls
from scipy.spatial import ConvexHull
for i, clust in enumerate(np.unique(cluster_labels)):
    cluster_events = events_df[events_df['cluster'] == clust]
    ax.scatter(cluster_events['x'], cluster_events['y'], c=[colors[i]], s=150, 
               marker='o', edgecolors='black', linewidths=1, 
               label=f'Cluster {clust}', alpha=0.8)
    
    # Draw convex hull if more than 2 points
    if len(cluster_events) >= 3:
        points = cluster_events[['x', 'y']].values
        hull = ConvexHull(points)
        for simplex in hull.simplices:
            ax.plot(points[simplex, 0], points[simplex, 1], 
                    color=colors[i], alpha=0.5, linewidth=2)

ax.set_xlabel('X (km)', fontsize=12)
ax.set_ylabel('Y (km)', fontsize=12)
ax.set_title('Event Clusters with Spatial Extent', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
ax.set_aspect('equal')

plt.tight_layout()
plt.savefig('../report/images/figure9_cluster_extent.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure9_cluster_extent.png")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print(f"\nResults saved to:")
print(f"  - outputs/event_locations.csv")
print(f"  - outputs/event_locations_with_clusters.csv")
print(f"  - report/images/ (9 figures)")
