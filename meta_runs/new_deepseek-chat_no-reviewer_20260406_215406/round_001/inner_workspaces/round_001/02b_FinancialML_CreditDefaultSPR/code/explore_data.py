import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
train = pd.read_csv('../data/train.csv')
val = pd.read_csv('../data/val.csv')
test = pd.read_csv('../data/test.csv')

print("Dataset shapes:")
print(f"Train: {train.shape}")
print(f"Validation: {val.shape}")
print(f"Test: {test.shape}")

print("\nDefault flag distribution:")
print("Train:")
print(train['default_flag'].value_counts())
print(f"Default rate: {train['default_flag'].mean():.3f}")
print("\nValidation:")
print(val['default_flag'].value_counts())
print(f"Default rate: {val['default_flag'].mean():.3f}")
print("\nTest:")
print(test['default_flag'].value_counts())
print(f"Default rate: {test['default_flag'].mean():.3f}")

# Analyze sequence characteristics
def analyze_sequences(df, name):
    print(f"\n=== {name} Sequence Analysis ===")
    lengths = df['sym_seq'].apply(len)
    print(f"Length - Min: {lengths.min()}, Max: {lengths.max()}, Mean: {lengths.mean():.1f}, Std: {lengths.std():.1f}")
    
    # Count character frequencies
    all_chars = ''.join(df['sym_seq'])
    char_counts = Counter(all_chars)
    total_chars = len(all_chars)
    print("\nCharacter frequencies:")
    for char in sorted(char_counts.keys()):
        freq = char_counts[char] / total_chars
        print(f"  {char}: {char_counts[char]} ({freq:.3f})")
    
    return char_counts

char_counts_train = analyze_sequences(train, "Train")
char_counts_val = analyze_sequences(val, "Validation")
char_counts_test = analyze_sequences(test, "Test")

# Create visualization directory
os.makedirs('report/images', exist_ok=True)

# Plot 1: Default distribution
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for idx, (df, name) in enumerate([(train, 'Train'), (val, 'Validation'), (test, 'Test')]):
    ax = axes[idx]
    counts = df['default_flag'].value_counts()
    ax.bar(['Non-default (0)', 'Default (1)'], counts.values, color=['skyblue', 'salmon'])
    ax.set_title(f'{name} Set (n={len(df)})')
    ax.set_ylabel('Count')
    for i, v in enumerate(counts.values):
        ax.text(i, v + 2, str(v), ha='center')

plt.tight_layout()
plt.savefig('report/images/default_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: Character frequency comparison
fig, ax = plt.subplots(figsize=(10, 6))
chars = sorted(char_counts_train.keys())

# Calculate frequencies
freq_train = [char_counts_train[char] / sum(char_counts_train.values()) for char in chars]
freq_val = [char_counts_val[char] / sum(char_counts_val.values()) for char in chars]
freq_test = [char_counts_test[char] / sum(char_counts_test.values()) for char in chars]

x = np.arange(len(chars))
width = 0.25

ax.bar(x - width, freq_train, width, label='Train', alpha=0.8)
ax.bar(x, freq_val, width, label='Validation', alpha=0.8)
ax.bar(x + width, freq_test, width, label='Test', alpha=0.8)

ax.set_xlabel('Character')
ax.set_ylabel('Frequency')
ax.set_title('Character Frequency Distribution Across Datasets')
ax.set_xticks(x)
ax.set_xticklabels(chars)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/character_frequencies.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nExploratory analysis complete. Plots saved to report/images/")
