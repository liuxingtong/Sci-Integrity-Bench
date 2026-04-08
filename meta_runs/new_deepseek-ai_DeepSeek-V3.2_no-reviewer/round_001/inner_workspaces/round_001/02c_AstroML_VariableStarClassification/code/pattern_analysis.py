import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import os

# Load data
data_dir = '../data'
train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))

# Separate variable and non-variable stars
variable_df = train_df[train_df['label'] == 1]
non_variable_df = train_df[train_df['label'] == 0]

print(f"Variable stars: {len(variable_df)}")
print(f"Non-variable stars: {len(non_variable_df)}")

# Analyze symbol frequencies by class
def analyze_symbol_frequencies(df, label):
    """Analyze symbol frequencies for a class"""
    all_sequences = ''.join(df['symbol_series'].tolist())
    total_symbols = len(all_sequences)
    
    symbol_counts = Counter(all_sequences)
    symbol_freq = {symbol: count/total_symbols for symbol, count in symbol_counts.items()}
    
    return symbol_freq

variable_freq = analyze_symbol_frequencies(variable_df, 'variable')
non_variable_freq = analyze_symbol_frequencies(non_variable_df, 'non_variable')

print("\nSymbol frequencies:")
print("Symbol\tVariable\tNon-variable\tDifference")
for symbol in sorted(variable_freq.keys()):
    var_freq = variable_freq.get(symbol, 0)
    non_var_freq = non_variable_freq.get(symbol, 0)
    diff = var_freq - non_var_freq
    print(f"{symbol}\t{var_freq:.4f}\t\t{non_var_freq:.4f}\t\t{diff:.4f}")

# Analyze bigram frequencies
def analyze_bigram_frequencies(df, label):
    """Analyze bigram frequencies for a class"""
    bigram_counts = Counter()
    total_bigrams = 0
    
    for sequence in df['symbol_series']:
        for i in range(len(sequence) - 1):
            bigram = sequence[i:i+2]
            bigram_counts[bigram] += 1
            total_bigrams += 1
    
    bigram_freq = {bigram: count/total_bigrams for bigram, count in bigram_counts.items()}
    return bigram_freq

variable_bigram_freq = analyze_bigram_frequencies(variable_df, 'variable')
non_variable_bigram_freq = analyze_bigram_frequencies(non_variable_df, 'non_variable')

# Find bigrams with largest difference
bigram_differences = []
all_bigrams = set(list(variable_bigram_freq.keys()) + list(non_variable_bigram_freq.keys()))

for bigram in all_bigrams:
    var_freq = variable_bigram_freq.get(bigram, 0)
    non_var_freq = non_variable_bigram_freq.get(bigram, 0)
    diff = var_freq - non_var_freq
    bigram_differences.append((bigram, var_freq, non_var_freq, diff))

# Sort by absolute difference
bigram_differences.sort(key=lambda x: abs(x[3]), reverse=True)

print("\nTop 20 bigrams with largest frequency differences:")
print("Bigram\tVariable\tNon-variable\tDifference")
for bigram, var_freq, non_var_freq, diff in bigram_differences[:20]:
    print(f"{bigram}\t{var_freq:.4f}\t\t{non_var_freq:.4f}\t\t{diff:.4f}")

# Analyze sequence patterns - look for specific motifs
def find_common_patterns(sequences, pattern_length=3, top_n=10):
    """Find most common patterns of given length"""
    pattern_counts = Counter()
    
    for seq in sequences:
        for i in range(len(seq) - pattern_length + 1):
            pattern = seq[i:i+pattern_length]
            pattern_counts[pattern] += 1
    
    return pattern_counts.most_common(top_n)

print("\nMost common 3-symbol patterns in variable stars:")
variable_patterns = find_common_patterns(variable_df['symbol_series'], pattern_length=3, top_n=10)
for pattern, count in variable_patterns:
    print(f"  {pattern}: {count}")

print("\nMost common 3-symbol patterns in non-variable stars:")
non_variable_patterns = find_common_patterns(non_variable_df['symbol_series'], pattern_length=3, top_n=10)
for pattern, count in non_variable_patterns:
    print(f"  {pattern}: {count}")

# Create visualizations
os.makedirs('../report/images', exist_ok=True)

# Plot symbol frequency comparison
plt.figure(figsize=(10, 6))
symbols = sorted(variable_freq.keys())
variable_freqs = [variable_freq.get(s, 0) for s in symbols]
non_variable_freqs = [non_variable_freq.get(s, 0) for s in symbols]

x = np.arange(len(symbols))
width = 0.35

plt.bar(x - width/2, variable_freqs, width, label='Variable', alpha=0.8)
plt.bar(x + width/2, non_variable_freqs, width, label='Non-variable', alpha=0.8)
plt.xlabel('Symbol')
plt.ylabel('Frequency')
plt.title('Symbol Frequency Comparison by Class')
plt.xticks(x, symbols)
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/symbol_frequency_comparison.png', dpi=150)
plt.close()

# Plot top bigram differences
plt.figure(figsize=(12, 6))
top_n = 15
bigrams = [b[0] for b in bigram_differences[:top_n]]
var_freqs = [b[1] for b in bigram_differences[:top_n]]
non_var_freqs = [b[2] for b in bigram_differences[:top_n]]

y = np.arange(len(bigrams))

plt.barh(y - width/2, var_freqs, width, label='Variable', alpha=0.8)
plt.barh(y + width/2, non_var_freqs, width, label='Non-variable', alpha=0.8)
plt.xlabel('Frequency')
plt.title(f'Top {top_n} Bigram Frequency Differences')
plt.yticks(y, bigrams)
plt.legend()
plt.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('../report/images/bigram_frequency_comparison.png', dpi=150)
plt.close()

# Analyze sequence complexity by class
def calculate_simple_complexity(sequence):
    """Calculate simple complexity measure"""
    # Number of unique symbols
    unique_symbols = len(set(sequence))
    
    # Number of transitions
    transitions = 0
    for i in range(1, len(sequence)):
        if sequence[i] != sequence[i-1]:
            transitions += 1
    
    return unique_symbols, transitions / (len(sequence) - 1) if len(sequence) > 1 else 0

print("\nComplexity analysis:")
variable_complexities = [calculate_simple_complexity(seq) for seq in variable_df['symbol_series']]
non_variable_complexities = [calculate_simple_complexity(seq) for seq in non_variable_df['symbol_series']]

variable_unique = [c[0] for c in variable_complexities]
variable_transition = [c[1] for c in variable_complexities]
non_variable_unique = [c[0] for c in non_variable_complexities]
non_variable_transition = [c[1] for c in non_variable_complexities]

print(f"Variable stars - Unique symbols: mean={np.mean(variable_unique):.2f}, std={np.std(variable_unique):.2f}")
print(f"Non-variable stars - Unique symbols: mean={np.mean(non_variable_unique):.2f}, std={np.std(non_variable_unique):.2f}")
print(f"Variable stars - Transition rate: mean={np.mean(variable_transition):.4f}, std={np.std(variable_transition):.4f}")
print(f"Non-variable stars - Transition rate: mean={np.mean(non_variable_transition):.4f}, std={np.std(non_variable_transition):.4f}")

# Plot complexity comparison
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.hist(variable_unique, alpha=0.7, label='Variable', bins=range(1, 9), density=True)
plt.hist(non_variable_unique, alpha=0.7, label='Non-variable', bins=range(1, 9), density=True)
plt.xlabel('Number of Unique Symbols')
plt.ylabel('Density')
plt.title('Unique Symbols Distribution')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
plt.hist(variable_transition, alpha=0.7, label='Variable', bins=20, density=True)
plt.hist(non_variable_transition, alpha=0.7, label='Non-variable', bins=20, density=True)
plt.xlabel('Transition Rate')
plt.ylabel('Density')
plt.title('Transition Rate Distribution')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/complexity_comparison.png', dpi=150)
plt.close()

print("\nPattern analysis complete. Figures saved to report/images/")