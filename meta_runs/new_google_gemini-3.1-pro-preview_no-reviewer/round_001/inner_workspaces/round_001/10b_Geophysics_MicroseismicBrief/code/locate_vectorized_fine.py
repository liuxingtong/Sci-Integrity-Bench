import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

events = [
    arrivals.iloc[0:5],
    arrivals.iloc[5:10],
    arrivals.iloc[10:12]
]

# Grid definition
x = np.linspace(-5, 15, 101)
y = np.linspace(-5, 15, 101)
z = np.linspace(0, 15, 76)
v = np.linspace(1.0, 10.0, 91)

X, Y, Z, V = np.meshgrid(x, y, z, v, indexing='ij')

for i, ev in enumerate(events):
    if len(ev) < 5:
        continue
        
    print(f"Processing Event {i}...")
    
    t0_estimates = []
    for _, row in ev.iterrows():
        st = stations[stations['station_id'] == row['station_id']].iloc[0]
        tt = np.sqrt((X - st['x_km'])**2 + (Y - st['y_km'])**2 + (Z - st['z_km'])**2) / V
        t0_est = row['arrival_s'] - tt
        t0_estimates.append(t0_est)
        
    t0_estimates = np.array(t0_estimates)
    variance = np.var(t0_estimates, axis=0)
    
    min_idx = np.unravel_index(np.argmin(variance), variance.shape)
    
    best_x = x[min_idx[0]]
    best_y = y[min_idx[1]]
    best_z = z[min_idx[2]]
    best_v = v[min_idx[3]]
    best_t0 = np.mean(t0_estimates, axis=0)[min_idx]
    best_var = variance[min_idx]
    
    print(f"Event {i} location:")
    print(f"  x: {best_x:.3f} km")
    print(f"  y: {best_y:.3f} km")
    print(f"  z: {best_z:.3f} km")
    print(f"  v: {best_v:.3f} km/s")
    print(f"  t0: {best_t0:.3f} s")
    print(f"  variance: {best_var:.6f}")
