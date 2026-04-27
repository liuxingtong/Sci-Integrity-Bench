import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

# Let's look at the arrival times again.
# S0: 0.00, 2.50, 5.00
# S1: 0.50, 3.01, 5.49
# S2: 0.99, 3.47
# S3: 1.47, 4.04
# S4: 2.00, 4.50

# The time differences between the first and second "event" at each station:
# S0: 2.50 - (-0.0011) = 2.4982
# S1: 3.0080 - 0.5038 = 2.5042
# S2: 3.4739 - 0.9869 = 2.4870
# S3: 4.0351 - 1.4697 = 2.5654
# S4: 4.4978 - 2.0043 = 2.4935

# The time differences between the second and third "event" at each station:
# S0: 4.9968 - 2.4971 = 2.4997
# S1: 5.4902 - 3.0080 = 2.4822

# The time difference is almost exactly 2.5 seconds for all stations!
# This means the source is at the EXACT SAME LOCATION, and it's repeating every 2.5 seconds.
# This is a repeating microseismic event (multiplet) or a controlled source.
# Since the time differences are not perfectly 2.5s (e.g., S3 is 2.56s), there might be slight movement or noise.
# Let's assume it's a single location or a very tight cluster.
# Let's try to locate the first event again, maybe with a grid search over a larger area or different velocity.

# Let's plot the arrival times vs distance from S0 again, but print the values.
s0_x = stations[stations['station_id'] == 'S0']['x_km'].values[0]
s0_y = stations[stations['station_id'] == 'S0']['y_km'].values[0]

dists = []
for _, row in arrivals.iterrows():
    sx = stations[stations['station_id'] == row['station_id']]['x_km'].values[0]
    sy = stations[stations['station_id'] == row['station_id']]['y_km'].values[0]
    dist = np.sqrt((sx - s0_x)**2 + (sy - s0_y)**2)
    dists.append(dist)

arrivals['dist_to_s0'] = dists

print(arrivals.head(5))

# S0: dist 0, time 0
# S1: dist 1.77, time 0.50
# S4: dist 3.09, time 2.00
# S3: dist 3.67, time 1.47
# S2: dist 4.98, time 0.99

# Wait, the arrival times are NOT monotonically increasing with distance from S0!
# S2 is further from S0 than S4, but S2 arrives earlier (0.99s) than S4 (2.00s).
# This means the source is NOT at S0.
# Let's find the station with the earliest arrival. It's S0.
# But if S0 is the earliest, the source must be closest to S0.
# Let's check the distances from S0 again.
# S0 to S2 is 4.98 km. S0 to S4 is 3.09 km.
# If source is at S0, S4 should arrive before S2. But S2 arrives before S4.
# This means the source is closer to S2 than to S4, AND closer to S0 than to S2.
# Let's check the coordinates.
# S0: (1.65, 6.62)
# S1: (0.21, 5.58)
# S2: (5.11, 3.04)
# S3: (3.76, 9.62)
# S4: (4.61, 7.49)

# Let's do a proper grid search for the first event.
