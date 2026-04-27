import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

# The event_id in the file is just 0 to 11, one for each row!
# This means the file doesn't group them into events.
# We need to group them by time.

plt.figure(figsize=(10, 4))
plt.plot(arrivals['arrival_s'], np.zeros(len(arrivals)), 'o')
for i, row in arrivals.iterrows():
    plt.text(row['arrival_s'], 0.01, row['station_id'], rotation=90)
plt.xlabel('Arrival Time (s)')
plt.yticks([])
plt.title('Arrival Times')
plt.tight_layout()
plt.savefig('outputs/arrivals_timeline.png')

# Let's look at the time differences
print(arrivals['arrival_s'].diff())
