import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import os

# Load data
stations = pd.read_csv('../data/stations.csv')
arrivals = pd.read_csv('../data/arrival_times.csv')

# Merge data
arrivals_with_coords = pd.merge(arrivals, stations, on='station_id', how='left')

# Assume P-wave velocity (km/s)
vp = 5.5  # km/s, typical for crustal rocks

# Function to calculate travel time from source to station
def calc_travel_time(source_x, source_y, station_x, station_y, velocity=vp):
    """Calculate travel time from source to station."""
    distance = np.sqrt((source_x - station_x)**2 + (source_y - station_y)**2)
    return distance / velocity

# Function to calculate misfit for a source location
def location_misfit(params, station_data, arrival_times):
    """Calculate misfit between observed and calculated arrival times."""
    source_x, source_y, origin_time = params
    misfit = 0
    for idx, row in station_data.iterrows():
        calc_time = origin_time + calc_travel_time(source_x, source_y, 
                                                  row['x_km'], row['y_km'])
        misfit += (calc_time - row['arrival_s'])**2
    return misfit

# Since we only have one arrival per "event", we need to group events.
# Based on the regular pattern, let's assume events occur in groups of 5
# (one detection at each station in sequence)

# Group arrivals into potential events (groups of 5 consecutive measurements)
event_groups = []
for i in range(0, len(arrivals_with_coords) - 4, 5):
    group = arrivals_with_coords.iloc[i:i+5]
    event_groups.append(group)

print(f"Number of potential event groups: {len(event_groups)}")

# Try to locate each group
located_events = []

for i, group in enumerate(event_groups):
    print(f"\n=== Processing event group {i} ===")
    print(f"Stations: {group['station_id'].tolist()}")
    print(f"Arrival times: {group['arrival_s'].tolist()}")
    
    # Initial guess: centroid of stations
    init_x = group['x_km'].mean()
    init_y = group['y_km'].mean()
    init_t0 = group['arrival_s'].min()  # earliest arrival
    
    # Perform optimization
    result = minimize(location_misfit, 
                     [init_x, init_y, init_t0],
                     args=(group, group['arrival_s']),
                     method='Nelder-Mead',
                     options={'maxiter': 1000})
    
    if result.success:
        loc_x, loc_y, origin_time = result.x
        misfit = result.fun
        print(f"Located at: ({loc_x:.3f}, {loc_y:.3f}) km")
        print(f"Origin time: {origin_time:.4f} s")
        print(f"Misfit: {misfit:.6f}")
        
        # Calculate residuals
        residuals = []
        for idx, row in group.iterrows():
            calc_time = origin_time + calc_travel_time(loc_x, loc_y, 
                                                      row['x_km'], row['y_km'])
            residual = calc_time - row['arrival_s']
            residuals.append(residual)
            print(f"  Station {row['station_id']}: obs={row['arrival_s']:.4f}, calc={calc_time:.4f}, residual={residual:.4f} s")
        
        located_events.append({
            'group_id': i,
            'x': loc_x,
            'y': loc_y,
            'origin_time': origin_time,
            'misfit': misfit,
            'stations': group['station_id'].tolist(),
            'residuals_mean': np.mean(np.abs(residuals))
        })
    else:
        print(f"Location failed: {result.message}")

# Convert to DataFrame
if located_events:
    events_df = pd.DataFrame(located_events)
    print("\n=== Located Events ===")
    print(events_df[['group_id', 'x', 'y', 'origin_time', 'misfit', 'residuals_mean']])
    
    # Save results
    os.makedirs('../outputs', exist_ok=True)
    events_df.to_csv('../outputs/located_events.csv', index=False)
    print("\nSaved located events to ../outputs/located_events.csv")
    
    # Create visualization
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: Station and event locations
    ax1 = axes[0]
    ax1.scatter(stations['x_km'], stations['y_km'], s=100, c='red', 
               marker='^', label='Stations', zorder=5)
    for idx, row in stations.iterrows():
        ax1.text(row['x_km']+0.1, row['y_km']+0.1, row['station_id'], 
                fontsize=9, zorder=6)
    
    # Plot event locations
    if len(events_df) > 0:
        ax1.scatter(events_df['x'], events_df['y'], s=80, c='blue', 
                   marker='o', label='Located Events', zorder=4)
        for idx, row in events_df.iterrows():
            ax1.text(row['x']+0.1, row['y']+0.1, f"E{int(row['group_id'])}", 
                    fontsize=8, zorder=6)
    
    ax1.set_xlabel('X (km)')
    ax1.set_ylabel('Y (km)')
    ax1.set_title('Station and Event Locations')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_aspect('equal', adjustable='box')
    
    # Plot 2: Event origin times
    ax2 = axes[1]
    if len(events_df) > 0:
        ax2.plot(events_df['origin_time'], events_df['group_id'], 'bo-', markersize=8)
        ax2.set_xlabel('Origin Time (s)')
        ax2.set_ylabel('Event Group ID')
        ax2.set_title('Event Origin Times')
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    os.makedirs('../report/images', exist_ok=True)
    plt.savefig('../report/images/event_locations.png', dpi=300, bbox_inches='tight')
    print("Saved figure to ../report/images/event_locations.png")
    
    plt.show()
else:
    print("No events were successfully located.")