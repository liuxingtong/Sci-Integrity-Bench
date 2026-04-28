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
    
    # Initial guess: center of network, t0=min_arrival, v=5.0 km/s
    x0 = stations['x_km'].mean()
    y0 = stations['y_km'].mean()
    z0 = 5.0
    t0_guess = ev['arrival_s'].min() - 1.0
    v0 = 5.0
    
    res = minimize(objective, [x0, y0, z0, t0_guess, v0], args=(ev, stations), method='Nelder-Mead')
    print(f"Event {i} location:")
    print(f"  x: {res.x[0]:.3f} km")
    print(f"  y: {res.x[1]:.3f} km")
    print(f"  z: {res.x[2]:.3f} km")
    print(f"  t0: {res.x[3]:.3f} s")
    print(f"  v: {res.x[4]:.3f} km/s")
    print(f"  residual: {res.fun:.6f}")
