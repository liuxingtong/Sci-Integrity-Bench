import pandas as pd
import os

print("Reading wms_alpha.csv...")
alpha_df = pd.read_csv('data/wms_alpha.csv')
print(f"Alpha shape: {alpha_df.shape}")
print("Alpha head:")
print(alpha_df.head())
print("\nAlpha info:")
print(alpha_df.info())
print("\nAlpha describe:")
print(alpha_df.describe())
print("\nAlpha unique values:")
for col in alpha_df.columns:
    print(f"{col}: {alpha_df[col].nunique()} unique values")

print("\n" + "="*50 + "\n")

print("Reading wms_beta.csv...")
beta_df = pd.read_csv('data/wms_beta.csv')
print(f"Beta shape: {beta_df.shape}")
print("Beta head:")
print(beta_df.head())
print("\nBeta info:")
print(beta_df.info())
print("\nBeta describe:")
print(beta_df.describe())
print("\nBeta unique values:")
for col in beta_df.columns:
    print(f"{col}: {beta_df[col].nunique()} unique values")
