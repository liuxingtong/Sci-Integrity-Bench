import pandas as pd
import numpy as np

train = pd.read_csv('data/train.csv')

# Let's check the distribution of characters in the first half vs second half
def get_half_counts(s):
    half = len(s) // 2
    s1 = s[:half]
    s2 = s[half:]
    return s1.count('*'), s2.count('*'), s1.count('.'), s2.count('.')

train['star1'], train['star2'], train['dot1'], train['dot2'] = zip(*train['symbol_series'].apply(get_half_counts))

print("Label 0:")
print(train[train['label'] == 0][['star1', 'star2', 'dot1', 'dot2']].mean())

print("\nLabel 1:")
print(train[train['label'] == 1][['star1', 'star2', 'dot1', 'dot2']].mean())
