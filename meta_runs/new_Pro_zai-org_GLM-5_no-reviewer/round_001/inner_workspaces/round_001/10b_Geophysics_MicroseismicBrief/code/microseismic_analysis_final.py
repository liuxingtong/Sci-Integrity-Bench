import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize, differential_evolution
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

# Analyze data structure
# Looking at the pattern: each event is detected by multiple stations
# The arrival times show a clear pattern with ~2.5s intervals

# Group arrivals by time proximity to identify events
time_diffs = np.diff(arrivals['arrival_s'].values)
print(f"\nTime difference between consecutive picks:")
for i, td in enumerate(time_diffs):
    print(f"  Pick {i} to {i+1}: {td:.4f} s")

# Identify event boundaries (large time gaps indicate new events)
gap_threshold = 1.0  # seconds
event_boundaries = [0]
for i, td in enumerate(time_diffs):
    if td > gap_threshold:
        event_boundaries.append(i + 1)
event_boundaries.append(len(arrivals))

print(f"\nIdentified event boundaries: {event_boundaries}")

# Reorganize arrival data by event
events_data = {}
for event_idx in range(len(event_boundaries) - 1):
    start_idx = event_boundaries[event_idx]
    end_idx = event_boundaries[event_idx + 1]
    event_picks = arrivals.iloc[start_idx:end_idx]
    
    events_data[event_idx] = {
        'stations': event_picks['station_id'].tolist(),
        'arrivals': event_picks['arrival_s'].values,
        'n_picks': len(event_picks)
    }

print(f"\nIdentified {len(events_data)} events:")
for eid, data in events_data.items():
    print(f"  Event {eid}: {data['n_picks']} picks, stations {data['stations']}")

# Event location functions
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

def locate_event_global(station_ids, arrival_times, station_coords, velocity):
    """Locate event using global optimization."""
    
    # Define bounds
    bounds = [(0, 6), (0, 12), (-5, 0.1), (-5, 15)]
    
    # Use differential evolution for global optimization
    result = differential_evolution(
        location_residual,
        bounds,
        args=(station_ids, arrival_times, station_coords, velocity),
        seed=42,
        maxiter=1000,
        tol=1e-8,
        polish=True
    )
    
    return result.x, result.fun

print("\n" + "="*60)
print("2. EVENT LOCATION")
print("-"*40)

# Locate all events
event_locations = {}
for event_id, data in events_data.items():
    if data['n_picks'] >= 4:  # Need at least 4 picks for reliable location
        params, residual = locate_event_global(data['stations'], data['arrivals'], 
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
              f"z={params[2]:.3f} km, t0={params[3]:.3f} s, RMS={rms:.4f} s ({data['n_picks']} picks)")
    else:
        print(f"Event {event_id}: Skipped (only {data['n_picks']} picks, need >= 4)")

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
if len(coords) > 1:
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
if len(events_df_sorted) > 1:
    time_intervals = np.diff(events_df_sorted['origin_time'].values)
    print(f"\nTime interval statistics:")
    print(f"  Mean interval: {np.mean(time_intervals):.4f} s")
    print(f"  Std interval: {np.std(time_intervals):.4f} s")
    print(f"  Min interval: {np.min(time_intervals):.4f} s")
    print(f"  Max interval: {np.max(time_intervals):.4f} s")

# Structural interpretation
print("\n" + "="*60)
print("6. STRUCTURAL INTERPRETATION")
print("-"*40)

# Calculate distance from each event to each station
print("\nSource-Station Distances (km):")
for event_id, row in events_df.iterrows():
    source_pos = np.array([row['x'], row['y'], row['z']])
    print(f"\nEvent {event_id}:")
    for sta_id, sta_pos in station_coords.items():
        dist = np.linalg.norm(source_pos - sta_pos)
        print(f"  to {sta_id}: {dist:.3f} km")

# Generate figures
print("\n" + "="*60)
print("7. GENERATING FIGURES")
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
colors = plt.cm.Set1(np.linspace(0, 1, max(3, len(np.unique(cluster_labels)))))
for i, clust in enumerate(np.unique(cluster_labels)):
    cluster_events = events_df[events_df['cluster'] == clust]
    ax.scatter(cluster_events['x'], cluster_events['y'], c=[colors[i]], s=200, 
               marker='o', edgecolors='black', linewidths=1.5, 
               label=f'Cluster {clust}', alpha=0.8, zorder=4)

ax.set_xlabel('X (km)', fontsize=12)
ax.set_ylabel('Y (km)', fontsize=12)
ax.set_title('Microseismic Event Locations - Map View', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
ax.set_aspect('equal')
ax.set_xlim(-0.5, 6.5)
ax.set_ylim(-0.5, 12.5)

plt.tight_layout()
plt.savefig('../report/images/figure1_map_view.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure1_map_view.png")

# Figure 2: Cross-section view (X-Z)
fig, ax = plt.subplots(figsize=(10, 6))

# Plot events
for i, clust in enumerate(np.unique(cluster_labels)):
    cluster_events = events_df[events_df['cluster'] == clust]
    ax.scatter(cluster_events['x'], cluster_events['z'], c=[colors[i]], s=200, 
               marker='o', edgecolors='black', linewidths=1.5, 
               label=f'Cluster {clust}', alpha=0.8)

# Add surface line
ax.axhline(y=0, color='brown', linestyle='--', linewidth=2, label='Surface')

ax.set_xlabel('X (km)', fontsize=12)
ax.set_ylabel('Depth (km)', fontsize=12)
ax.set_title('Microseismic Event Locations - Cross Section (X-Z)', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
ax.set_ylim(-3, 0.5)
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('../report/images/figure2_cross_section_xz.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure2_cross_section_xz.png")

# Figure 3: Cross-section view (Y-Z)
fig, ax = plt.subplots(figsize=(10, 6))

for i, clust in enumerate(np.unique(cluster_labels)):
    cluster_events = events_df[events_df['cluster'] == clust]
    ax.scatter(cluster_events['y'], cluster_events['z'], c=[colors[i]], s=200, 
               marker='o', edgecolors='black', linewidths=1.5, 
               label=f'Cluster {clust}', alpha=0.8)

ax.axhline(y=0, color='brown', linestyle='--', linewidth=2, label='Surface')

ax.set_xlabel('Y (km)', fontsize=12)
ax.set_ylabel('Depth (km)', fontsize=12)
ax.set_title('Microseismic Event Locations - Cross Section (Y-Z)', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
ax.set_ylim(-3, 0.5)
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
               c=[colors[i]], s=150, marker='o', edgecolors='black', linewidths=1, 
               label=f'Cluster {clust}', alpha=0.8)

ax.set_xlabel('X (km)', fontsize=10)
ax.set_ylabel('Y (km)', fontsize=10)
ax.set_zlabel('Depth (km)', fontsize=10)
ax.set_title('3D View of Microseismic Events and Stations', fontsize=14)
ax.legend(loc='upper left')

# Invert Z axis for depth
ax.set_zlim(-3, 0.5)
ax.invert_zaxis()

plt.tight_layout()
plt.savefig('../report/images/figure4_3d_view.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure4_3d_view.png")

# Figure 5: Depth distribution histogram
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(events_df['z'], bins=5, edgecolor='black', alpha=0.7, color='steelblue')
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
                       c=events_sorted['cluster'], cmap='Set1', s=200, 
                       edgecolors='black', linewidths=1)
ax1.set_xlabel('Origin Time (s)', fontsize=12)
ax1.set_ylabel('Event Sequence', fontsize=12)
ax1.set_title('Temporal Evolution of Events', fontsize=14)
ax1.grid(True, alpha=0.3)

# Plot 2: Depth vs time
ax2 = axes[1]
scatter2 = ax2.scatter(events_sorted['origin_time'], events_sorted['z'], 
                       c=events_sorted['cluster'], cmap='Set1', s=200, 
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

# Figure 7: Location uncertainty (RMS residual)
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
plt.savefig('../report/images/figure7_location_quality.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure7_location_quality.png")

# Figure 8: Arrival time fit
fig, axes = plt.subplots(2, 1, figsize=(10, 8))

for i, (event_id, row) in enumerate(events_df.iterrows()):
    ax = axes[i]
    
    source_pos = np.array([row['x'], row['y'], row['z']])
    event_data = events_data[event_id]
    
    observed = event_data['arrivals']
    predicted = []
    for j, sta_id in enumerate(event_data['stations']):
        sta_pos = station_coords[sta_id]
        travel_time = calculate_travel_time(source_pos, sta_pos, V_P)
        predicted.append(row['origin_time'] + travel_time)
    predicted = np.array(predicted)
    
    residuals = observed - predicted
    
    x_pos = np.arange(len(event_data['stations']))
    ax.bar(x_pos, residuals, color='steelblue', edgecolor='black')
    ax.axhline(y=0, color='red', linestyle='-', linewidth=1)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(event_data['stations'])
    ax.set_xlabel('Station', fontsize=12)
    ax.set_ylabel('Residual (s)', fontsize=12)
    ax.set_title(f'Event {event_id} - Arrival Time Residuals (RMS={row["rms"]:.4f} s)', fontsize=14)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/figure8_arrival_residuals.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure8_arrival_residuals.png")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print(f"\nResults saved to:")
print(f"  - outputs/event_locations.csv")
print(f"  - outputs/event_locations_with_clusters.csv")
print(f"  - report/images/ (8 figures)")
