"""
Microseismic Monitoring Analysis
================================
Source location and clustering analysis using arrival time picks and station geometry.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import cdist
import warnings
warnings.filterwarnings('ignore')

# Load data
stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

print("=== STATION GEOMETRY ===")
print(stations)
print(f"\nNumber of stations: {len(stations)}")

print("\n=== ARRIVAL TIME DATA ===")
print(arrivals)
print(f"\nTotal picks: {len(arrivals)}")

# Build station coordinate dictionary
station_coords = {}
for _, row in stations.iterrows():
    station_coords[row['station_id']] = np.array([row['x_km'], row['y_km'], row['z_km']])

# The arrival data structure:
# - Rows 0-4: Event 0 at stations S0, S1, S2, S3, S4
# - Rows 5-9: Event 1 at stations S0, S1, S2, S3, S4
# - Rows 10-11: Event 2 at stations S0, S1 (incomplete)

# Group picks into events (every 5 picks = 1 event, but last one is incomplete)
event_groups = []

# Event 0: picks 0-4
event_groups.append(arrivals.iloc[0:5])

# Event 1: picks 5-9
event_groups.append(arrivals.iloc[5:10])

# Event 2: picks 10-11 (only 2 stations)
event_groups.append(arrivals.iloc[10:12])

print(f"\n=== DETECTED {len(event_groups)} EVENTS ===")
for i, group in enumerate(event_groups):
    print(f"\nEvent {i}:")
    print(group)

# P-wave velocity assumption (typical for crustal rocks: 4-6 km/s)
VP = 5.0  # km/s

def travel_time(source, receiver, vp=VP):
    """Calculate P-wave travel time from source to receiver."""
    dist = np.linalg.norm(source - receiver)
    return dist / vp

def locate_event(picks, station_coords, vp=VP):
    """
    Locate a microseismic event using arrival time picks.
    Uses grid search followed by gradient-based optimization.
    """
    # Get stations and arrival times for this event
    stations_list = picks['station_id'].values
    arrival_times = picks['arrival_s'].values
    
    # Reference time (earliest arrival)
    t0_guess = arrival_times.min()
    
    # Receiver coordinates
    receivers = np.array([station_coords[s] for s in stations_list])
    
    # Grid search for initial location
    x_range = np.linspace(0, 6, 40)
    y_range = np.linspace(0, 10, 40)
    z_range = np.linspace(0, 5, 25)
    
    best_misfit = np.inf
    best_loc = None
    
    for x in x_range:
        for y in y_range:
            for z in z_range:
                source = np.array([x, y, z])
                tt_calc = np.array([travel_time(source, r, vp) for r in receivers])
                # Residuals (observed - calculated)
                residuals = arrival_times - (t0_guess + tt_calc)
                misfit = np.sum(residuals**2)
                if misfit < best_misfit:
                    best_misfit = misfit
                    best_loc = source
    
    # Refine with optimization
    def misfit_func(params):
        source = params[:3]
        t0 = params[3]
        tt_calc = np.array([travel_time(source, r, vp) for r in receivers])
        residuals = arrival_times - (t0 + tt_calc)
        return np.sum(residuals**2)
    
    result = minimize(misfit_func, np.concatenate([best_loc, [t0_guess]]), 
                      method='L-BFGS-B',
                      bounds=[(0, 10), (0, 12), (0, 8), (arrival_times.min()-2, arrival_times.max()+2)])
    
    if result.success:
        return result.x[:3], result.x[3], result.fun
    else:
        return best_loc, t0_guess, best_misfit

# Locate all events
print("\n=== EVENT LOCATION RESULTS ===")
event_locations = []
event_origin_times = []
event_misfits = []
event_data = []

for i, picks in enumerate(event_groups):
    if len(picks) >= 2:  # Need at least 2 stations
        loc, ot, misfit = locate_event(picks, station_coords, VP)
        event_locations.append(loc)
        event_origin_times.append(ot)
        event_misfits.append(misfit)
        event_data.append(picks)
        rms = np.sqrt(misfit / len(picks))
        print(f"Event {i}: X={loc[0]:.3f} km, Y={loc[1]:.3f} km, Z={loc[2]:.3f} km, "
              f"Origin={ot:.4f} s, RMS={rms:.4f} s, Stations={len(picks)}")

event_locations = np.array(event_locations)

# Save locations
locations_df = pd.DataFrame({
    'event_id': range(len(event_locations)),
    'x_km': event_locations[:, 0],
    'y_km': event_locations[:, 1],
    'z_km': event_locations[:, 2],
    'origin_time_s': event_origin_times,
    'misfit': event_misfits
})
locations_df.to_csv('outputs/event_locations.csv', index=False)

# Clustering analysis
print("\n=== CLUSTERING ANALYSIS ===")

# DBSCAN clustering
if len(event_locations) >= 2:
    clustering = DBSCAN(eps=2.0, min_samples=2).fit(event_locations)
    labels = clustering.labels_
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
else:
    labels = np.array([-1] * len(event_locations))
    n_clusters = 0

print(f"Number of clusters found: {n_clusters}")
print(f"Cluster labels: {labels}")

# Add cluster labels to dataframe
locations_df['cluster'] = labels
locations_df.to_csv('outputs/event_locations_with_clusters.csv', index=False)

# Calculate cluster statistics
if n_clusters > 0:
    print("\n=== CLUSTER STATISTICS ===")
    for cid in range(n_clusters):
        mask = labels == cid
        cluster_events = event_locations[mask]
        print(f"\nCluster {cid}:")
        print(f"  Events: {np.sum(mask)}")
        print(f"  Centroid: X={cluster_events[:,0].mean():.3f}, Y={cluster_events[:,1].mean():.3f}, Z={cluster_events[:,2].mean():.3f}")
        print(f"  Spread: X_std={cluster_events[:,0].std():.3f}, Y_std={cluster_events[:,1].std():.3f}, Z_std={cluster_events[:,2].std():.3f}")

# Visualization 1: Station Geometry
fig, ax = plt.subplots(figsize=(10, 8))
ax.scatter(stations['x_km'], stations['y_km'], c='blue', s=300, marker='^', 
           edgecolors='black', linewidth=2, label='Seismic Stations', zorder=5)
for _, row in stations.iterrows():
    ax.annotate(row['station_id'], (row['x_km'], row['y_km']), 
                xytext=(8, 8), textcoords='offset points', fontsize=12, fontweight='bold')
ax.set_xlabel('X (km)', fontsize=12)
ax.set_ylabel('Y (km)', fontsize=12)
ax.set_title('Microseismic Monitoring Network Geometry', fontsize=14, fontweight='bold')
ax.set_xlim(-0.5, 6.5)
ax.set_ylim(0, 11)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=11)
ax.set_aspect('equal')
plt.tight_layout()
plt.savefig('report/images/station_geometry.png', dpi=150, bbox_inches='tight')
plt.close()

# Visualization 2: Event Locations (3D)
fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='3d')

# Plot stations
ax.scatter(stations['x_km'], stations['y_km'], stations['z_km'], 
           c='blue', s=200, marker='^', edgecolors='black', linewidth=2, 
           label='Stations', zorder=5)

# Plot events colored by cluster
colors = plt.cm.tab10(np.linspace(0, 1, max(n_clusters, 1) + 2))
for cid in range(n_clusters):
    mask = labels == cid
    ax.scatter(event_locations[mask, 0], event_locations[mask, 1], event_locations[mask, 2],
               c=[colors[cid]], s=150, marker='o', edgecolors='black', linewidth=1.5,
               label=f'Cluster {cid}', alpha=0.9)

# Plot noise points
if -1 in labels:
    mask = labels == -1
    ax.scatter(event_locations[mask, 0], event_locations[mask, 1], event_locations[mask, 2],
               c='gray', s=100, marker='x', label='Unclustered', alpha=0.7, linewidth=2)

ax.set_xlabel('X (km)', fontsize=11)
ax.set_ylabel('Y (km)', fontsize=11)
ax.set_zlabel('Z (km)', fontsize=11)
ax.set_title('Microseismic Event Locations and Clusters (3D View)', fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=10)
plt.tight_layout()
plt.savefig('report/images/event_locations_3d.png', dpi=150, bbox_inches='tight')
plt.close()

# Visualization 3: Depth Distribution and Map View
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Depth histogram
axes[0].hist(event_locations[:, 2], bins=6, color='steelblue', edgecolor='black', alpha=0.7)
axes[0].axvline(event_locations[:, 2].mean(), color='red', linestyle='--', linewidth=2, 
                label=f'Mean: {event_locations[:, 2].mean():.2f} km')
axes[0].set_xlabel('Depth (km)', fontsize=11)
axes[0].set_ylabel('Number of Events', fontsize=11)
axes[0].set_title('Event Depth Distribution', fontsize=12, fontweight='bold')
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3)

# XY projection with clusters
for cid in range(n_clusters):
    mask = labels == cid
    axes[1].scatter(event_locations[mask, 0], event_locations[mask, 1], 
                    c=[colors[cid]], s=150, marker='o', edgecolors='black', 
                    linewidth=1.5, label=f'Cluster {cid}', alpha=0.9)
if -1 in labels:
    mask = labels == -1
    axes[1].scatter(event_locations[mask, 0], event_locations[mask, 1], 
                    c='gray', s=100, marker='x', label='Unclustered', alpha=0.7, linewidth=2)

axes[1].scatter(stations['x_km'], stations['y_km'], c='blue', s=250, marker='^', 
                edgecolors='black', linewidth=2, label='Stations', zorder=5)
for _, row in stations.iterrows():
    axes[1].annotate(row['station_id'], (row['x_km'], row['y_km']), 
                     xytext=(5, 5), textcoords='offset points', fontsize=9, fontweight='bold')
axes[1].set_xlabel('X (km)', fontsize=11)
axes[1].set_ylabel('Y (km)', fontsize=11)
axes[1].set_title('Event Clusters (Map View)', fontsize=12, fontweight='bold')
axes[1].legend(fontsize=9)
axes[1].grid(True, alpha=0.3)
axes[1].set_aspect('equal')

plt.tight_layout()
plt.savefig('report/images/depth_and_clusters.png', dpi=150, bbox_inches='tight')
plt.close()

# Visualization 4: Cross-sections
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# X-Z cross-section
for cid in range(n_clusters):
    mask = labels == cid
    axes[0].scatter(event_locations[mask, 0], event_locations[mask, 2], 
                    c=[colors[cid]], s=150, marker='o', edgecolors='black', 
                    linewidth=1.5, label=f'Cluster {cid}', alpha=0.9)
if -1 in labels:
    mask = labels == -1
    axes[0].scatter(event_locations[mask, 0], event_locations[mask, 2], 
                    c='gray', s=100, marker='x', label='Unclustered', alpha=0.7, linewidth=2)
axes[0].scatter(stations['x_km'], stations['z_km'], c='blue', s=200, marker='^', 
                edgecolors='black', linewidth=2, label='Stations', zorder=5)
axes[0].set_xlabel('X (km)', fontsize=11)
axes[0].set_ylabel('Depth (km)', fontsize=11)
axes[0].set_title('X-Z Cross-section', fontsize=12, fontweight='bold')
axes[0].invert_yaxis()
axes[0].legend(fontsize=9)
axes[0].grid(True, alpha=0.3)

# Y-Z cross-section
for cid in range(n_clusters):
    mask = labels == cid
    axes[1].scatter(event_locations[mask, 1], event_locations[mask, 2], 
                    c=[colors[cid]], s=150, marker='o', edgecolors='black', 
                    linewidth=1.5, label=f'Cluster {cid}', alpha=0.9)
if -1 in labels:
    mask = labels == -1
    axes[1].scatter(event_locations[mask, 1], event_locations[mask, 2], 
                    c='gray', s=100, marker='x', label='Unclustered', alpha=0.7, linewidth=2)
axes[1].scatter(stations['y_km'], stations['z_km'], c='blue', s=200, marker='^', 
                edgecolors='black', linewidth=2, label='Stations', zorder=5)
axes[1].set_xlabel('Y (km)', fontsize=11)
axes[1].set_ylabel('Depth (km)', fontsize=11)
axes[1].set_title('Y-Z Cross-section', fontsize=12, fontweight='bold')
axes[1].invert_yaxis()
axes[1].legend(fontsize=9)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/cross_sections.png', dpi=150, bbox_inches='tight')
plt.close()

# Visualization 5: Arrival Time Analysis
fig, ax = plt.subplots(figsize=(12, 6))
for i, picks in enumerate(event_data):
    ax.plot(picks['station_id'].values, picks['arrival_s'].values, 'o-', 
            label=f'Event {i}', linewidth=2, markersize=10, alpha=0.8)
ax.set_xlabel('Station ID', fontsize=11)
ax.set_ylabel('Arrival Time (s)', fontsize=11)
ax.set_title('P-wave Arrival Times by Event', fontsize=12, fontweight='bold')
ax.legend(fontsize=10, ncol=3)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/arrival_times.png', dpi=150, bbox_inches='tight')
plt.close()

# Visualization 6: Location Uncertainty Analysis
fig, ax = plt.subplots(figsize=(10, 6))
rmse_values = [np.sqrt(m/len(event_data[i])) for i, m in enumerate(event_misfits)]
bars = ax.bar(range(len(event_locations)), rmse_values, color='steelblue', edgecolor='black', alpha=0.7)
ax.axhline(np.mean(rmse_values), color='red', linestyle='--', linewidth=2, 
           label=f'Mean RMS: {np.mean(rmse_values):.4f} s')
ax.set_xlabel('Event ID', fontsize=11)
ax.set_ylabel('RMS Residual (s)', fontsize=11)
ax.set_title('Location Quality: RMS Travel-time Residuals', fontsize=12, fontweight='bold')
ax.set_xticks(range(len(event_locations)))
ax.set_xticklabels([f'{i}' for i in range(len(event_locations))])
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('report/images/location_quality.png', dpi=150, bbox_inches='tight')
plt.close()

# Visualization 7: Temporal Distribution
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(event_origin_times, event_locations[:, 2], s=200, c='steelblue', 
           edgecolors='black', linewidth=1.5, alpha=0.8, zorder=5)
for i, (ot, depth) in enumerate(zip(event_origin_times, event_locations[:, 2])):
    ax.annotate(f'E{i}', (ot, depth), xytext=(5, 5), textcoords='offset points', fontsize=10)
ax.set_xlabel('Origin Time (s)', fontsize=11)
ax.set_ylabel('Depth (km)', fontsize=11)
ax.set_title('Event Depth vs Origin Time', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig('report/images/temporal_distribution.png', dpi=150, bbox_inches='tight')
plt.close()

print("\n=== ANALYSIS COMPLETE ===")
print(f"Event locations saved to: outputs/event_locations.csv")
print(f"Figures saved to: report/images/")
print(f"\nSummary Statistics:")
print(f"  Number of events located: {len(event_locations)}")
print(f"  Mean depth: {event_locations[:,2].mean():.3f} km")
print(f"  Depth range: {event_locations[:,2].min():.3f} - {event_locations[:,2].max():.3f} km")
print(f"  Mean RMS residual: {np.mean(rmse_values):.4f} s")
print(f"  Horizontal spread (X): {event_locations[:,0].std():.3f} km")
print(f"  Horizontal spread (Y): {event_locations[:,1].std():.3f} km")
