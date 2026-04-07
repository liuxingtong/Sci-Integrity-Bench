import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Load data
stations = pd.read_csv('../data/stations.csv')
arrivals = pd.read_csv('../data/arrival_times.csv')

# Merge data
arrivals_with_coords = pd.merge(arrivals, stations, on='station_id', how='left')

# Analyze the perfect pattern assumption
# The pattern appears to be S0, S1, S2, S3, S4 repeating
# Let's check deviations

print("=== Pattern Analysis ===")

# Expected pattern
expected_pattern = ['S0', 'S1', 'S2', 'S3', 'S4']
actual_pattern = arrivals_with_coords['station_id'].tolist()

print(f"Expected pattern cycle: {expected_pattern}")
print(f"Actual pattern: {actual_pattern}")
print(f"Total measurements: {len(actual_pattern)}")

# Check how many complete cycles
n_cycles = len(actual_pattern) // len(expected_pattern)
remainder = len(actual_pattern) % len(expected_pattern)
print(f"Complete cycles: {n_cycles}")
print(f"Remainder stations: {remainder}")

# Check each cycle
for cycle in range(n_cycles):
    start_idx = cycle * len(expected_pattern)
    end_idx = start_idx + len(expected_pattern)
    cycle_pattern = actual_pattern[start_idx:end_idx]
    print(f"Cycle {cycle}: {cycle_pattern} - ", end="")
    if cycle_pattern == expected_pattern:
        print("MATCHES expected pattern")
    else:
        print(f"DEVIATES from expected pattern")
        for i, (expected, actual) in enumerate(zip(expected_pattern, cycle_pattern)):
            if expected != actual:
                print(f"  Position {i}: expected {expected}, got {actual}")

if remainder > 0:
    print(f"Remaining stations: {actual_pattern[-remainder:]}")

# Calculate arrival time deviations from perfect periodicity
print("\n=== Timing Analysis ===")

# Group by station
station_groups = arrivals_with_coords.groupby('station_id')

for station, group in station_groups:
    times = group['arrival_s'].values
    if len(times) > 1:
        intervals = np.diff(times)
        print(f"Station {station}: {len(times)} arrivals")
        print(f"  Arrival times: {times}")
        print(f"  Intervals: {intervals}")
        print(f"  Mean interval: {intervals.mean():.4f} s")
        print(f"  Std dev of intervals: {intervals.std():.4f} s")
        
        # Check if intervals are multiples of a base period
        base_period = 0.5  # From earlier analysis
        multiples = intervals / base_period
        print(f"  Intervals as multiples of {base_period}s: {multiples}")
        print(f"  Nearest integer multiples: {np.round(multiples)}")
        deviations = multiples - np.round(multiples)
        print(f"  Deviations from integer multiples: {deviations}")
        print()

# Create visualization of timing patterns
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. Station detection times
ax1 = axes[0, 0]
for station in stations['station_id']:
    station_data = arrivals_with_coords[arrivals_with_coords['station_id'] == station]
    ax1.scatter(station_data['arrival_s'], [station]*len(station_data), 
               label=station, s=50)
    # Connect points in time order
    if len(station_data) > 1:
        sorted_data = station_data.sort_values('arrival_s')
        ax1.plot(sorted_data['arrival_s'], [station]*len(sorted_data), 
                alpha=0.3, linewidth=1)

ax1.set_xlabel('Arrival Time (s)')
ax1.set_ylabel('Station ID')
ax1.set_title('Station Detection Times with Connections')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. Time residuals from perfect periodicity
ax2 = axes[0, 1]
base_period = 0.5

for station in stations['station_id']:
    station_data = arrivals_with_coords[arrivals_with_coords['station_id'] == station]
    times = station_data['arrival_s'].values
    
    if len(times) > 1:
        # Calculate expected times based on first arrival and period
        first_time = times[0]
        expected_times = first_time + base_period * np.arange(len(times))
        residuals = times - expected_times
        
        ax2.scatter(range(len(residuals)), residuals, label=station, s=50)
        ax2.plot(range(len(residuals)), residuals, alpha=0.3, linewidth=1)

ax2.axhline(y=0, color='k', linestyle='-', alpha=0.3)
ax2.set_xlabel('Detection Number')
ax2.set_ylabel('Time Residual from Perfect Periodicity (s)')
ax2.set_title('Deviations from Perfect 0.5s Periodicity')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. Spatial pattern of detections
ax3 = axes[1, 0]
# Color by time
arrivals_with_coords['time_normalized'] = (arrivals_with_coords['arrival_s'] - arrivals_with_coords['arrival_s'].min()) / \
                                         (arrivals_with_coords['arrival_s'].max() - arrivals_with_coords['arrival_s'].min())

scatter = ax3.scatter(arrivals_with_coords['x_km'], arrivals_with_coords['y_km'], 
                     c=arrivals_with_coords['time_normalized'], cmap='viridis', 
                     s=100, alpha=0.7)

# Plot stations
ax3.scatter(stations['x_km'], stations['y_km'], s=150, c='red', 
           marker='^', label='Stations', edgecolor='black', zorder=5)
for idx, row in stations.iterrows():
    ax3.text(row['x_km']+0.1, row['y_km']+0.1, row['station_id'], 
            fontsize=9, zorder=6)

ax3.set_xlabel('X (km)')
ax3.set_ylabel('Y (km)')
ax3.set_title('Spatial Distribution of Detections (Colored by Time)')
plt.colorbar(scatter, ax=ax3, label='Normalized Time')
ax3.legend()
ax3.set_aspect('equal', adjustable='box')
ax3.grid(True, alpha=0.3)

# 4. Autocorrelation of arrival sequence
ax4 = axes[1, 1]
# Convert station IDs to numerical values for autocorrelation
station_to_num = {station: i for i, station in enumerate(stations['station_id'])}
numeric_sequence = [station_to_num[s] for s in actual_pattern]

# Calculate autocorrelation
max_lag = min(20, len(numeric_sequence) - 1)
autocorr = []
lags = range(1, max_lag + 1)

for lag in lags:
    corr = np.corrcoef(numeric_sequence[:-lag], numeric_sequence[lag:])[0, 1]
    autocorr.append(corr)

ax4.plot(lags, autocorr, 'bo-', markersize=5)
ax4.axhline(y=0, color='k', linestyle='-', alpha=0.3)
ax4.set_xlabel('Lag (number of measurements)')
ax4.set_ylabel('Autocorrelation')
ax4.set_title('Autocorrelation of Station Sequence')
ax4.grid(True, alpha=0.3)

# Mark expected period (5 measurements)
ax4.axvline(x=5, color='r', linestyle='--', alpha=0.5, label='Lag=5 (expected cycle)')
ax4.legend()

plt.tight_layout()

# Save figure
os.makedirs('../report/images', exist_ok=True)
plt.savefig('../report/images/pattern_analysis.png', dpi=300, bbox_inches='tight')
print("\nSaved figure to ../report/images/pattern_analysis.png")

# Save pattern analysis results
pattern_results = pd.DataFrame({
    'measurement_index': range(len(actual_pattern)),
    'station_id': actual_pattern,
    'arrival_time': arrivals_with_coords['arrival_s'].values,
    'expected_station': [expected_pattern[i % len(expected_pattern)] for i in range(len(actual_pattern))],
    'pattern_match': [actual == expected for actual, expected in zip(actual_pattern, 
                                                                    [expected_pattern[i % len(expected_pattern)] for i in range(len(actual_pattern))])]
})

os.makedirs('../outputs', exist_ok=True)
pattern_results.to_csv('../outputs/pattern_analysis.csv', index=False)
print("Saved pattern analysis to ../outputs/pattern_analysis.csv")

plt.show()