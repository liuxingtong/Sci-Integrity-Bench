import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.spatial.distance import cdist
import os

# Load data
stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

print("=== Attempting Event Location ===")
print("Note: With only one pick per 'event_id', traditional location is impossible.")
print("We need to hypothesize which picks belong to the same actual events.")

# Let's explore a hypothesis: maybe we have 3 events, each recorded at multiple stations
# The pattern S0,S1,S2,S3,S4,S0,S1,S2,S3,S4,S0,S1 suggests 3 cycles
# Could be 3 events with 4 stations each?

# Let's try to find clusters in arrival times
from sklearn.cluster import DBSCAN

# Reshape arrival times for clustering
arrival_times = arrivals['arrival_s'].values.reshape(-1, 1)

# Try DBSCAN with different parameters
eps_values = [0.1, 0.2, 0.5, 1.0]
for eps in eps_values:
    dbscan = DBSCAN(eps=eps, min_samples=2)
    clusters = dbscan.fit_predict(arrival_times)
    n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
    n_noise = list(clusters).count(-1)
    print(f"DBSCAN eps={eps}: {n_clusters} clusters, {n_noise} noise points")
    if n_clusters > 0:
        print(f"  Cluster labels: {clusters}")

# The arrival times are too regularly spaced for DBSCAN to find clusters
# Let's try a different approach: assume constant velocity and try to locate
# hypothetical events that could explain the observed pattern

# First, let's assume a P-wave velocity (typical for crustal rocks)
vp = 5.0  # km/s (typical for upper crust)
print(f"\nAssuming P-wave velocity: {vp} km/s")

# Let's try to find if any pairs of picks could be from the same event
# For two picks at stations i and j with times ti and tj,
# the time difference constraint is: |ti - tj| <= distance(i,j)/vp

station_coords = {row['station_id']: (row['x_km'], row['y_km'], row['z_km']) 
                  for _, row in stations.iterrows()}

# Calculate maximum possible time difference for each station pair
print("\nMaximum allowed time differences for station pairs (distance/vp):")
for i, si in enumerate(stations['station_id']):
    for j, sj in enumerate(stations['station_id']):
        if i < j:
            xi, yi, zi = station_coords[si]
            xj, yj, zj = station_coords[sj]
            dist = np.sqrt((xi-xj)**2 + (yi-yj)**2 + (zi-zj)**2)
            max_tdiff = dist / vp
            print(f"  {si}-{sj}: dist={dist:.3f} km, max Δt={max_tdiff:.3f} s")

# Now let's look at actual time differences between consecutive picks
print("\nActual time differences between consecutive picks:")
arrivals_sorted = arrivals.sort_values('arrival_s').reset_index(drop=True)
for i in range(len(arrivals_sorted)-1):
    t1 = arrivals_sorted.loc[i, 'arrival_s']
    t2 = arrivals_sorted.loc[i+1, 'arrival_s']
    s1 = arrivals_sorted.loc[i, 'station_id']
    s2 = arrivals_sorted.loc[i+1, 'station_id']
    dt = t2 - t1
    xi, yi, zi = station_coords[s1]
    xj, yj, zj = station_coords[s2]
    dist = np.sqrt((xi-xj)**2 + (yi-yj)**2 + (zi-zj)**2)
    max_allowed = dist / vp
    possible_same_event = dt <= max_allowed
    print(f"  {s1}({t1:.3f}s) -> {s2}({t2:.3f}s): Δt={dt:.3f}s, dist={dist:.3f}km, max Δt={max_allowed:.3f}s, same event? {possible_same_event}")

# Let's try a grid search for possible event locations
print("\n=== Grid Search for Possible Event Locations ===")
# Create a grid
x_min, x_max = stations['x_km'].min() - 2, stations['x_km'].max() + 2
y_min, y_max = stations['y_km'].min() - 2, stations['y_km'].max() + 2

nx, ny = 50, 50
x_grid = np.linspace(x_min, x_max, nx)
y_grid = np.linspace(y_min, y_max, ny)
X, Y = np.meshgrid(x_grid, y_grid)

# Assume events at z=0 for simplicity
z_event = 0.0

# Let's test if we can find locations that explain the pattern
# We'll look for locations that minimize travel time residuals
# for groups of picks that might be from the same event

def calculate_travel_time(x, y, z, station_coord, vp):
    """Calculate travel time from event to station"""
    dist = np.sqrt((x - station_coord[0])**2 + 
                   (y - station_coord[1])**2 + 
                   (z - station_coord[2])**2)
    return dist / vp

# Try to locate using the first pick from each station
# as if they were from one event
first_picks = []
for station in ['S0', 'S1', 'S2', 'S3', 'S4']:
    station_picks = arrivals[arrivals['station_id'] == station]
    if len(station_picks) > 0:
        first_pick = station_picks.iloc[0]
        first_picks.append({
            'station': station,
            'time': first_pick['arrival_s'],
            'event_id': first_pick['event_id']
        })

print(f"\nFirst pick from each station (potential first event):")
for pick in first_picks:
    print(f"  Station {pick['station']}: time={pick['time']:.3f}s, event_id={pick['event_id']}")

# Create a misfit function for these picks
def misfit_function(params, picks, station_coords, vp):
    x, y, t0 = params  # t0 is origin time
    misfit = 0
    for pick in picks:
        station = pick['station']
        obs_time = pick['time']
        pred_time = t0 + calculate_travel_time(x, y, 0, station_coords[station], vp)
        misfit += (obs_time - pred_time)**2
    return misfit

# Initial guess: centroid of stations
x0 = stations['x_km'].mean()
y0 = stations['y_km'].mean()
t0 = np.mean([p['time'] for p in first_picks])

initial_params = [x0, y0, t0]
print(f"\nInitial guess for event location: x={x0:.2f} km, y={y0:.2f} km, t0={t0:.3f} s")

# Run optimization
result = minimize(misfit_function, initial_params, 
                  args=(first_picks, station_coords, vp),
                  method='Nelder-Mead')

if result.success:
    x_opt, y_opt, t0_opt = result.x
    print(f"Optimized location: x={x_opt:.2f} km, y={y_opt:.2f} km, t0={t0_opt:.3f} s")
    print(f"Misfit: {result.fun:.6f}")
    
    # Calculate residuals
    print("\nResiduals (observed - predicted):")
    for pick in first_picks:
        station = pick['station']
        obs_time = pick['time']
        pred_time = t0_opt + calculate_travel_time(x_opt, y_opt, 0, station_coords[station], vp)
        residual = obs_time - pred_time
        print(f"  Station {station}: {residual:.4f} s")
else:
    print("Optimization failed")

print("\n=== Creating Visualization ===")
# Create visualization of station geometry and possible event locations
fig, ax = plt.subplots(figsize=(10, 8))

# Plot stations
ax.scatter(stations['x_km'], stations['y_km'], s=200, c='red', 
           marker='^', edgecolors='black', label='Stations', zorder=5)
for i, row in stations.iterrows():
    ax.text(row['x_km'] + 0.15, row['y_km'] + 0.15, row['station_id'], 
            fontsize=12, fontweight='bold')

# Plot optimized event location if available
if result.success:
    ax.scatter(x_opt, y_opt, s=300, c='blue', marker='*', 
               edgecolors='black', label='Optimized Event Location', zorder=10)
    ax.text(x_opt + 0.2, y_opt + 0.2, 'Event 1', fontsize=11, fontweight='bold')
    
    # Draw circles showing travel time contours
    for pick in first_picks:
        station = pick['station']
        sx, sy, sz = station_coords[station]
        travel_time = pick['time'] - t0_opt
        radius = travel_time * vp
        circle = plt.Circle((sx, sy), radius, color='blue', 
                           fill=False, linestyle='--', alpha=0.5)
        ax.add_patch(circle)

# Set plot properties
ax.set_xlabel('X (km)', fontsize=12)
ax.set_ylabel('Y (km)', fontsize=12)
ax.set_title('Station Geometry and Possible Event Location', fontsize=14)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right')
ax.set_aspect('equal', adjustable='box')

# Set limits
buffer = 1.0
ax.set_xlim(stations['x_km'].min() - buffer, stations['x_km'].max() + buffer)
ax.set_ylim(stations['y_km'].min() - buffer, stations['y_km'].max() + buffer)

plt.tight_layout()
plt.savefig('report/images/event_location_attempt.png', dpi=300, bbox_inches='tight')
plt.close()

print("Figure saved to report/images/event_location_attempt.png")
print("\nEvent location analysis complete.")