import pandas as pd
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

# Group into 3 events
events = [
    arrivals.iloc[0:5],
    arrivals.iloc[5:10],
    arrivals.iloc[10:12]
]

station_dict = {row['station_id']: (row['x_km'], row['y_km'], row['z_km']) for _, row in stations.iterrows()}

def calc_travel_time(x, y, z, sx, sy, sz, v):
    return np.sqrt((x - sx)**2 + (y - sy)**2 + (z - sz)**2) / v

def objective(params, event_arrivals):
    x, y, z, t0, v = params
    if z < 0 or v < 1 or v > 10:
        return 1e9
    
    error = 0
    for _, row in event_arrivals.iterrows():
        sx, sy, sz = station_dict[row['station_id']]
        tt_calc = calc_travel_time(x, y, z, sx, sy, sz, v)
        t_calc = t0 + tt_calc
        error += (t_calc - row['arrival_s'])**2
    return error

results = []
for i, ev in enumerate(events):
    if len(ev) < 4:
        print(f"Event {i} has too few picks ({len(ev)}), skipping.")
        continue
        
    best_res = None
    best_err = np.inf
    
    # Try multiple initial guesses
    for x0 in np.linspace(0, 6, 4):
        for y0 in np.linspace(2, 10, 4):
            for z0 in np.linspace(0, 5, 3):
                for v0 in [3.0, 4.0, 5.0, 6.0]:
                    t0_guess = ev['arrival_s'].min() - np.sqrt((x0-1.65)**2 + (y0-6.62)**2 + z0**2)/v0
                    init_guess = [x0, y0, z0, t0_guess, v0]
                    
                    res = minimize(objective, init_guess, args=(ev,), method='Nelder-Mead')
                    if res.success and res.fun < best_err:
                        best_err = res.fun
                        best_res = res
                        
    print(f"Event {i}:")
    print(f"  x: {best_res.x[0]:.3f}, y: {best_res.x[1]:.3f}, z: {best_res.x[2]:.3f}, t0: {best_res.x[3]:.3f}, v: {best_res.x[4]:.3f}")
    print(f"  Residual: {best_res.fun:.6e}")
    results.append(best_res.x)
