import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's look at the problem again. "Variable star classification"
# Maybe the symbols are not magnitudes, but something else.
# What if the symbols represent the *change* in magnitude?
# u: large decrease, v: small decrease, w: no change, x: small increase, y: large increase, z: very large increase
# Or maybe they are just arbitrary symbols.

# Let's try to find the most frequent substrings of length 3, 4, 5 in the whole dataset
from collections import Counter

def get_all_substrings(series, k):
    substrings = []
    for s in series:
        for i in range(len(s) - k + 1):
            substrings.append(s[i:i+k])
    return substrings

for k in [3, 4, 5]:
    subs_0 = get_all_substrings(train[train['label'] == 0]['symbol_series'], k)
    subs_1 = get_all_substrings(train[train['label'] == 1]['symbol_series'], k)
    
    counts_0 = Counter(subs_0)
    counts_1 = Counter(subs_1)
    
    print(f"\nTop 10 substrings of length {k} for Label 0:")
    print(counts_0.most_common(10))
    
    print(f"\nTop 10 substrings of length {k} for Label 1:")
    print(counts_1.most_common(10))
