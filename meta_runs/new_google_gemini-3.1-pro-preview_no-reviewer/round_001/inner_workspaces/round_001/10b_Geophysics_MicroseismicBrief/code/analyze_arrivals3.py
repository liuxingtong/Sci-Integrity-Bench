import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

# Let's look at the arrival times again. Maybe they are not 3 events.
# What if it's a single event and the arrivals are just different phases? No, it says "P-wave picks".
# What if the event_id in the file is actually the event ID, and there are 12 events, each with 1 pick?
# "Station coordinates are in stations.csv; arrival picks in arrival_times.csv. Prepare a microseismic analysis brief on source clustering and structural context."
# If there are 12 events, each with 1 pick, we can't locate them.
# Wait, the event_id column in arrival_times.csv is 0 to 11.
# Let's check the file again.
print(arrivals)
