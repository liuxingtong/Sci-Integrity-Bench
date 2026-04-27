import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

train = pd.read_csv('data/train.csv')

char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6, '.': 0, '*': 7}

def to_numeric(s):
    return [char_map[c] for c in s]

fig, axes = plt.subplots(4, 2, figsize=(12, 10))
axes = axes.flatten()

# Plot 4 non-variable
for i in range(4):
    s = train[train['label'] == 0]['symbol_series'].iloc[i]
    axes[i].plot(to_numeric(s), marker='o')
    axes[i].set_title(f'Non-variable {i}')

# Plot 4 variable
for i in range(4):
    s = train[train['label'] == 1]['symbol_series'].iloc[i]
    axes[i+4].plot(to_numeric(s), marker='o', color='orange')
    axes[i+4].set_title(f'Variable {i}')

plt.tight_layout()
plt.savefig('outputs/series_plot.png')
