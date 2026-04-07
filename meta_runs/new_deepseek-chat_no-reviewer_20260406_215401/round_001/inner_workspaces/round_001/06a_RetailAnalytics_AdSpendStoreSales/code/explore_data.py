import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load the data
df = pd.read_csv('../data/store_monthly_sales.csv')
print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nColumn info:")
print(df.info())
print("\nDescriptive statistics:")
print(df.describe())
print("\nMissing values:")
print(df.isnull().sum())

# Check store and time dimensions
print("\nUnique stores:", df['store_id'].nunique())
print("Unique months per store (should be 36):", df.groupby('store_id').size().unique())
print("Year range:", df['year'].min(), "to", df['year'].max())
print("Month range:", df['month'].min(), "to", df['month'].max())

# Create a datetime column for time series analysis
# Note: year values are 1,2,3 - assuming these represent years 2001, 2002, 2003
df['year_adj'] = df['year'] + 2000  # Convert 1,2,3 to 2001,2002,2003
df['date'] = pd.to_datetime(df['year_adj'].astype(str) + '-' + df['month'].astype(str) + '-01', format='%Y-%m-%d')
print("\nDate range:", df['date'].min(), "to", df['date'].max())

# Save the dataframe with date for later use
df.to_csv('../outputs/store_monthly_sales_with_date.csv', index=False)
print("\nData saved to outputs/store_monthly_sales_with_date.csv")