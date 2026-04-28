import pandas as pd
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

plt.figure(figsize=(10, 6))
for i, row in arrivals.iterrows():
    plt.plot(row['arrival_s'], row['station_id'], 'bo')

plt.xlabel('Arrival Time (s)')
plt.ylabel('Station ID')
plt.title('Arrival Times')
plt.grid(True)
plt.savefig('report/images/arrivals.png')
