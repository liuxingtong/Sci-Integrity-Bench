import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Load data
stations = pd.read_csv('../data/stations.csv')
arrivals = pd.read_csv('../data/arrival_times.csv')

# Merge data
arrivals_with_coords = pd.merge(arrivals, stations, on='station_id', how='left')

# Create figure
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. Station locations
ax1 = axes[0, 0]
ax1.scatter(stations['x_km'], stations['y_km'], s=100, c='red', marker='^', label='Stations')
for idx, row in stations.iterrows():
    ax1.text(row['x_km']+0.1, row['y_km']+0.1, row['station_id'], fontsize=9)
ax1.set_xlabel('X (km)')
ax1.set_ylabel('Y (km)')
ax1.set_title('Station Locations')
ax1.grid(True, alpha=0.3)
ax1.legend()
ax1.set_aspect('equal', adjustable='box')

# 2. Arrival times by station
ax2 = axes[0, 1]
for station in stations['station_id']:
    station_data = arrivals_with_coords[arrivals_with_coords['station_id'] == station]
    ax2.scatter(station_data['arrival_s'], [station]*len(station_data), 
               label=station, s=50)
ax2.set_xlabel('Arrival Time (s)')
ax2.set_ylabel('Station ID')
ax2.set_title('Arrival Times by Station')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. Arrival time sequence
ax3 = axes[1, 0]
ax3.plot(arrivals_with_coords['arrival_s'], arrivals_with_coords['event_id'], 'bo-', markersize=5)
ax3.set_xlabel('Arrival Time (s)')
ax3.set_ylabel('Event ID')
ax3.set_title('Arrival Time Sequence')
ax3.grid(True, alpha=0.3)

# 4. Station usage pattern
ax4 = axes[1, 1]
station_sequence = arrivals_with_coords['station_id'].tolist()
colors = {'S0': 'red', 'S1': 'blue', 'S2': 'green', 'S3': 'orange', 'S4': 'purple'}
for i, station in enumerate(station_sequence):
    ax4.scatter(i, 0, color=colors[station], s=100, marker='s')
    ax4.text(i, 0.1, station, ha='center', fontsize=8)
ax4.set_xlabel('Sequence Index')
ax4.set_yticks([])
ax4.set_title('Station Detection Sequence')
ax4.set_xlim(-0.5, len(station_sequence)-0.5)

plt.tight_layout()

# Save figure
os.makedirs('../report/images', exist_ok=True)
plt.savefig('../report/images/data_overview.png', dpi=300, bbox_inches='tight')
print("Saved figure to ../report/images/data_overview.png")

# Additional analysis: Check if events form clusters in time
print("\n=== Time Clustering Analysis ===")
arrival_times = arrivals_with_coords['arrival_s'].values

# Calculate time differences between consecutive arrivals
time_diffs = np.diff(arrival_times)
print(f"Time differences between consecutive arrivals: {time_diffs}")
print(f"Mean time difference: {np.mean(time_diffs):.4f} s")
print(f"Std dev of time differences: {np.std(time_diffs):.4f} s")

# Look for patterns in station sequence
print(f"\nStation sequence: {station_sequence}")
print(f"Station cycle pattern: {station_sequence[:5]} (first cycle)")
print(f"Station cycle pattern: {station_sequence[5:10]} (second cycle)")
print(f"Station cycle pattern: {station_sequence[10:]} (third cycle start)")

plt.show()