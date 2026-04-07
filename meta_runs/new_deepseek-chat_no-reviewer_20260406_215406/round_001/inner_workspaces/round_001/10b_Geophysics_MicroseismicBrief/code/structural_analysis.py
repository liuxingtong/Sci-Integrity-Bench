import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os

# Load data
stations = pd.read_csv('../data/stations.csv')
arrivals = pd.read_csv('../data/arrival_times.csv')

# Merge data
arrivals_with_coords = pd.merge(arrivals, stations, on='station_id', how='left')

# Create figure
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# 1. Station locations with convex hull
ax1 = axes[0, 0]
ax1.scatter(stations['x_km'], stations['y_km'], s=100, c='red', marker='^', label='Stations')
for idx, row in stations.iterrows():
    ax1.text(row['x_km']+0.1, row['y_km']+0.1, row['station_id'], fontsize=9)

# Calculate convex hull
from scipy.spatial import ConvexHull
points = stations[['x_km', 'y_km']].values
hull = ConvexHull(points)

# Plot convex hull
for simplex in hull.simplices:
    ax1.plot(points[simplex, 0], points[simplex, 1], 'k--', alpha=0.5)

# Plot centroid
centroid = points.mean(axis=0)
ax1.scatter(centroid[0], centroid[1], s=150, c='blue', marker='x', label='Centroid')

ax1.set_xlabel('X (km)')
ax1.set_ylabel('Y (km)')
ax1.set_title('Station Geometry with Convex Hull')
ax1.grid(True, alpha=0.3)
ax1.legend()
ax1.set_aspect('equal', adjustable='box')

# 2. Arrival time vs. distance from centroid
ax2 = axes[0, 1]
# Calculate distance from centroid for each station
station_distances = np.sqrt((stations['x_km'] - centroid[0])**2 + 
                           (stations['y_km'] - centroid[1])**2)
stations_with_dist = stations.copy()
stations_with_dist['distance_from_centroid'] = station_distances

# For each arrival, get station distance
arrivals_with_dist = pd.merge(arrivals_with_coords, stations_with_dist[['station_id', 'distance_from_centroid']], 
                             on='station_id', how='left')

# Plot
for station in stations['station_id']:
    station_data = arrivals_with_dist[arrivals_with_dist['station_id'] == station]
    ax2.scatter(station_data['arrival_s'], 
               station_data['distance_from_centroid'], 
               label=station, s=50)

ax2.set_xlabel('Arrival Time (s)')
ax2.set_ylabel('Distance from Centroid (km)')
ax2.set_title('Arrival Time vs. Distance from Array Center')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. Rose diagram of station bearings from centroid
ax3 = axes[0, 2]
# Calculate bearings (azimuths) from centroid to stations
bearings = []
for idx, row in stations.iterrows():
    dx = row['x_km'] - centroid[0]
    dy = row['y_km'] - centroid[1]
    # Convert to degrees, 0 = north, 90 = east
    bearing = np.degrees(np.arctan2(dx, dy))  # Using dx, dy for azimuth from north
    if bearing < 0:
        bearing += 360
    bearings.append(bearing)

# Create rose diagram
ax3 = plt.subplot(2, 3, 3, projection='polar')
ax3.set_theta_zero_location('N')
ax3.set_theta_direction(-1)  # Clockwise

# Plot bearings
for bearing, station_id in zip(bearings, stations['station_id']):
    ax3.plot([np.radians(bearing), np.radians(bearing)], [0, 1], 
            label=station_id, linewidth=3)

ax3.set_title('Station Bearings from Array Center', pad=20)
ax3.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

# 4. Time-distance analysis with linear regression
ax4 = axes[1, 0]
# Group by station and calculate mean arrival time for each station position in sequence
station_sequence = arrivals_with_coords['station_id'].tolist()
arrival_sequence = arrivals_with_coords['arrival_s'].tolist()

# Create sequences for each station
station_data_dict = {}
for station in stations['station_id']:
    indices = [i for i, s in enumerate(station_sequence) if s == station]
    station_times = [arrival_sequence[i] for i in indices]
    station_data_dict[station] = station_times

# Plot time series for each station
for station in stations['station_id']:
    times = station_data_dict[station]
    sequence_nums = np.arange(len(times))
    ax4.plot(sequence_nums, times, 'o-', label=station, markersize=5)

ax4.set_xlabel('Detection Sequence Number')
ax4.set_ylabel('Arrival Time (s)')
ax4.set_title('Arrival Time Sequences by Station')
ax4.legend()
ax4.grid(True, alpha=0.3)

# 5. Moveout analysis - time vs. station position along a line
ax5 = axes[1, 1]
# Try to find best fitting line through stations
# Project stations onto a line and analyze moveout

# First, perform PCA to find principal direction of station distribution
from sklearn.decomposition import PCA
pca = PCA(n_components=2)
pca.fit(points)
principal_dir = pca.components_[0]  # First principal component

# Project stations onto this direction
projections = np.dot(points - centroid, principal_dir)

# Sort stations by projection
sorted_indices = np.argsort(projections)
sorted_stations = stations.iloc[sorted_indices]
sorted_projections = projections[sorted_indices]

# For each arrival time, get the station projection
arrivals_with_proj = arrivals_with_coords.copy()
proj_dict = {}
for idx, row in stations.iterrows():
    proj_dict[row['station_id']] = projections[idx]
arrivals_with_proj['projection'] = arrivals_with_proj['station_id'].map(proj_dict)

# Plot moveout: arrival time vs. projection
for station in stations['station_id']:
    station_data = arrivals_with_proj[arrivals_with_proj['station_id'] == station]
    ax5.scatter(station_data['projection'], station_data['arrival_s'], 
               label=station, s=50)

# Fit linear regression
X = arrivals_with_proj['projection'].values.reshape(-1, 1)
y = arrivals_with_proj['arrival_s'].values
slope, intercept, r_value, p_value, std_err = stats.linregress(arrivals_with_proj['projection'], 
                                                              arrivals_with_proj['arrival_s'])

# Plot regression line
x_range = np.array([projections.min(), projections.max()])
ax5.plot(x_range, intercept + slope * x_range, 'k--', 
        label=f'Fit: slope={slope:.3f}, R²={r_value**2:.3f}')

ax5.set_xlabel('Projection onto Principal Direction')
ax5.set_ylabel('Arrival Time (s)')
ax5.set_title('Moveout Analysis along Principal Axis')
ax5.legend()
ax5.grid(True, alpha=0.3)

# 6. Event rate analysis
ax6 = axes[1, 2]
# Calculate inter-event times
arrival_times_sorted = np.sort(arrivals_with_coords['arrival_s'].values)
inter_event_times = np.diff(arrival_times_sorted)

# Plot histogram
ax6.hist(inter_event_times, bins=10, alpha=0.7, color='purple', edgecolor='black')
ax6.axvline(np.mean(inter_event_times), color='red', linestyle='--', 
           label=f'Mean: {np.mean(inter_event_times):.3f} s')
ax6.set_xlabel('Inter-Event Time (s)')
ax6.set_ylabel('Frequency')
ax6.set_title('Distribution of Inter-Event Times')
ax6.legend()
ax6.grid(True, alpha=0.3)

plt.tight_layout()

# Save figure
os.makedirs('../report/images', exist_ok=True)
plt.savefig('../report/images/structural_analysis.png', dpi=300, bbox_inches='tight')
print("Saved figure to ../report/images/structural_analysis.png")

# Calculate and print key metrics
print("\n=== Structural Analysis Metrics ===")
print(f"Station array centroid: ({centroid[0]:.3f}, {centroid[1]:.3f}) km")
print(f"Station array aperture (max distance): {station_distances.max():.3f} km")
print(f"Principal direction of station distribution: {principal_dir}")
print(f"Moveout slope (time vs. projection): {slope:.6f} s/km")
print(f"  This corresponds to apparent velocity: {1/abs(slope):.2f} km/s (if slope ≠ 0)")
print(f"Mean inter-event time: {np.mean(inter_event_times):.4f} s")
print(f"Std dev of inter-event times: {np.std(inter_event_times):.4f} s")
print(f"Event rate: {1/np.mean(inter_event_times):.2f} events/s")

# Save metrics
metrics_df = pd.DataFrame({
    'metric': ['centroid_x', 'centroid_y', 'array_aperture_km', 
               'principal_dir_x', 'principal_dir_y', 'moveout_slope', 
               'apparent_velocity_km_s', 'mean_inter_event_time_s',
               'std_inter_event_time_s', 'event_rate_Hz'],
    'value': [centroid[0], centroid[1], station_distances.max(),
              principal_dir[0], principal_dir[1], slope,
              1/abs(slope) if slope != 0 else np.inf,
              np.mean(inter_event_times), np.std(inter_event_times),
              1/np.mean(inter_event_times)]
})

os.makedirs('../outputs', exist_ok=True)
metrics_df.to_csv('../outputs/structural_metrics.csv', index=False)
print("\nSaved structural metrics to ../outputs/structural_metrics.csv")

plt.show()