import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

train = pd.read_csv('data/train.csv')

chars = ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']

for c in chars:
    train[f'count_{c}'] = train['symbol_series'].apply(lambda x: x.count(c))

print("Mean counts for Label 0 (Non-variable):")
print(train[train['label'] == 0][[f'count_{c}' for c in chars]].mean())

print("\nMean counts for Label 1 (Variable):")
print(train[train['label'] == 1][[f'count_{c}' for c in chars]].mean())

# Let's check the variance of the characters
char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6}

def get_variance(s):
    vals = [char_map[c] for c in s if c in char_map]
    if len(vals) > 0:
        return np.var(vals)
    return 0

train['variance'] = train['symbol_series'].apply(get_variance)
print("\nMean variance for Label 0:", train[train['label'] == 0]['variance'].mean())
print("Mean variance for Label 1:", train[train['label'] == 1]['variance'].mean())
