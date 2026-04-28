import pandas as pd

arrivals = pd.read_csv('data/arrival_times.csv')

events = [
    arrivals.iloc[0:5],
    arrivals.iloc[5:10],
    arrivals.iloc[10:12]
]

for i, ev in enumerate(events):
    print(f"Event {i} relative arrival times:")
    t0 = ev[ev['station_id'] == 'S0']['arrival_s'].values[0]
    for _, row in ev.iterrows():
        print(f"  {row['station_id']}: {row['arrival_s'] - t0:.4f}")
