import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# Load data
stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

print(stations)
print(arrivals)

# Group arrivals into events based on time proximity
# It looks like there are 3 events, roughly at t=0, t=2.5, t=5.0
# Let's just group them manually for now to see
events = []
events.append(arrivals.iloc[0:5])
events.append(arrivals.iloc[5:10])
events.append(arrivals.iloc[10:12])

for i, ev in enumerate(events):
    print(f'Event {i}:')
    print(ev)
