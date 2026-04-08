import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
df = pd.read_csv('data/store_monthly_sales.csv')

print("=== Data Overview ===")
print(f"Shape: {df.shape}")
print(f"\nColumns: {df.columns.tolist()}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nMissing values:\n{df.isnull().sum()}")
print(f"\nBasic statistics:\n{df.describe()}")

print(f"\n=== Unique Values ===")
print(f"Number of stores: {df['store_id'].nunique()}")
print(f"Years: {sorted(df['year'].unique())}")
print(f"Months: {sorted(df['month'].unique())}")
print(f"Holiday months: {df['is_holiday_month'].value_counts().to_dict()}")

# Check for any missing values in key columns
print(f"\n=== Missing Value Check ===")
for col in df.columns:
    missing = df[col].isnull().sum()
    if missing > 0:
        print(f"{col}: {missing} missing values")

# Save overview
overview_text = f"""Data Overview:
- Shape: {df.shape}
- Stores: {df['store_id'].nunique()}
- Years: {sorted(df['year'].unique())}
- Months per year: {sorted(df['month'].unique())}
- Holiday months indicator: {df['is_holiday_month'].value_counts().to_dict()}
"""
with open('outputs/data_overview.txt', 'w') as f:
    f.write(overview_text)

print("\nData overview saved to outputs/data_overview.txt")
