import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Load data
stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

print("=== Stations Data ===")
print(stations)
print(f"\nNumber of stations: {len(stations)}")
print(f"Station IDs: {stations['station_id'].tolist()}")

print("\n=== Arrival Times Data ===")
print(arrivals)
print(f"\nNumber of arrival picks: {len(arrivals)}")
print(f"Unique event IDs: {arrivals['event_id'].nunique()}")
print(f"Unique station IDs in arrivals: {arrivals['station_id'].nunique()}")

# Check if all stations have picks
stations_with_picks = arrivals['station_id'].unique()
print(f"\nStations with picks: {stations_with_picks}")
print(f"Stations without picks: {set(stations['station_id']) - set(stations_with_picks)}")

# Group by event_id to see how many stations per event
event_stats = arrivals.groupby('event_id').agg({
    'station_id': 'count',
    'arrival_s': ['min', 'max', 'mean']
}).reset_index()
event_stats.columns = ['event_id', 'num_stations', 'min_arrival', 'max_arrival', 'mean_arrival']
print("\n=== Event Statistics ===")
print(event_stats)

# Check distribution of arrivals per station
station_stats = arrivals.groupby('station_id').agg({
    'event_id': 'count',
    'arrival_s': ['min', 'max', 'mean']
}).reset_index()
station_stats.columns = ['station_id', 'num_events', 'min_arrival', 'max_arrival', 'mean_arrival']
print("\n=== Station Statistics ===")
print(station_stats)

# Create output directory
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Save statistics to CSV
stations.to_csv('outputs/stations_processed.csv', index=False)
arrivals.to_csv('outputs/arrivals_processed.csv', index=False)
event_stats.to_csv('outputs/event_stats.csv', index=False)
station_stats.to_csv('outputs/station_stats.csv', index=False)

print("\nData analysis complete. Files saved to outputs/ directory.")