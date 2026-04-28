import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

train = pd.read_csv('data/train.csv')

char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6, '*': np.nan, '.': np.nan}

fig, axes = plt.subplots(4, 2, figsize=(12, 10))
axes = axes.flatten()

for i in range(8):
    row = train.iloc[i]
    series = [char_map[c] for c in row['symbol_series']]
    axes[i].plot(series, marker='o')
    axes[i].set_title(f"Label: {row['label']}")

plt.tight_layout()
plt.savefig('outputs/series_plot.png')
