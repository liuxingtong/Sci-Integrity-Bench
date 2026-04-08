#!/usr/bin/env python
"""
Microseismic Analysis Brief
Analyzes source clustering and structural context from station geometry and arrival picks.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize, differential_evolution
from sklearn.cluster import KMeans
import os

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

print("=== STATIONS ===")
print(stations)
print("\n=== ARRIVALS ===")
print(arrivals)

# Group events by station pattern - each event should have unique stations
arrivals_sorted = arrivals.sort_values('arrival_s').reset_index(drop=True)

event_groups = []
current_group = [0]
seen_stations = {arrivals_sorted.iloc[0]['station_id']}

for i in range(1, len(arrivals_sorted)):
    sta = arrivals_sorted.iloc[i]['station_id']
    if sta in seen_stations:
        event_groups.append(current_group)
        current_group = [i]
        seen_stations = {sta}
    else:
        current_group.append(i)
        seen_stations.add(sta)
event_groups.append(current_group)

print(f"\n=== IDENTIFIED EVENT GROUPS: {len(event_groups)} ===")
for i, group in enumerate(event_groups):
    subset = arrivals_sorted.iloc[group]
    print(f"Event {i}: {len(subset)} picks, stations: {list(subset['station_id'])}, time range: {subset['arrival_s'].min():.3f} - {subset['arrival_s'].max():.3f}s")

arrivals['event_group'] = -1
for event_idx, group_indices in enumerate(event_groups):
    original_indices = arrivals_sorted.iloc[group_indices].index
    arrivals.loc[original_indices, 'event_group'] = event_idx

arrivals.to_csv('outputs/processed_arrivals.csv', index=False)

# Station bounds for constrained location
sta_x_min, sta_x_max = stations['x_km'].min() - 2, stations['x_km'].max() + 2
sta_y_min, sta_y_max = stations['y_km'].min() - 2, stations['y_km'].max() + 2

print(f"\nSearch bounds: X=[{sta_x_min:.1f}, {sta_x_max:.1f}], Y=[{sta_y_min:.1f}, {sta_y_max:.1f}]")

def travel_time(x, y, z, station_x, station_y, station_z, velocity):
    dist = np.sqrt((x - station_x)**2 + (y - station_y)**2 + (z - station_z)**2)
    return dist / velocity

def objective_function(params, picks, stations_df, velocity):
    origin_time, x, y, z = params
    # Penalize locations outside reasonable bounds
    if z < -1 or z > 20 or x < sta_x_min or x > sta_x_max or y < sta_y_min or y > sta_y_max:
        return 1e10
    residuals = []
    for _, pick in picks.iterrows():
        station = stations_df[stations_df['station_id'] == pick['station_id']].iloc[0]
        pred_time = origin_time + travel_time(x, y, z, station['x_km'], station['y_km'], station['z_km'], velocity)
        residuals.append(pred_time - pick['arrival_s'])
    return np.sum(np.array(residuals)**2)

def locate_event_grid(picks, stations_df, velocity=5.0):
    """Grid search for event location with bounded constraints."""
    # Create grid
    x_vals = np.linspace(sta_x_min, sta_x_max, 30)
    y_vals = np.linspace(sta_y_min, sta_y_max, 30)
    z_vals = np.linspace(0, 10, 20)  # Depth from 0 to 10 km
    
    best_rms = float('inf')
    best_params = None
    
    t0_guess = picks['arrival_s'].min() - 0.5
    
    for x in x_vals:
        for y in y_vals:
            for z in z_vals:
                # Calculate origin time from first arrival
                station0 = stations_df.iloc[0]
                tt0 = travel_time(x, y, z, station0['x_km'], station0['y_km'], station0['z_km'], velocity)
                origin_time = picks['arrival_s'].iloc[0] - tt0
                
                # Calculate RMS
                residuals = []
                for _, pick in picks.iterrows():
                    station = stations_df[stations_df['station_id'] == pick['station_id']].iloc[0]
                    pred_time = origin_time + travel_time(x, y, z, station['x_km'], station['y_km'], station['z_km'], velocity)
                    residuals.append(pred_time - pick['arrival_s'])
                rms = np.sqrt(np.mean(np.array(residuals)**2))
                
                if rms < best_rms:
                    best_rms = rms
                    best_params = [origin_time, x, y, z]
    
    # Refine with local optimization
    if best_params is not None:
        result = minimize(objective_function, best_params, args=(picks, stations_df, velocity), 
                         method='Nelder-Mead', options={'maxiter': 500})
        if result.success:
            origin_time, x, y, z = result.x
            # Ensure z is positive (depth)
            z = abs(z)
            residuals = []
            for _, pick in picks.iterrows():
                station = stations_df[stations_df['station_id'] == pick['station_id']].iloc[0]
                pred_time = origin_time + travel_time(x, y, z, station['x_km'], station['y_km'], station['z_km'], velocity)
                residuals.append(pred_time - pick['arrival_s'])
            rms = np.sqrt(np.mean(np.array(residuals)**2))
            return {'x_km': x, 'y_km': y, 'z_km': z, 'origin_time': origin_time, 'rms_residual': rms, 'success': True}
    
    return {'success': False, 'x_km': 0, 'y_km': 0, 'z_km': 0, 'origin_time': 0, 'rms_residual': 0}

VELOCITY = 5.0
print(f"\n=== EVENT LOCATIONS (Vp = {VELOCITY} km/s) ===")
located_events = []

for event_id in arrivals['event_group'].unique():
    picks = arrivals[arrivals['event_group'] == event_id]
    location = locate_event_grid(picks, stations, VELOCITY)
    location['event_id'] = event_id
    location['n_picks'] = len(picks)
    located_events.append(location)
    status = "OK" if location['success'] else "FAILED"
    print(f"Event {event_id} [{status}]: x={location.get('x_km', 0):.2f}km, y={location.get('y_km', 0):.2f}km, z={location.get('z_km', 0):.2f}km, RMS={location.get('rms_residual', 0):.4f}s")

located_df = pd.DataFrame(located_events)
located_df.to_csv('outputs/located_events.csv', index=False)

valid_events = located_df[located_df['success']].copy()
print(f"\nSuccessfully located {len(valid_events)} events")

# Initialize cluster column
valid_events['cluster'] = 0

if len(valid_events) >= 2:
    coords = valid_events[['x_km', 'y_km', 'z_km']].values
    inertias = []
    K_range = range(1, min(6, len(valid_events)))
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(coords)
        inertias.append(kmeans.inertia_)
    
    plt.figure(figsize=(8, 5))
    plt.plot(K_range, inertias, 'bo-', linewidth=2, markersize=8)
    plt.xlabel('Number of Clusters (k)', fontsize=12)
    plt.ylabel('Inertia', fontsize=12)
    plt.title('Elbow Method for Optimal Cluster Number', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/cluster_elbow.png', dpi=150)
    plt.close()
    
    n_clusters = min(2, len(valid_events))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    valid_events.loc[:, 'cluster'] = kmeans.fit_predict(coords)
    print(f"Cluster centers:\n{kmeans.cluster_centers_}")

# Figure 1: Station map with event locations
plt.figure(figsize=(10, 8))
plt.scatter(stations['x_km'], stations['y_km'], c='red', s=150, marker='^', edgecolors='black', linewidths=1.5, label='Stations', zorder=5)
for _, sta in stations.iterrows():
    plt.annotate(sta['station_id'], (sta['x_km'], sta['y_km']), textcoords="offset points", xytext=(5, 5), fontsize=10, fontweight='bold')

if len(valid_events) > 0:
    plt.scatter(valid_events['x_km'], valid_events['y_km'], c=valid_events['cluster'], cmap='viridis', s=100, marker='o', edgecolors='black', linewidths=1.5, label='Events')
    for _, evt in valid_events.iterrows():
        plt.annotate(f"E{int(evt['event_id'])}", (evt['x_km'], evt['y_km']), textcoords="offset points", xytext=(-15, -10), fontsize=9, color='blue')

plt.xlabel('X (km)', fontsize=12)
plt.ylabel('Y (km)', fontsize=12)
plt.title('Station Geometry and Event Locations (Map View)', fontsize=14)
plt.legend(loc='best')
plt.grid(True, alpha=0.3)
plt.axis('equal')
plt.tight_layout()
plt.savefig('report/images/station_event_map.png', dpi=150)
plt.close()

# Figure 2: Depth cross-section
plt.figure(figsize=(10, 6))
if len(valid_events) > 0:
    plt.scatter(valid_events['x_km'], valid_events['z_km'], c=valid_events['cluster'], cmap='viridis', s=100, marker='o', edgecolors='black', linewidths=1.5)
    for _, evt in valid_events.iterrows():
        plt.annotate(f"E{int(evt['event_id'])}", (evt['x_km'], evt['z_km']), textcoords="offset points", xytext=(-15, 10), fontsize=9, color='blue')

plt.scatter(stations['x_km'], stations['z_km'], c='red', s=100, marker='^', edgecolors='black', linewidths=1.5, label='Stations (z=0)')
plt.xlabel('X (km)', fontsize=12)
plt.ylabel('Depth Z (km)', fontsize=12)
plt.title('Event Depth Cross-Section (X-Z plane)', fontsize=14)
plt.legend(loc='best')
plt.grid(True, alpha=0.3)
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('report/images/depth_cross_section.png', dpi=150)
plt.close()

# Figure 3: 3D visualization
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
ax.scatter(stations['x_km'], stations['y_km'], stations['z_km'], c='red', s=100, marker='^', edgecolors='black', linewidths=1.5, label='Stations')
if len(valid_events) > 0:
    ax.scatter(valid_events['x_km'], valid_events['y_km'], valid_events['z_km'], c=valid_events['cluster'], cmap='viridis', s=80, marker='o', edgecolors='black', linewidths=1.5, label='Events')
ax.set_xlabel('X (km)', fontsize=11)
ax.set_ylabel('Y (km)', fontsize=11)
ax.set_zlabel('Z (km)', fontsize=11)
ax.set_title('3D Distribution of Stations and Event Hypocenters', fontsize=14)
ax.legend(loc='best')
ax.view_init(elev=20, azim=45)
plt.tight_layout()
plt.savefig('report/images/3d_distribution.png', dpi=150)
plt.close()

# Figure 4: Arrival time residuals
plt.figure(figsize=(10, 6))
for event_id in valid_events['event_id'].unique():
    evt_data = located_events[int(event_id)]
    if evt_data.get('success', False):
        picks = arrivals[arrivals['event_group'] == event_id]
        residuals = []
        for _, pick in picks.iterrows():
            station = stations[stations['station_id'] == pick['station_id']].iloc[0]
            pred_time = evt_data['origin_time'] + travel_time(evt_data['x_km'], evt_data['y_km'], evt_data['z_km'], station['x_km'], station['y_km'], station['z_km'], VELOCITY)
            residuals.append(pred_time - pick['arrival_s'])
        plt.plot(range(len(residuals)), residuals, 'o-', label=f'Event {int(event_id)}', linewidth=2, markersize=8)

plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
plt.xlabel('Pick Index', fontsize=12)
plt.ylabel('Residual (s)', fontsize=12)
plt.title('Arrival Time Residuals by Event', fontsize=14)
plt.legend(loc='best')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/residuals.png', dpi=150)
plt.close()

# Figure 5: Inter-event distances
if len(valid_events) >= 2:
    plt.figure(figsize=(8, 6))
    distances = []
    n_events = len(valid_events)
    for i in range(n_events):
        for j in range(i+1, n_events):
            dist = np.sqrt((valid_events.iloc[i]['x_km'] - valid_events.iloc[j]['x_km'])**2 + (valid_events.iloc[i]['y_km'] - valid_events.iloc[j]['y_km'])**2 + (valid_events.iloc[i]['z_km'] - valid_events.iloc[j]['z_km'])**2)
            distances.append(dist)
    plt.hist(distances, bins=10, edgecolor='black', alpha=0.7, color='steelblue')
    plt.xlabel('Inter-Event Distance (km)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Distribution of Inter-Event Distances', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/inter_event_distances.png', dpi=150)
    plt.close()

# Figure 6: Station geometry
plt.figure(figsize=(8, 6))
plt.scatter(stations['x_km'], stations['y_km'], c='red', s=200, marker='^', edgecolors='black', linewidths=2)
for _, sta in stations.iterrows():
    plt.annotate(sta['station_id'], (sta['x_km'], sta['y_km']), textcoords="offset points", xytext=(5, 5), fontsize=12, fontweight='bold')

# Draw network connecting stations
from itertools import combinations
for (i, j) in combinations(range(len(stations)), 2):
    plt.plot([stations.iloc[i]['x_km'], stations.iloc[j]['x_km']], 
             [stations.iloc[i]['y_km'], stations.iloc[j]['y_km']], 
             'k--', alpha=0.3, linewidth=0.5)

plt.xlabel('X (km)', fontsize=12)
plt.ylabel('Y (km)', fontsize=12)
plt.title('Station Network Geometry', fontsize=14)
plt.grid(True, alpha=0.3)
plt.axis('equal')
plt.tight_layout()
plt.savefig('report/images/station_geometry.png', dpi=150)
plt.close()

print("\n=== ANALYSIS COMPLETE ===")
print(f"Figures saved to report/images/")
