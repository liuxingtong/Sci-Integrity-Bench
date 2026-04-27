import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

# Let's look at the arrival times again. Maybe they are not 3 events.
print(arrivals)

# Let's plot arrival time vs distance from a hypothetical source.
# Or maybe we can just do a grid search over the whole space for each event.
# Wait, the event_id is in the file!
print(arrivals.groupby('event_id').size())
