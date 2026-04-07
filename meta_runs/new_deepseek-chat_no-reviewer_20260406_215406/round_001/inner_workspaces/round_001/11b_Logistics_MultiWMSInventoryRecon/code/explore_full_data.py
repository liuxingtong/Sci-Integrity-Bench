import pandas as pd
import numpy as np

# Read the full files
alpha_df = pd.read_csv('data/wms_alpha.csv')
beta_df = pd.read_csv('data/wms_beta.csv')

print("=== WMS Alpha (full dataset) ===")
print(f"Rows: {len(alpha_df)}")
print(f"Columns: {list(alpha_df.columns)}")
print("\nFirst 10 rows:")
print(alpha_df.head(10))
print("\nLast 10 rows:")
print(alpha_df.tail(10))
print("\nSample of rows:")
print(alpha_df.sample(min(10, len(alpha_df))))

print("\n" + "="*80 + "\n")

print("=== WMS Beta (full dataset) ===")
print(f"Rows: {len(beta_df)}")
print(f"Columns: {list(beta_df.columns)}")
print("\nFirst 10 rows:")
print(beta_df.head(10))
print("\nLast 10 rows:")
print(beta_df.tail(10))
print("\nSample of rows:")
print(beta_df.sample(min(10, len(beta_df))))

# Check for any patterns or issues
print("\n" + "="*80 + "\n")
print("=== Data Quality Checks ===")

print("\nAlpha - Missing values:")
print(alpha_df.isnull().sum())

print("\nBeta - Missing values:")
print(beta_df.isnull().sum())

print("\nAlpha - Duplicate rows:")
print(f"{alpha_df.duplicated().sum()} duplicates")

print("\nBeta - Duplicate rows:")
print(f"{beta_df.duplicated().sum()} duplicates")
