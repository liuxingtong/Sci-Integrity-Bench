import pandas as pd
import numpy as np
import re
import os

# Read the data files
print("Reading data files...")
df_a = pd.read_csv('../data/museum_export_a.csv', skiprows=2)  # Skip header rows
df_b = pd.read_csv('../data/museum_export_b.csv', skiprows=2)  # Skip header rows

print("\nBatch A shape:", df_a.shape)
print("Batch B shape:", df_b.shape)

print("\nBatch A columns:", df_a.columns.tolist())
print("Batch B columns:", df_b.columns.tolist())

print("\nBatch A first few rows:")
print(df_a.head())
print("\nBatch B first few rows:")
print(df_b.head())

print("\nBatch A info:")
df_a.info()
print("\nBatch B info:")
df_b.info()

# Check for footer rows
print("\nChecking for footer rows in Batch A:")
print(df_a.tail())
print("\nChecking for footer rows in Batch B:")
print(df_b.tail())