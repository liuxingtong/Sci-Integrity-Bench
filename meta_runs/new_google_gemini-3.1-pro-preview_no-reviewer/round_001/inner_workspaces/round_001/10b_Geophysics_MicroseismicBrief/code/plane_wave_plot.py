import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

events = [
    arrivals.iloc[0:5],
    arrivals.iloc[5:10],
    arrivals.iloc[10:12]
]

plt.figure(figsize=(8, 8))
plt.scatter(stations['x_km'], stations['y_km'], marker='^', s=100, c='red', label='Stations')
for i, row in stations.iterrows():
    plt.text(row['x_km']+0.1, row['y_km']+0.1, row['station_id'])

colors = ['blue', 'green']
for i, ev in enumerate(events[:2]):
    X = []
    y = []
    for _, row in ev.iterrows():
        st = stations[stations['station_id'] == row['station_id']].iloc[0]
        X.append([st['x_km'], st['y_km'], st['z_km']])
        y.append(row['arrival_s'])
        
    X = np.array(X)
    y = np.array(y)
    
    reg = LinearRegression().fit(X[:, :2], y)
    sx, sy = reg.coef_
    
    # Plot slowness vector direction
    center_x = np.mean(X[:, 0])
    center_y = np.mean(X[:, 1])
    
    # The wave comes FROM the opposite direction of the slowness vector
    dx = -sx * 10
    dy = -sy * 10
    
    plt.arrow(center_x - dx/2, center_y - dy/2, dx, dy, head_width=0.3, head_length=0.5, fc=colors[i], ec=colors[i], label=f'Event {i} direction')

plt.xlabel('X (km)')
plt.ylabel('Y (km)')
plt.title('Station Locations and Wave Arrival Directions')
plt.legend()
plt.grid(True)
plt.savefig('report/images/directions.png')
