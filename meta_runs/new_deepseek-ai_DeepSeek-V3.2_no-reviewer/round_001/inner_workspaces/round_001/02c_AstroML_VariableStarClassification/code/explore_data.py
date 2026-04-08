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

print("Training data shape:", train_df.shape)
print("Validation data shape:", val_df.shape)
print("Test data shape:", test_df.shape)

print("\nFirst few rows of training data:")
print(train_df.head())

print("\nData types:")
print(train_df.dtypes)

print("\nMissing values in training data:")
print(train_df.isnull().sum())

print("\nLabel distribution in training data:")
print(train_df['label'].value_counts())
print("Proportion of class 1:", train_df['label'].mean())

print("\nLabel distribution in validation data:")
print(val_df['label'].value_counts())
print("Proportion of class 1:", val_df['label'].mean())

print("\nLabel distribution in test data:")
print(test_df['label'].value_counts())
print("Proportion of class 1:", test_df['label'].mean())

# Analyze symbol_series characteristics
train_df['symbol_length'] = train_df['symbol_series'].apply(len)
val_df['symbol_length'] = val_df['symbol_series'].apply(len)
test_df['symbol_length'] = test_df['symbol_series'].apply(len)

print("\nSymbol series length statistics:")
print("Train - min:", train_df['symbol_length'].min(), "max:", train_df['symbol_length'].max(), 
      "mean:", train_df['symbol_length'].mean(), "std:", train_df['symbol_length'].std())
print("Val - min:", val_df['symbol_length'].min(), "max:", val_df['symbol_length'].max(), 
      "mean:", val_df['symbol_length'].mean(), "std:", val_df['symbol_length'].std())
print("Test - min:", test_df['symbol_length'].min(), "max:", test_df['symbol_length'].max(), 
      "mean:", test_df['symbol_length'].mean(), "std:", test_df['symbol_length'].std())

# Check unique symbols
all_symbols = ''.join(train_df['symbol_series'].tolist() + val_df['symbol_series'].tolist() + test_df['symbol_series'].tolist())
unique_symbols = set(all_symbols)
print("\nUnique symbols in all data:", unique_symbols)
print("Number of unique symbols:", len(unique_symbols))

# Check field_id distribution
print("\nField ID distribution in training data:")
print(train_df['field_id'].value_counts())

# Create output directory for figures
os.makedirs('../report/images', exist_ok=True)

# Plot label distribution
plt.figure(figsize=(10, 4))

plt.subplot(1, 3, 1)
train_df['label'].value_counts().sort_index().plot(kind='bar')
plt.title('Training Data Label Distribution')
plt.xlabel('Label')
plt.ylabel('Count')

plt.subplot(1, 3, 2)
val_df['label'].value_counts().sort_index().plot(kind='bar')
plt.title('Validation Data Label Distribution')
plt.xlabel('Label')
plt.ylabel('Count')

plt.subplot(1, 3, 3)
test_df['label'].value_counts().sort_index().plot(kind='bar')
plt.title('Test Data Label Distribution')
plt.xlabel('Label')
plt.ylabel('Count')

plt.tight_layout()
plt.savefig('../report/images/label_distribution.png', dpi=150)
plt.close()

# Plot symbol length distribution
plt.figure(figsize=(10, 4))

plt.subplot(1, 3, 1)
plt.hist(train_df['symbol_length'], bins=20, alpha=0.7, color='blue')
plt.title('Training Data Symbol Length')
plt.xlabel('Length')
plt.ylabel('Frequency')

plt.subplot(1, 3, 2)
plt.hist(val_df['symbol_length'], bins=20, alpha=0.7, color='green')
plt.title('Validation Data Symbol Length')
plt.xlabel('Length')
plt.ylabel('Frequency')

plt.subplot(1, 3, 3)
plt.hist(test_df['symbol_length'], bins=20, alpha=0.7, color='red')
plt.title('Test Data Symbol Length')
plt.xlabel('Length')
plt.ylabel('Frequency')

plt.tight_layout()
plt.savefig('../report/images/symbol_length_distribution.png', dpi=150)
plt.close()

print("\nExploration complete. Figures saved to report/images/")