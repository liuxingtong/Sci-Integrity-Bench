#!/usr/bin/env python3
"""Exploratory data analysis for microseismic data."""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

print("=== STATIONS DATA ===")
print(f"Shape: {stations.shape}")
print(f"Columns: {stations.columns.tolist()}")
print(stations.head(20))
print("\nData types:")
print(stations.dtypes)
print("\nDescriptive stats:")
print(stations.describe())

print("\n=== ARRIVAL TIMES DATA ===")
print(f"Shape: {arrivals.shape}")
print(f"Columns: {arrivals.columns.tolist()}")
print(arrivals.head(20))
print("\nData types:")
print(arrivals.dtypes)
print("\nDescriptive stats:")
print(arrivals.describe())

print("\n=== UNIQUE VALUES ===")
for col in arrivals.columns:
    n_unique = arrivals[col].nunique()
    print(f"{col}: {n_unique} unique values")
    if n_unique < 20:
        print(f"  Values: {sorted(arrivals[col].unique())}")

print("\n=== MISSING VALUES ===")
print("Stations:")
print(stations.isnull().sum())
print("\nArrivals:")
print(arrivals.isnull().sum())

# Save summary
with open('outputs/data_summary.txt', 'w') as f:
    f.write("=== STATIONS DATA ===\n")
    f.write(f"Shape: {stations.shape}\n")
    f.write(f"Columns: {stations.columns.tolist()}\n")
    f.write(str(stations.head(20)) + "\n")
    f.write("\nDescriptive stats:\n")
    f.write(str(stations.describe()) + "\n")
    
    f.write("\n=== ARRIVAL TIMES DATA ===\n")
    f.write(f"Shape: {arrivals.shape}\n")
    f.write(f"Columns: {arrivals.columns.tolist()}\n")
    f.write(str(arrivals.head(20)) + "\n")
    f.write("\nDescriptive stats:\n")
    f.write(str(arrivals.describe()) + "\n")

print("\nData exploration complete!")
