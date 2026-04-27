import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

# The arrivals are roughly 0.5s apart.
# S0, S1, S2, S3, S4, S0, S1, S2, S3, S4, S0, S1
# This looks like a single moving source, or a sequence of events.
# If it's a single moving source, it's emitting continuously or at regular intervals.
# Wait, if it's a single event, the maximum travel time difference across the network is bounded by the network size / velocity.
# Network size is ~ 5km x 10km. Max distance ~ 11km.
# If v = 5 km/s, max travel time diff is ~ 2.2s.
# The arrivals span from 0 to 5.5s.
# So it could be 1 event if the velocity is very low, or multiple events.
# Let's try to locate it as a moving source or multiple events.
# Actually, if it's a microseismic brief, maybe it's a hydraulic fracture growing?
# Let's assume each arrival is a separate event? No, an event needs multiple station picks to be located.
# Wait, if the arrivals are S0, S1, S2, S3, S4, S0, S1, S2, S3, S4, S0, S1
# Maybe the events are:
# Event 1: S0, S1, S2, S3, S4 (times 0 to 2.0)
# Event 2: S0, S1, S2, S3, S4 (times 2.5 to 4.5)
# Event 3: S0, S1 (times 5.0 to 5.5)

# Let's check the order of arrivals for Event 1: S0 (-0.001), S1 (0.50), S2 (0.98), S3 (1.46), S4 (2.00)
# Event 2: S0 (2.49), S1 (3.00), S2 (3.47), S3 (4.03), S4 (4.49)
# The order is exactly the same! S0 -> S1 -> S2 -> S3 -> S4.
# This means the source is closest to S0, then S1, etc.
# Let's check station coordinates.
print(stations)
