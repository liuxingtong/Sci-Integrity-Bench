import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

# Assume 3 events based on the repeating station pattern
events = [
    arrivals.iloc[0:5],
    arrivals.iloc[5:10],
    arrivals.iloc[10:12]
]

station_dict = {row['station_id']: (row['x_km'], row['y_km'], row['z_km']) for _, row in stations.iterrows()}

def grid_search(event_arrivals, v):
    best_err = np.inf
    best_loc = None
    
    # Grid over x, y, z
    xs = np.linspace(-2, 10, 50)
    ys = np.linspace(-2, 12, 50)
    zs = np.linspace(0, 5, 20)
    
    # We can profile out t0
    # t_calc = t0 + d/v => t0 = t_obs - d/v
    # We want to minimize sum( (t_obs - d/v - t0)^2 )
    # The optimal t0 is the mean of (t_obs - d/v)
    
    for x in xs:
        for y in ys:
            for z in zs:
                t_diffs = []
                for _, row in event_arrivals.iterrows():
                    sx, sy, sz = station_dict[row['station_id']]
                    d = np.sqrt((x-sx)**2 + (y-sy)**2 + (z-sz)**2)
                    t_diffs.append(row['arrival_s'] - d/v)
                
                t0 = np.mean(t_diffs)
                err = np.sum((np.array(t_diffs) - t0)**2)
                
                if err < best_err:
                    best_err = err
                    best_loc = (x, y, z, t0)
                    
    return best_loc, best_err

for v in [3.0, 4.0, 5.0, 6.0]:
    print(f"\nVelocity: {v}")
    for i, ev in enumerate(events):
        if len(ev) < 3:
            continue
        loc, err = grid_search(ev, v)
        print(f"Event {i}: x={loc[0]:.2f}, y={loc[1]:.2f}, z={loc[2]:.2f}, t0={loc[3]:.2f}, err={err:.4f}")
