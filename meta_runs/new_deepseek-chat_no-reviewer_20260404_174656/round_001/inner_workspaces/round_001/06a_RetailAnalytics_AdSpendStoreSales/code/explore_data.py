import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read the data
df = pd.read_csv('../data/store_monthly_sales.csv')

print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nMissing values:")
print(df.isnull().sum())
print("\nBasic statistics:")
print(df.describe())

# Check unique stores and time periods
print("\nUnique stores:", df['store_id'].nunique())
print("Unique months:", df['month'].nunique())
print("Unique years:", df['year'].nunique())
print("\nYear-month combinations:")
print(df.groupby(['year', 'month']).size().reset_index().head(12))

# Create a datetime column for easier time series analysis
df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')

# Check if data is balanced (same number of observations per store)
store_counts = df['store_id'].value_counts()
print("\nObservations per store:")
print(store_counts.describe())
print("\nStores with incomplete data:", (store_counts != store_counts.max()).sum())

# Save the dataframe with date column for later use
df.to_csv('../outputs/store_monthly_sales_with_date.csv', index=False)

print("\nExploration complete. Data saved to outputs/store_monthly_sales_with_date.csv")