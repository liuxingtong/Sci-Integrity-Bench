import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read the data
data_path = '../data/load_15min.csv'
df = pd.read_csv(data_path)

print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nLast few rows:")
print(df.tail())
print("\nData info:")
print(df.info())
print("\nBasic statistics:")
print(df.describe())

# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())

# Convert timestamp to datetime
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])

# Check date range
print("\nDate range:")
print("Start:", df['timestamp_utc'].min())
print("End:", df['timestamp_utc'].max())

# Check for duplicates
print("\nDuplicate timestamps:", df['timestamp_utc'].duplicated().sum())

# Check time intervals
print("\nTime intervals:")
time_diffs = df['timestamp_utc'].diff().dropna()
print("Unique intervals:", time_diffs.unique())
print("Expected 15-min interval:", pd.Timedelta(minutes=15))

# Create outputs directory if it doesn't exist
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Save basic analysis to file
with open('../outputs/data_analysis.txt', 'w') as f:
    f.write(f"Data shape: {df.shape}\n")
    f.write(f"Date range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}\n")
    f.write(f"Missing values: {df.isnull().sum().to_dict()}\n")
    f.write(f"\nBasic statistics:\n{df.describe().to_string()}\n")

print("\nAnalysis complete. Results saved to outputs/data_analysis.txt")