import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import os

# Load data
data_dir = '../data'
train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))

# Convert symbols to numerical values for visualization
symbol_to_num = {'w': 0, '.': 1, '*': 2, 'x': 3, 'z': 4, 'v': 5, 'y': 6, 'u': 7}

# Create output directory
os.makedirs('../report/images', exist_ok=True)

# Visualize sample sequences
plt.figure(figsize=(15, 10))

# Select some examples from each class
variable_examples = train_df[train_df['label'] == 1].head(5)['symbol_series'].values
non_variable_examples = train_df[train_df['label'] == 0].head(5)['symbol_series'].values

# Plot variable star sequences
for i, seq in enumerate(variable_examples):
    plt.subplot(2, 5, i + 1)
    numeric_seq = [symbol_to_num[s] for s in seq]
    plt.plot(numeric_seq, marker='o', markersize=3)
    plt.title(f'Variable Star Example {i+1}')
    plt.xlabel('Position')
    plt.ylabel('Symbol Value')
    plt.ylim(-0.5, 7.5)
    plt.grid(True, alpha=0.3)
    
    # Add sequence as text
    plt.text(0, -1, seq[:20], fontsize=8, ha='left')
    plt.text(20, -1, seq[20:], fontsize=8, ha='left')

# Plot non-variable star sequences
for i, seq in enumerate(non_variable_examples):
    plt.subplot(2, 5, i + 6)
    numeric_seq = [symbol_to_num[s] for s in seq]
    plt.plot(numeric_seq, marker='o', markersize=3)
    plt.title(f'Non-variable Star Example {i+1}')
    plt.xlabel('Position')
    plt.ylabel('Symbol Value')
    plt.ylim(-0.5, 7.5)
    plt.grid(True, alpha=0.3)
    
    # Add sequence as text
    plt.text(0, -1, seq[:20], fontsize=8, ha='left')
    plt.text(20, -1, seq[20:], fontsize=8, ha='left')

plt.tight_layout()
plt.savefig('../report/images/sequence_visualization.png', dpi=150, bbox_inches='tight')
plt.close()

# Analyze positional patterns
def analyze_positional_patterns(df, label_name):
    """Analyze symbol frequencies at each position"""
    sequences = df['symbol_series'].values
    n_positions = len(sequences[0]) if len(sequences) > 0 else 0
    
    # Initialize counters for each position
    position_counts = [Counter() for _ in range(n_positions)]
    
    for seq in sequences:
        for pos, symbol in enumerate(seq):
            position_counts[pos][symbol] += 1
    
    return position_counts

variable_pos_counts = analyze_positional_patterns(train_df[train_df['label'] == 1], 'variable')
non_variable_pos_counts = analyze_positional_patterns(train_df[train_df['label'] == 0], 'non_variable')

# Find positions with largest differences
n_positions = len(variable_pos_counts)
position_differences = []

for pos in range(n_positions):
    var_counts = variable_pos_counts[pos]
    non_var_counts = non_variable_pos_counts[pos]
    
    # Calculate total
    var_total = sum(var_counts.values())
    non_var_total = sum(non_var_counts.values())
    
    # Calculate difference for each symbol
    for symbol in symbol_to_num.keys():
        var_freq = var_counts.get(symbol, 0) / var_total if var_total > 0 else 0
        non_var_freq = non_var_counts.get(symbol, 0) / non_var_total if non_var_total > 0 else 0
        diff = var_freq - non_var_freq
        
        if abs(diff) > 0.1:  # Only record large differences
            position_differences.append((pos, symbol, var_freq, non_var_freq, diff))

print(f"\nPositions with large symbol frequency differences (>0.1):")
print("Position\tSymbol\tVariable\tNon-variable\tDifference")
for pos, symbol, var_freq, non_var_freq, diff in position_differences[:20]:
    print(f"{pos}\t\t{symbol}\t{var_freq:.3f}\t\t{non_var_freq:.3f}\t\t{diff:.3f}")

# Visualize positional symbol frequencies
plt.figure(figsize=(15, 8))

symbols = list(symbol_to_num.keys())
n_symbols = len(symbols)

for i, symbol in enumerate(symbols):
    plt.subplot(2, 4, i + 1)
    
    var_freqs = [variable_pos_counts[pos].get(symbol, 0) / sum(variable_pos_counts[pos].values()) 
                 for pos in range(n_positions)]
    non_var_freqs = [non_variable_pos_counts[pos].get(symbol, 0) / sum(non_variable_pos_counts[pos].values()) 
                     for pos in range(n_positions)]
    
    plt.plot(var_freqs, label='Variable', alpha=0.7)
    plt.plot(non_var_freqs, label='Non-variable', alpha=0.7)
    plt.title(f"Symbol '{symbol}' Frequency by Position")
    plt.xlabel('Position in Sequence')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/positional_symbol_frequencies.png', dpi=150)
plt.close()

# Try to find simple rules
print("\n" + "="*60)
print("Testing simple positional rules:")
print("="*60)

# Check if specific symbols at specific positions are predictive
best_rules = []

for pos in range(n_positions):
    for symbol in symbols:
        # Calculate accuracy of rule: if symbol at position == X, predict variable
        correct = 0
        total = 0
        
        for idx, row in train_df.iterrows():
            seq = row['symbol_series']
            label = row['label']
            
            if pos < len(seq):
                prediction = 1 if seq[pos] == symbol else 0
                if prediction == label:
                    correct += 1
                total += 1
        
        if total > 0:
            accuracy = correct / total
            if accuracy > 0.6:  # Better than random
                best_rules.append((pos, symbol, accuracy, correct, total))

# Sort by accuracy
best_rules.sort(key=lambda x: x[2], reverse=True)

print(f"\nTop simple positional rules (train set):")
print("Position\tSymbol\tAccuracy\tCorrect/Total")
for pos, symbol, accuracy, correct, total in best_rules[:10]:
    print(f"{pos}\t\t{symbol}\t{accuracy:.3f}\t\t{correct}/{total}")

# Test the best rule on validation set
if best_rules:
    best_pos, best_symbol, best_acc, _, _ = best_rules[0]
    
    val_df = pd.read_csv(os.path.join(data_dir, 'val.csv'))
    
    correct_val = 0
    total_val = 0
    
    for idx, row in val_df.iterrows():
        seq = row['symbol_series']
        label = row['label']
        
        if best_pos < len(seq):
            prediction = 1 if seq[best_pos] == best_symbol else 0
            if prediction == label:
                correct_val += 1
            total_val += 1
    
    if total_val > 0:
        val_accuracy = correct_val / total_val
        print(f"\nBest rule on validation set: position {best_pos} == '{best_symbol}'")
        print(f"Validation accuracy: {val_accuracy:.3f} ({correct_val}/{total_val})")

print("\nVisualization complete. Figures saved to report/images/")