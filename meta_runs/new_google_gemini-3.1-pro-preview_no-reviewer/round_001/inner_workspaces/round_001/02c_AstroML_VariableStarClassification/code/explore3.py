import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

train_df = pd.read_csv('data/train.csv')

chars = ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']

for label in [0, 1]:
    subset = train_df[train_df['label'] == label]
    all_chars = ''.join(subset['symbol_series'].tolist())
    counts = Counter(all_chars)
    total = sum(counts.values())
    print(f'Label {label} character distribution:')
    for c in chars:
        print(f'  {c}: {counts[c]/total:.4f}')
