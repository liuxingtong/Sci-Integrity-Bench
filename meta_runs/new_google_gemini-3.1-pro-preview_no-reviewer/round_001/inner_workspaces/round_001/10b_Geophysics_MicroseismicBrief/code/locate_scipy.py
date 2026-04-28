import pandas as pd
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

# Group into events
events = [
    arrivals.iloc[0:5],
    arrivals.iloc[5:10],
    arrivals.iloc[10:12]
]

def calc_travel_time(x, y, z, sx, sy, sz, v):
    return np.sqrt((x - sx)**2 + (y - sy)**2 + (z - sz)**2) / v

def objective(params, event_arrivals, stations):
    x, y, z, t0, v = params
    error = 0
    for _, row in event_arrivals.iterrows():
        station = stations[stations['station_id'] == row['station_id']].iloc[0]
        tt = calc_travel_time(x, y, z, station['x_km'], station['y_km'], station['z_km'], v)
        error += (row['arrival_s'] - (t0 + tt))**2
    return error

for i, ev in enumerate(events):
    if len(ev) < 5:
        print(f"Event {i} has only {len(ev)} arrivals, skipping full inversion.")
        continue
    
    best_res = float('inf')
    best_x = None
    
    # Try multiple initial guesses to avoid local minima
    for x0 in np.linspace(0, 10, 3):
        for y0 in np.linspace(0, 10, 3):
            for z0 in np.linspace(0, 5, 3):
                for v0 in [3.0, 4.0, 5.0, 6.0]:
                    t0_guess = ev['arrival_s'].min() - 1.0
                    
                    res = minimize(objective, [x0, y0, z0, t0_guess, v0], args=(ev, stations), method='L-BFGS-B', bounds=[(0, 10), (0, 10), (0, 10), (None, None), (2.0, 8.0)])
                    if res.fun < best_res:
                        best_res = res.fun
                        best_x = res.x
                        
    print(f"Event {i} location:")
    print(f"  x: {best_x[0]:.3f} km")
    print(f"  y: {best_x[1]:.3f} km")
    print(f"  z: {best_x[2]:.3f} km")
    print(f"  t0: {best_x[3]:.3f} s")
    print(f"  v: {best_x[4]:.3f} km/s")
    print(f"  residual: {best_res:.6f}")
