import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

print(stations)
print(arrivals)

# Plot stations
plt.figure(figsize=(8, 8))
plt.scatter(stations['x_km'], stations['y_km'], marker='^', s=100, c='red', label='Stations')
for i, row in stations.iterrows():
    plt.text(row['x_km'] + 0.1, row['y_km'] + 0.1, row['station_id'])
plt.xlabel('X (km)')
plt.ylabel('Y (km)')
plt.title('Station Locations')
plt.legend()
plt.grid(True)
plt.savefig('outputs/stations.png')
