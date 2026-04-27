import pandas as pd
import numpy as np
import re

train = pd.read_csv('data/train.csv')

# Let's look for specific patterns, like consecutive characters
def max_consecutive(s, char):
    matches = re.findall(f'[{char}]+', s)
    if not matches:
        return 0
    return max(len(m) for m in matches)

for c in ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']:
    train[f'max_cons_{c}'] = train['symbol_series'].apply(lambda x: max_consecutive(x, c))

print("Label 0 max consecutive:")
print(train[train['label'] == 0][[f'max_cons_{c}' for c in ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']]].mean())

print("\nLabel 1 max consecutive:")
print(train[train['label'] == 1][[f'max_cons_{c}' for c in ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']]].mean())
