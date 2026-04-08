import pandas as pd
import os

print("Examining museum_export_a.csv...")
df_a = pd.read_csv('data/museum_export_a.csv')
print(f"Shape: {df_a.shape}")
print(f"Columns: {df_a.columns.tolist()}")
print("\nFirst 10 rows:")
print(df_a.head(10))
print("\nInfo:")
print(df_a.info())

print("\n" + "="*50 + "\n")

print("Examining museum_export_b.csv...")
df_b = pd.read_csv('data/museum_export_b.csv')
print(f"Shape: {df_b.shape}")
print(f"Columns: {df_b.columns.tolist()}")
print("\nFirst 10 rows:")
print(df_b.head(10))
print("\nInfo:")
print(df_b.info())