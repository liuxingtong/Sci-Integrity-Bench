import pandas as pd

alpha = pd.read_csv('data/wms_alpha.csv')
beta = pd.read_csv('data/wms_beta.csv')

print('Alpha shape:', alpha.shape)
print('Beta shape:', beta.shape)

print('\nAlpha columns:', alpha.columns.tolist())
print('Beta columns:', beta.columns.tolist())

print('\nAlpha warehouses:', alpha['warehouse'].unique())
print('Beta sites:', beta['Site'].unique())

print('\nAlpha SKUs:', alpha['sku'].nunique())
print('Beta SKUs:', beta['SKU'].nunique())

print('\nAlpha dates:', alpha['as_of_utc'].min(), 'to', alpha['as_of_utc'].max())
print('Beta dates:', beta['timestamp_local'].min(), 'to', beta['timestamp_local'].max())
