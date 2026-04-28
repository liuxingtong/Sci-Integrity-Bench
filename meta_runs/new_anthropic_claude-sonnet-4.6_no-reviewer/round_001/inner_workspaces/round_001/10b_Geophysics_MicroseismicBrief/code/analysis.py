#!/usr/bin/env python3
"""Comprehensive microseismic analysis: source location, clustering, and structural context."""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from scipy.spatial.distance import cdist
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.optimize import minimize
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')
import os

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# ============================================================
# 1. LOAD DATA
# ============================================================
stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

print("Stations:")
print(stations)
print("\nArrivals (first 20):")
print(arrivals.head(20))
print("\nArrivals columns:", arrivals.columns.tolist())
print("Arrivals shape:", arrivals.shape)

# ============================================================
# 2. DATA PREPROCESSING
# ============================================================
# Identify column names
print("\nStation columns:", stations.columns.tolist())
print("Arrival columns:", arrivals.columns.tolist())

# Standardize column names
stations.columns = [c.strip().lower() for c in stations.columns]
arrivals.columns = [c.strip().lower() for c in arrivals.columns]

print("\nStandardized station columns:", stations.columns.tolist())
print("Standardized arrival columns:", arrivals.columns.tolist())
print("\nStations:")
print(stations)
print("\nArrivals:")
print(arrivals.head(30))

# Save data summary
with open('outputs/data_summary.txt', 'w') as f:
    f.write("STATIONS:\n")
    f.write(stations.to_string())
    f.write("\n\nARRIVALS (first 50):\n")
    f.write(arrivals.head(50).to_string())
    f.write("\n\nARRIVALS STATS:\n")
    f.write(arrivals.describe().to_string())

print("\nData summary saved.")
