import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

# If event_id is 0 to 11, maybe it's a mistake in the data generation and they are actually 3 events?
# Let's assume they are 3 events: 0-4, 5-9, 10-11.
# But the residuals are very high (~0.8s) for 5 stations. This means the model (constant velocity, single point source) doesn't fit well.
# Let's check the distances between stations.

for i in range(len(stations)):
    for j in range(i+1, len(stations)):
        dx = stations.iloc[i]['x_km'] - stations.iloc[j]['x_km']
        dy = stations.iloc[i]['y_km'] - stations.iloc[j]['y_km']
        dist = np.sqrt(dx**2 + dy**2)
        print(f"{stations.iloc[i]['station_id']} to {stations.iloc[j]['station_id']}: {dist:.2f} km")

# Let's plot the arrival times vs distance from S0.
# Since S0 is the first arrival for both "events", maybe the source is near S0.

s0_x = stations[stations['station_id'] == 'S0']['x_km'].values[0]
s0_y = stations[stations['station_id'] == 'S0']['y_km'].values[0]

dists = []
for _, row in arrivals.iterrows():
    sx = stations[stations['station_id'] == row['station_id']]['x_km'].values[0]
    sy = stations[stations['station_id'] == row['station_id']]['y_km'].values[0]
    dist = np.sqrt((sx - s0_x)**2 + (sy - s0_y)**2)
    dists.append(dist)

arrivals['dist_to_s0'] = dists

plt.figure()
plt.plot(arrivals['dist_to_s0'][:5], arrivals['arrival_s'][:5], 'o', label='Event 1')
plt.plot(arrivals['dist_to_s0'][5:10], arrivals['arrival_s'][5:10], 'x', label='Event 2')
plt.xlabel('Distance to S0 (km)')
plt.ylabel('Arrival Time (s)')
plt.legend()
plt.savefig('outputs/dist_vs_time.png')
