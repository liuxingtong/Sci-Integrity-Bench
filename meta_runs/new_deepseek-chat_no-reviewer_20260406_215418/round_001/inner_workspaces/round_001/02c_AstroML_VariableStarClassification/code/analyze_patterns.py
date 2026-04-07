import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import os

# Set up paths
data_dir = '../data'
output_dir = '../outputs'
report_img_dir = '../report/images'

# Load data
train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))

# Separate variable and non-variable stars
variable = train_df[train_df['label'] == 1]
non_variable = train_df[train_df['label'] == 0]

print(f"Variable stars: {len(variable)}")
print(f"Non-variable stars: {len(non_variable)}")

# Define symbols
symbols = ['*', 'v', 'w', 'z', 'y', 'u', '.', 'x']

# Analyze symbol frequencies by class
print("\n=== Symbol Frequencies ===")
print("Variable stars:")
var_symbols = ''.join(variable['symbol_series'].tolist())
var_counts = Counter(var_symbols)
total_var = len(var_symbols)
for sym in symbols:
    freq = var_counts.get(sym, 0) / total_var
    print(f"  {sym}: {freq:.4f}")

print("\nNon-variable stars:")
nonvar_symbols = ''.join(non_variable['symbol_series'].tolist())
nonvar_counts = Counter(nonvar_symbols)
total_nonvar = len(nonvar_symbols)
for sym in symbols:
    freq = nonvar_counts.get(sym, 0) / total_nonvar
    print(f"  {sym}: {freq:.4f}")

# Calculate differences
print("\n=== Frequency Differences (Variable - Non-variable) ===")
for sym in symbols:
    var_freq = var_counts.get(sym, 0) / total_var
    nonvar_freq = nonvar_counts.get(sym, 0) / total_nonvar
    diff = var_freq - nonvar_freq
    print(f"  {sym}: {diff:+.4f}")

# Analyze position-specific patterns
print("\n=== Position Analysis ===")
# Convert to position matrices
max_len = 40

var_pos_matrix = np.zeros((max_len, len(symbols)))
nonvar_pos_matrix = np.zeros((max_len, len(symbols)))

symbol_to_idx = {sym: i for i, sym in enumerate(symbols)}

for series in variable['symbol_series']:
    for pos, sym in enumerate(series[:max_len]):
        var_pos_matrix[pos, symbol_to_idx[sym]] += 1

for series in non_variable['symbol_series']:
    for pos, sym in enumerate(series[:max_len]):
        nonvar_pos_matrix[pos, symbol_to_idx[sym]] += 1

# Normalize
var_pos_matrix = var_pos_matrix / len(variable)
nonvar_pos_matrix = nonvar_pos_matrix / len(non_variable)

# Find positions with biggest differences
print("\nPositions with largest frequency differences:")
for sym in symbols:
    idx = symbol_to_idx[sym]
    diffs = var_pos_matrix[:, idx] - nonvar_pos_matrix[:, idx]
    max_pos = np.argmax(np.abs(diffs))
    max_diff = diffs[max_pos]
    print(f"  {sym}: position {max_pos}, diff = {max_diff:+.4f}")

# Plot symbol frequencies by class
plt.figure(figsize=(10, 6))
x = np.arange(len(symbols))
width = 0.35

var_freqs = [var_counts.get(sym, 0) / total_var for sym in symbols]
nonvar_freqs = [nonvar_counts.get(sym, 0) / total_nonvar for sym in symbols]

plt.bar(x - width/2, var_freqs, width, label='Variable', color='red', alpha=0.7)
plt.bar(x + width/2, nonvar_freqs, width, label='Non-variable', color='blue', alpha=0.7)

plt.xlabel('Symbol')
plt.ylabel('Frequency')
plt.title('Symbol Frequencies by Class')
plt.xticks(x, symbols)
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(report_img_dir, 'symbol_frequencies.png'), dpi=150)
plt.close()

# Plot position-specific patterns for key symbols
key_symbols = ['*', 'v', '.']  # Bright, medium, dim
fig, axes = plt.subplots(len(key_symbols), 1, figsize=(12, 10))

for i, sym in enumerate(key_symbols):
    idx = symbol_to_idx[sym]
    axes[i].plot(var_pos_matrix[:, idx], 'r-', label='Variable', alpha=0.7)
    axes[i].plot(nonvar_pos_matrix[:, idx], 'b-', label='Non-variable', alpha=0.7)
    axes[i].set_ylabel(f'Freq of {sym}')
    axes[i].set_xlabel('Position')
    axes[i].legend()
    axes[i].grid(alpha=0.3)

plt.suptitle('Position-Specific Symbol Frequencies')
plt.tight_layout()
plt.savefig(os.path.join(report_img_dir, 'position_patterns.png'), dpi=150)
plt.close()

# Analyze transition patterns
print("\n=== Transition Analysis ===")
# Calculate transition matrices
var_trans = np.zeros((len(symbols), len(symbols)))
nonvar_trans = np.zeros((len(symbols), len(symbols)))

for series in variable['symbol_series']:
    for i in range(len(series) - 1):
        idx1 = symbol_to_idx[series[i]]
        idx2 = symbol_to_idx[series[i+1]]
        var_trans[idx1, idx2] += 1

for series in non_variable['symbol_series']:
    for i in range(len(series) - 1):
        idx1 = symbol_to_idx[series[i]]
        idx2 = symbol_to_idx[series[i+1]]
        nonvar_trans[idx1, idx2] += 1

# Normalize by row
var_trans = var_trans / var_trans.sum(axis=1, keepdims=True)
nonvar_trans = nonvar_trans / nonvar_trans.sum(axis=1, keepdims=True)

# Find most different transitions
print("\nMost different transitions (Variable - Non-variable):")
transition_diffs = []
for i, sym1 in enumerate(symbols):
    for j, sym2 in enumerate(symbols):
        diff = var_trans[i, j] - nonvar_trans[i, j]
        transition_diffs.append((abs(diff), sym1, sym2, diff))

transition_diffs.sort(reverse=True)
for i in range(10):
    diff_abs, sym1, sym2, diff = transition_diffs[i]
    print(f"  {sym1}->{sym2}: {diff:+.4f}")

print("\nPattern analysis complete!")
