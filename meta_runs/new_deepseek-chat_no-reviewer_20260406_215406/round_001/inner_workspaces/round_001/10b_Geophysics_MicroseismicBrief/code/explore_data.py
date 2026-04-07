import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Load data
stations = pd.read_csv('../data/stations.csv')
arrivals = pd.read_csv('../data/arrival_times.csv')

print("=== Stations Data ===")
print(stations)
print(f"\nNumber of stations: {len(stations)}")
print(f"Station IDs: {stations['station_id'].tolist()}")

print("\n=== Arrival Times Data ===")
print(arrivals)
print(f"\nNumber of arrival records: {len(arrivals)}")
print(f"Unique event IDs: {arrivals['event_id'].unique()}")
print(f"Number of unique events: {arrivals['event_id'].nunique()}")

# Check if each event has exactly 5 stations (S0-S4)
event_counts = arrivals.groupby('event_id').size()
print(f"\nEvents per station count:\n{event_counts.value_counts()}")

# Merge data to get coordinates for each arrival
arrivals_with_coords = pd.merge(arrivals, stations, on='station_id', how='left')
print("\n=== Arrivals with Coordinates ===")
print(arrivals_with_coords.head())

# Save merged data
os.makedirs('../outputs', exist_ok=True)
arrivals_with_coords.to_csv('../outputs/arrivals_with_coords.csv', index=False)
print("\nSaved merged data to ../outputs/arrivals_with_coords.csv")

# Basic statistics
print("\n=== Arrival Time Statistics ===")
print(f"Arrival time range: {arrivals['arrival_s'].min():.4f} to {arrivals['arrival_s'].max():.4f} s")
print(f"Mean arrival time: {arrivals['arrival_s'].mean():.4f} s")
print(f"Std dev of arrival times: {arrivals['arrival_s'].std():.4f} s")

# Check for negative arrival time (S0, event 0 has -0.0011)
negative_arrivals = arrivals[arrivals['arrival_s'] < 0]
print(f"\nNegative arrival times: {len(negative_arrivals)}")
print(negative_arrivals)