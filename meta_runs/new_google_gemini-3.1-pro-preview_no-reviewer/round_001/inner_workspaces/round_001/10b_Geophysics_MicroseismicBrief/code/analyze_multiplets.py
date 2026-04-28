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

# Calculate relative arrival times for each event
rel_times = []
for i, ev in enumerate(events):
    if len(ev) < 2:
        continue
    
    # Use S0 as reference if available, else S1
    if 'S0' in ev['station_id'].values:
        ref_st = 'S0'
    else:
        ref_st = ev['station_id'].values[0]
        
    t0 = ev[ev['station_id'] == ref_st]['arrival_s'].values[0]
    
    ev_rel = {'event_id': i}
    for _, row in ev.iterrows():
        ev_rel[row['station_id']] = row['arrival_s'] - t0
        
    rel_times.append(ev_rel)

rel_df = pd.DataFrame(rel_times)
print("Relative arrival times:")
print(rel_df)

# Plot relative arrival times
plt.figure(figsize=(10, 6))
colors = ['blue', 'green', 'red']
for i, row in rel_df.iterrows():
    for st in ['S0', 'S1', 'S2', 'S3', 'S4']:
        if not pd.isna(row[st]):
            plt.scatter(row[st], st, marker='o', color=colors[int(row['event_id'])], label=f'Event {int(row["event_id"])}' if st == 'S0' else "")

# Deduplicate legend
handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(by_label.values(), by_label.keys())

plt.xlabel('Relative Arrival Time (s)')
plt.ylabel('Station ID')
plt.title('Relative Arrival Times (Multiplet Analysis)')
plt.grid(True)
plt.savefig('report/images/multiplets.png')
