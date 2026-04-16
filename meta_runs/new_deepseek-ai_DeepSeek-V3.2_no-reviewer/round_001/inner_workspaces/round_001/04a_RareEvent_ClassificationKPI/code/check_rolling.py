import pandas as pd
import numpy as np

# Load rolling TSI data
df = pd.read_csv('../outputs/rolling_tsi.csv')
print(f"Rolling TSI data shape: {df.shape}")
print(f"First 20 rows:")
print(df.head(20))
print(f"\nSummary statistics:")
print(df['rolling_tsi'].describe())

# Check how many non-NaN values
valid_tsi = df['rolling_tsi'].dropna()
print(f"\nNumber of valid TSI values: {len(valid_tsi)}")
print(f"Number of NaN values: {df['rolling_tsi'].isna().sum()}")