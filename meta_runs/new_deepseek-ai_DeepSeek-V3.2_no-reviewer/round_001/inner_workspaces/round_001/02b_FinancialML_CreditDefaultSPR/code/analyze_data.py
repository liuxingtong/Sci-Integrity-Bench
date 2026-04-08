import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load data
train = pd.read_csv('../data/train.csv')
val = pd.read_csv('../data/val.csv')
test = pd.read_csv('../data/test.csv')

print("=== Data Overview ===")
print(f"Train shape: {train.shape}")
print(f"Validation shape: {val.shape}")
print(f"Test shape: {test.shape}")

print("\n=== Target Distribution ===")
print(f"Train default rate: {train['default_flag'].mean():.3f} ({train['default_flag'].sum()}/{len(train)})")
print(f"Val default rate: {val['default_flag'].mean():.3f} ({val['default_flag'].sum()}/{len(val)})")
print(f"Test default rate: {test['default_flag'].mean():.3f} ({test['default_flag'].sum()}/{len(test)})")

print("\n=== Symbolic Sequence Analysis ===")
# Check sequence lengths
for name, df in [('Train', train), ('Val', val), ('Test', test)]:
    seq_lengths = df['sym_seq'].apply(len)
    print(f"{name} sequence length - min: {seq_lengths.min()}, max: {seq_lengths.max()}, mean: {seq_lengths.mean():.1f}")

# Check unique symbols
all_sequences = pd.concat([train['sym_seq'], val['sym_seq'], test['sym_seq']])
all_symbols = set(''.join(all_sequences))
print(f"\nUnique symbols in all sequences: {sorted(all_symbols)}")
print(f"Number of unique symbols: {len(all_symbols)}")

# Check symbol frequencies
symbol_counts = {}
for seq in all_sequences:
    for char in seq:
        symbol_counts[char] = symbol_counts.get(char, 0) + 1

print("\nSymbol frequencies:")
for symbol in sorted(symbol_counts.keys()):
    print(f"  {symbol}: {symbol_counts[symbol]}")

# Create output directory
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Plot target distribution
plt.figure(figsize=(10, 4))
plt.subplot(1, 3, 1)
train['default_flag'].value_counts().plot(kind='bar', color=['skyblue', 'salmon'])
plt.title('Train Set Target Distribution')
plt.xlabel('Default Flag')
plt.ylabel('Count')
plt.xticks([0, 1], ['0 (No Default)', '1 (Default)'], rotation=0)

plt.subplot(1, 3, 2)
val['default_flag'].value_counts().plot(kind='bar', color=['skyblue', 'salmon'])
plt.title('Validation Set Target Distribution')
plt.xlabel('Default Flag')
plt.ylabel('Count')
plt.xticks([0, 1], ['0 (No Default)', '1 (Default)'], rotation=0)

plt.subplot(1, 3, 3)
test['default_flag'].value_counts().plot(kind='bar', color=['skyblue', 'salmon'])
plt.title('Test Set Target Distribution')
plt.xlabel('Default Flag')
plt.ylabel('Count')
plt.xticks([0, 1], ['0 (No Default)', '1 (Default)'], rotation=0)

plt.tight_layout()
plt.savefig('report/images/target_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n=== First few sequences ===")
print(train.head(10))

# Save analysis summary
with open('outputs/data_analysis.txt', 'w') as f:
    f.write("Data Analysis Summary\n")
    f.write("="*50 + "\n")
    f.write(f"Train samples: {len(train)}\n")
    f.write(f"Validation samples: {len(val)}\n")
    f.write(f"Test samples: {len(test)}\n")
    f.write(f"\nTarget distribution:\n")
    f.write(f"  Train default rate: {train['default_flag'].mean():.3f}\n")
    f.write(f"  Val default rate: {val['default_flag'].mean():.3f}\n")
    f.write(f"  Test default rate: {test['default_flag'].mean():.3f}\n")
    f.write(f"\nSequence length: {train['sym_seq'].apply(len).iloc[0]} characters\n")
    f.write(f"Unique symbols: {sorted(all_symbols)}\n")
    f.write(f"Number of unique symbols: {len(all_symbols)}\n")