import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import os

# Load data
train = pd.read_csv('../data/train.csv')

# Separate default and non-default sequences
default_seqs = train[train['default_flag'] == 1]['sym_seq']
non_default_seqs = train[train['default_flag'] == 0]['sym_seq']

print(f"Default sequences: {len(default_seqs)}")
print(f"Non-default sequences: {len(non_default_seqs)}")

# Analyze character frequencies by class
def get_char_frequencies(seqs):
    all_chars = ''.join(seqs)
    char_counts = Counter(all_chars)
    total = sum(char_counts.values())
    return {char: count/total for char, count in char_counts.items()}

freq_default = get_char_frequencies(default_seqs)
freq_non_default = get_char_frequencies(non_default_seqs)

print("\nCharacter frequencies by class:")
print("Char | Default | Non-default | Difference")
print("-" * 45)
for char in sorted(freq_default.keys()):
    diff = freq_default[char] - freq_non_default[char]
    print(f"{char:4} | {freq_default[char]:.4f}   | {freq_non_default[char]:.4f}      | {diff:+.4f}")

# Analyze bigram frequencies
def get_bigram_frequencies(seqs):
    bigrams = []
    for seq in seqs:
        bigrams.extend([seq[i:i+2] for i in range(len(seq)-1)])
    bigram_counts = Counter(bigrams)
    total = sum(bigram_counts.values())
    return {bigram: count/total for bigram, count in bigram_counts.items()}

bigram_default = get_bigram_frequencies(default_seqs)
bigram_non_default = get_bigram_frequencies(non_default_seqs)

# Find bigrams with largest difference
bigram_diffs = {}
all_bigrams = set(list(bigram_default.keys()) + list(bigram_non_default.keys()))
for bigram in all_bigrams:
    freq_d = bigram_default.get(bigram, 0)
    freq_nd = bigram_non_default.get(bigram, 0)
    bigram_diffs[bigram] = freq_d - freq_nd

# Sort by absolute difference
sorted_bigrams = sorted(bigram_diffs.items(), key=lambda x: abs(x[1]), reverse=True)

print("\nTop 20 bigrams with largest frequency differences:")
print("Bigram | Default Freq | Non-default Freq | Difference")
print("-" * 60)
for bigram, diff in sorted_bigrams[:20]:
    freq_d = bigram_default.get(bigram, 0)
    freq_nd = bigram_non_default.get(bigram, 0)
    print(f"{bigram:6} | {freq_d:.5f}       | {freq_nd:.5f}          | {diff:+.5f}")

# Analyze position-specific patterns
position_analysis = []
for pos in range(20):  # All sequences are length 20
    chars_at_pos_default = [seq[pos] for seq in default_seqs]
    chars_at_pos_non_default = [seq[pos] for seq in non_default_seqs]
    
    for char in ['1', '2', 'A', 'B', 'C', 'D']:
        freq_d = chars_at_pos_default.count(char) / len(chars_at_pos_default)
        freq_nd = chars_at_pos_non_default.count(char) / len(chars_at_pos_non_default)
        diff = freq_d - freq_nd
        position_analysis.append({
            'position': pos,
            'char': char,
            'freq_default': freq_d,
            'freq_non_default': freq_nd,
            'difference': diff
        })

# Find positions with largest differences
position_df = pd.DataFrame(position_analysis)
position_df['abs_diff'] = position_df['difference'].abs()
sorted_positions = position_df.sort_values('abs_diff', ascending=False)

print("\nTop 20 position-character combinations with largest differences:")
print("Pos | Char | Default Freq | Non-default Freq | Difference")
print("-" * 65)
for _, row in sorted_positions.head(20).iterrows():
    print(f"{row['position']:3} | {row['char']:4} | {row['freq_default']:.4f}       | {row['freq_non_default']:.4f}          | {row['difference']:+.4f}")

# Create visualizations
os.makedirs('../report/images', exist_ok=True)

# Plot 1: Character frequency comparison
fig, ax = plt.subplots(figsize=(10, 6))
chars = sorted(freq_default.keys())
x = np.arange(len(chars))
width = 0.35

ax.bar(x - width/2, [freq_default[char] for char in chars], width, label='Default', color='salmon')
ax.bar(x + width/2, [freq_non_default[char] for char in chars], width, label='Non-default', color='skyblue')

ax.set_xlabel('Character')
ax.set_ylabel('Frequency')
ax.set_title('Character Frequency by Default Status')
ax.set_xticks(x)
ax.set_xticklabels(chars)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/char_freq_by_class.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: Position analysis heatmap
# Create a matrix of differences
diff_matrix = np.zeros((6, 20))  # 6 chars x 20 positions
chars_idx = {char: i for i, char in enumerate(sorted(chars))}

for _, row in position_df.iterrows():
    i = chars_idx[row['char']]
    j = row['position']
    diff_matrix[i, j] = row['difference']

fig, ax = plt.subplots(figsize=(12, 4))
im = ax.imshow(diff_matrix, cmap='RdBu', aspect='auto', vmin=-0.15, vmax=0.15)
ax.set_xlabel('Position in Sequence')
ax.set_ylabel('Character')
ax.set_yticks(range(6))
ax.set_yticklabels(sorted(chars))
ax.set_title('Frequency Difference (Default - Non-default) by Position and Character')
plt.colorbar(im, ax=ax, label='Frequency Difference')

plt.tight_layout()
plt.savefig('../report/images/position_char_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nPattern analysis complete. Visualizations saved to report/images/")
