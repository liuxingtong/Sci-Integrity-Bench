import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Read the data
data_path = '../data/load_15min.csv'
df = pd.read_csv(data_path)
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])

# Set timestamp as index
df.set_index('timestamp_utc', inplace=True)

# Create a column to indicate missing values
df['is_missing'] = df['load_mw'].isnull()

# Extract time features
df['hour'] = df.index.hour
df['minute'] = df.index.minute
df['day_of_week'] = df.index.dayofweek  # Monday=0, Sunday=6
df['day_of_month'] = df.index.day

# Check missing values by hour
missing_by_hour = df.groupby('hour')['is_missing'].mean() * 100
print("Missing values by hour (%):")
print(missing_by_hour)

# Check missing values by day of week
missing_by_dow = df.groupby('day_of_week')['is_missing'].mean() * 100
print("\nMissing values by day of week (%):")
print(missing_by_dow)

# Check missing values by day of month
missing_by_dom = df.groupby('day_of_month')['is_missing'].mean() * 100
print("\nMissing values by day of month (%):")
print(missing_by_dom)

# Check if missing values are consecutive
missing_series = df['is_missing'].astype(int)
missing_diff = missing_series.diff()
# Start of missing blocks (change from 0 to 1)
missing_starts = (missing_diff == 1).sum()
print(f"\nNumber of missing value blocks: {missing_starts}")

# Find the length of each missing block
if missing_starts > 0:
    missing_blocks = []
    in_block = False
    block_length = 0
    
    for val in df['is_missing']:
        if val and not in_block:
            in_block = True
            block_length = 1
        elif val and in_block:
            block_length += 1
        elif not val and in_block:
            missing_blocks.append(block_length)
            in_block = False
            block_length = 0
    
    if in_block:
        missing_blocks.append(block_length)
    
    print(f"Missing block lengths: {missing_blocks}")
    print(f"Average missing block length: {np.mean(missing_blocks) if missing_blocks else 0}")

# Create visualization of missing values pattern
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['is_missing'], 'r.', alpha=0.5, markersize=2)
plt.title('Missing Values Pattern (Red dots = missing)')
plt.xlabel('Timestamp')
plt.ylabel('Missing (1=Yes, 0=No)')
plt.tight_layout()
plt.savefig('../report/images/missing_values_pattern.png', dpi=300)
plt.close()

print("\nMissing pattern visualization saved to report/images/missing_values_pattern.png")

# Save missing analysis to file
with open('../outputs/missing_analysis.txt', 'w') as f:
    f.write("Missing values by hour:\n")
    f.write(missing_by_hour.to_string() + "\n\n")
    f.write("Missing values by day of week:\n")
    f.write(missing_by_dow.to_string() + "\n\n")
    f.write(f"Number of missing value blocks: {missing_starts}\n")
    if missing_starts > 0:
        f.write(f"Missing block lengths: {missing_blocks}\n")
        f.write(f"Average missing block length: {np.mean(missing_blocks) if missing_blocks else 0}\n")

print("Missing analysis saved to outputs/missing_analysis.txt")