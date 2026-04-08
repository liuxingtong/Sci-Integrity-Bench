import pandas as pd
import numpy as np
import os

# Create output directories if they don't exist
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Read both WMS exports
print("Reading WMS Alpha export...")
wms_alpha = pd.read_csv('../data/wms_alpha.csv')
print(f"WMS Alpha shape: {wms_alpha.shape}")
print(wms_alpha.head())
print("\nWMS Alpha columns:", wms_alpha.columns.tolist())
print("\nWMS Alpha dtypes:")
print(wms_alpha.dtypes)

print("\n" + "="*50 + "\n")

print("Reading WMS Beta export...")
wms_beta = pd.read_csv('../data/wms_beta.csv')
print(f"WMS Beta shape: {wms_beta.shape}")
print(wms_beta.head())
print("\nWMS Beta columns:", wms_beta.columns.tolist())
print("\nWMS Beta dtypes:")
print(wms_beta.dtypes)

# Standardize column names for reconciliation
print("\n" + "="*50)
print("Standardizing column names...")

# WMS Alpha standardization
wms_alpha_std = wms_alpha.rename(columns={
    'sku': 'SKU',
    'qty': 'Quantity',
    'warehouse': 'Warehouse',
    'as_of_utc': 'Timestamp'
})
wms_alpha_std['Source'] = 'WMS_Alpha'

# WMS Beta standardization
wms_beta_std = wms_beta.rename(columns={
    'SKU': 'SKU',
    'Quantity': 'Quantity',
    'Site': 'Warehouse',
    'timestamp_local': 'Timestamp'
})
wms_beta_std['Source'] = 'WMS_Beta'

print("\nStandardized WMS Alpha:")
print(wms_alpha_std.head())
print("\nStandardized WMS Beta:")
print(wms_beta_std.head())

# Save standardized data
wms_alpha_std.to_csv('../outputs/wms_alpha_standardized.csv', index=False)
wms_beta_std.to_csv('../outputs/wms_beta_standardized.csv', index=False)

print("\nStandardized data saved to outputs/")