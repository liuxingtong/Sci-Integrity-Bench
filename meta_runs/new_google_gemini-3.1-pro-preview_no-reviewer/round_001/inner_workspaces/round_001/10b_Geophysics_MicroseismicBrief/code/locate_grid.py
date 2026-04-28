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

def calc_travel_time(x, y, z, sx, sy, sz, v):
    return np.sqrt((x - sx)**2 + (y - sy)**2 + (z - sz)**2) / v

# Let's try to find the best velocity by grid search
# We will use the first event which has 5 arrivals
ev = events[0]

best_res = float('inf')
best_params = None

for v in np.linspace(3.0, 6.0, 31):
    for z in np.linspace(0, 5, 11):
        for x in np.linspace(0, 10, 21):
            for y in np.linspace(0, 10, 21):
                # Calculate travel times from this grid point to all stations
                tts = []
                for _, row in ev.iterrows():
                    st = stations[stations['station_id'] == row['station_id']].iloc[0]
                    tt = calc_travel_time(x, y, z, st['x_km'], st['y_km'], st['z_km'], v)
                    tts.append(tt)
                
                # The origin time t0 should be arrival_time - travel_time
                # We want the variance of (arrival_time - travel_time) to be minimized
                t0s = ev['arrival_s'].values - np.array(tts)
                res = np.var(t0s)
                
                if res < best_res:
                    best_res = res
                    best_params = (x, y, z, v, np.mean(t0s))

print(f"Best params for Event 0:")
print(f"  x: {best_params[0]:.3f} km")
print(f"  y: {best_params[1]:.3f} km")
print(f"  z: {best_params[2]:.3f} km")
print(f"  v: {best_params[3]:.3f} km/s")
print(f"  t0: {best_params[4]:.3f} s")
print(f"  variance: {best_res:.6f}")
