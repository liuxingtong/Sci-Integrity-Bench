import pandas as pd
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

# Group arrivals into events based on time proximity or just sequential chunks
# Let's assume 3 events: 0-4, 5-9, 10-11
events = [
    arrivals.iloc[0:5],
    arrivals.iloc[5:10],
    arrivals.iloc[10:12]
]

def calc_travel_time(x, y, z, sx, sy, sz, v):
    return np.sqrt((x - sx)**2 + (y - sy)**2 + (z - sz)**2) / v

def objective(params, event_arrivals, station_dict):
    x, y, z, t0, v = params
    if z < 0 or v < 1 or v > 10:
        return 1e9
    
    error = 0
    for _, row in event_arrivals.iterrows():
        stat = station_dict[row['station_id']]
        tt_calc = calc_travel_time(x, y, z, stat['x'], stat['y'], stat['z'], v)
        t_calc = t0 + tt_calc
        error += (t_calc - row['arrival_s'])**2
    return error

station_dict = {}
for _, row in stations.iterrows():
    station_dict[row['station_id']] = {'x': row['x_km'], 'y': row['y_km'], 'z': row['z_km']}

results = []
for i, ev in enumerate(events):
    if len(ev) < 4:
        print(f"Event {i} has too few picks ({len(ev)}), skipping full inversion, maybe fix V.")
        # Try with fixed V=5.0
        def obj_fixed_v(params):
            x, y, z, t0 = params
            return objective([x, y, z, t0, 5.0], ev, station_dict)
        res = minimize(obj_fixed_v, [2.5, 5.0, 2.0, ev['arrival_s'].min() - 1], method='Nelder-Mead')
        print(f"Event {i} (fixed V=5):", res.x)
        continue
        
    # Initial guess: center of network, depth 2km, t0 slightly before first arrival, v=5 km/s
    init_guess = [2.5, 5.0, 2.0, ev['arrival_s'].min() - 1, 5.0]
    
    res = minimize(objective, init_guess, args=(ev, station_dict), method='Nelder-Mead')
    print(f"Event {i}:")
    print(f"  Success: {res.success}")
    print(f"  x: {res.x[0]:.3f}, y: {res.x[1]:.3f}, z: {res.x[2]:.3f}, t0: {res.x[3]:.3f}, v: {res.x[4]:.3f}")
    print(f"  Residual: {res.fun:.6f}")
    results.append(res.x)
