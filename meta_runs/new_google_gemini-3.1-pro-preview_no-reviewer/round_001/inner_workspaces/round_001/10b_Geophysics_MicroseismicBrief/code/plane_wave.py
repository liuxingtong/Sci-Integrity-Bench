import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

events = [
    arrivals.iloc[0:5],
    arrivals.iloc[5:10],
    arrivals.iloc[10:12]
]

for i, ev in enumerate(events):
    if len(ev) < 5:
        continue
    
    print(f"Event {i}:")
    X = []
    y = []
    for _, row in ev.iterrows():
        st = stations[stations['station_id'] == row['station_id']].iloc[0]
        X.append([st['x_km'], st['y_km'], st['z_km']])
        y.append(row['arrival_s'])
        
    X = np.array(X)
    y = np.array(y)
    
    reg = LinearRegression().fit(X[:, :2], y)
    print(f"  R^2: {reg.score(X[:, :2], y):.6f}")
    print(f"  Coef: {reg.coef_}")
    print(f"  Intercept: {reg.intercept_}")
    
    # Slowness vector
    sx, sy = reg.coef_
    slowness = np.sqrt(sx**2 + sy**2)
    velocity = 1 / slowness
    azimuth = np.degrees(np.arctan2(sx, sy))
    print(f"  Apparent velocity: {velocity:.3f} km/s")
    print(f"  Azimuth: {azimuth:.3f} deg")
