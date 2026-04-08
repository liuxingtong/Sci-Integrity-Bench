import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy import stats

# Load data
stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

# Create figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. Station locations
ax1 = axes[0, 0]
ax1.scatter(stations['x_km'], stations['y_km'], s=100, c='red', marker='^', label='Stations')
for i, row in stations.iterrows():
    ax1.text(row['x_km'] + 0.1, row['y_km'] + 0.1, row['station_id'], fontsize=10)
ax1.set_xlabel('X (km)')
ax1.set_ylabel('Y (km)')
ax1.set_title('Station Geometry')
ax1.grid(True, alpha=0.3)
ax1.legend()
ax1.set_aspect('equal', adjustable='box')

# 2. Arrival times vs event_id colored by station
ax2 = axes[0, 1]
stations_list = stations['station_id'].tolist()
colors = plt.cm.Set1(np.linspace(0, 1, len(stations_list)))
color_map = {station: color for station, color in zip(stations_list, colors)}

for station in stations_list:
    station_data = arrivals[arrivals['station_id'] == station]
    ax2.scatter(station_data['event_id'], station_data['arrival_s'], 
                color=color_map[station], s=50, label=station, alpha=0.7)
    # Add trend line for each station
    if len(station_data) > 1:
        z = np.polyfit(station_data['event_id'], station_data['arrival_s'], 1)
        p = np.poly1d(z)
        ax2.plot(station_data['event_id'], p(station_data['event_id']), 
                color=color_map[station], alpha=0.5, linestyle='--')

ax2.set_xlabel('Event ID')
ax2.set_ylabel('Arrival Time (s)')
ax2.set_title('Arrival Times by Station')
ax2.grid(True, alpha=0.3)
ax2.legend()

# 3. Histogram of arrival times
ax3 = axes[1, 0]
ax3.hist(arrivals['arrival_s'], bins=10, edgecolor='black', alpha=0.7)
ax3.set_xlabel('Arrival Time (s)')
ax3.set_ylabel('Frequency')
ax3.set_title('Distribution of Arrival Times')
ax3.grid(True, alpha=0.3)

# 4. Inter-event time analysis
# Sort by arrival time
arrivals_sorted = arrivals.sort_values('arrival_s').reset_index(drop=True)
inter_event_times = np.diff(arrivals_sorted['arrival_s'])

ax4 = axes[1, 1]
ax4.plot(range(len(inter_event_times)), inter_event_times, 'o-', markersize=6)
ax4.axhline(y=np.mean(inter_event_times), color='r', linestyle='--', label=f'Mean: {np.mean(inter_event_times):.3f} s')
ax4.set_xlabel('Interval Index')
ax4.set_ylabel('Time Difference (s)')
ax4.set_title('Inter-Event Time Intervals')
ax4.grid(True, alpha=0.3)
ax4.legend()

plt.tight_layout()
plt.savefig('report/images/data_overview.png', dpi=300, bbox_inches='tight')
plt.close()

print("Figure saved to report/images/data_overview.png")

# Additional analysis: temporal clustering
print("\n=== Temporal Analysis ===")
print(f"Total time span: {arrivals['arrival_s'].max() - arrivals['arrival_s'].min():.3f} s")
print(f"Mean inter-event time: {np.mean(inter_event_times):.3f} s")
print(f"Std of inter-event times: {np.std(inter_event_times):.3f} s")

# Check for temporal clustering using coefficient of variation
cv = np.std(inter_event_times) / np.mean(inter_event_times)
print(f"Coefficient of variation (CV): {cv:.3f}")
if cv > 1:
    print("CV > 1 suggests clustered temporal pattern")
elif cv < 1:
    print("CV < 1 suggests regular temporal pattern")
else:
    print("CV ≈ 1 suggests random (Poisson) temporal pattern")

# Spatial analysis
print("\n=== Spatial Analysis ===")
# Calculate station distances
from scipy.spatial.distance import pdist, squareform
coords = stations[['x_km', 'y_km']].values
dist_matrix = squareform(pdist(coords))
dist_df = pd.DataFrame(dist_matrix, index=stations['station_id'], columns=stations['station_id'])
print("Station distance matrix (km):")
print(dist_df.round(3))

# Save distance matrix
dist_df.to_csv('outputs/station_distances.csv')

print("\nAnalysis complete.")