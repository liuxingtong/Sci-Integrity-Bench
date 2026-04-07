import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set up paths
data_dir = '../data'
train_path = os.path.join(data_dir, 'train.csv')
val_path = os.path.join(data_dir, 'val.csv')
test_path = os.path.join(data_dir, 'test.csv')

# Load data
train_df = pd.read_csv(train_path)
val_df = pd.read_csv(val_path)
test_df = pd.read_csv(test_path)

print("=== Dataset Sizes ===")
print(f"Training set: {len(train_df)} samples")
print(f"Validation set: {len(val_df)} samples")
print(f"Test set: {len(test_df)} samples")

print("\n=== Label Distribution ===")
print("Training set:")
print(train_df['label'].value_counts())
print(f"Balanced accuracy baseline: {max(train_df['label'].value_counts(normalize=True)):.3f}")

print("\nValidation set:")
print(val_df['label'].value_counts())

print("\nTest set:")
print(test_df['label'].value_counts())

print("\n=== Symbol Series Analysis ===")
# Check length of symbol series
train_df['series_length'] = train_df['symbol_series'].apply(len)
val_df['series_length'] = val_df['symbol_series'].apply(len)
test_df['series_length'] = test_df['symbol_series'].apply(len)

print(f"Training series length - min: {train_df['series_length'].min()}, max: {train_df['series_length'].max()}, mean: {train_df['series_length'].mean():.1f}")
print(f"Validation series length - min: {val_df['series_length'].min()}, max: {val_df['series_length'].max()}, mean: {val_df['series_length'].mean():.1f}")
print(f"Test series length - min: {test_df['series_length'].min()}, max: {test_df['series_length'].max()}, mean: {test_df['series_length'].mean():.1f}")

# Check unique symbols
all_series = ''.join(train_df['symbol_series'].tolist() + val_df['symbol_series'].tolist() + test_df['symbol_series'].tolist())
unique_symbols = set(all_series)
print(f"\nUnique symbols in all data: {unique_symbols}")
print(f"Number of unique symbols: {len(unique_symbols)}")

# Check field_id distribution
print("\n=== Field ID Distribution ===")
print("Training set:")
print(train_df['field_id'].value_counts())

print("\n=== Sample Data ===")
print(train_df.head())
