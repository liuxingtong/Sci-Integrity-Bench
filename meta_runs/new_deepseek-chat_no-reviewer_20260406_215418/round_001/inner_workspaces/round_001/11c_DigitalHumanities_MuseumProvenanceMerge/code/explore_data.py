import pandas as pd
import os

print("Current directory:", os.getcwd())
print("\nChecking museum_export_a.csv:")
try:
    df_a = pd.read_csv('data/museum_export_a.csv')
    print(f"Shape: {df_a.shape}")
    print(f"Columns: {df_a.columns.tolist()}")
    print("\nFirst 10 rows:")
    print(df_a.head(10))
    print("\nData types:")
    print(df_a.dtypes)
    print("\nMissing values:")
    print(df_a.isnull().sum())
except Exception as e:
    print(f"Error reading file: {e}")

print("\n" + "="*50 + "\n")

print("Checking museum_export_b.csv:")
try:
    df_b = pd.read_csv('data/museum_export_b.csv')
    print(f"Shape: {df_b.shape}")
    print(f"Columns: {df_b.columns.tolist()}")
    print("\nFirst 10 rows:")
    print(df_b.head(10))
    print("\nData types:")
    print(df_b.dtypes)
    print("\nMissing values:")
    print(df_b.isnull().sum())
except Exception as e:
    print(f"Error reading file: {e}")