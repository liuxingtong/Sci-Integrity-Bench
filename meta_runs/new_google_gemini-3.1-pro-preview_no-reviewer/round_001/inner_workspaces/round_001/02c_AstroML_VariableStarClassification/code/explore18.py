import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# What if the symbols are NOT brightness levels, but something else?
# Let's try to use a pre-trained model or a more powerful sequence model.
# Since we can't easily use deep learning here, let's try to extract more complex string features.

# Let's try to find the longest repeating substring
def longest_repeating_substring(s):
    n = len(s)
    lrs = ""
    for i in range(n):
        for j in range(i+1, n):
            # Find length of longest common prefix of s[i:] and s[j:]
            k = 0
            while j + k < n and s[i+k] == s[j+k]:
                k += 1
            if k > len(lrs):
                lrs = s[i:i+k]
    return len(lrs)

train['lrs_len'] = train['symbol_series'].apply(longest_repeating_substring)
val['lrs_len'] = val['symbol_series'].apply(longest_repeating_substring)

print("Mean LRS len for Label 0:", train[train['label'] == 0]['lrs_len'].mean())
print("Mean LRS len for Label 1:", train[train['label'] == 1]['lrs_len'].mean())

# Let's try to find the number of unique substrings of length k
def num_unique_substrings(s, k):
    return len(set(s[i:i+k] for i in range(len(s) - k + 1)))

for k in range(2, 6):
    train[f'unique_{k}'] = train['symbol_series'].apply(lambda x: num_unique_substrings(x, k))
    val[f'unique_{k}'] = val['symbol_series'].apply(lambda x: num_unique_substrings(x, k))
    
    print(f"Mean unique {k} for Label 0:", train[train['label'] == 0][f'unique_{k}'].mean())
    print(f"Mean unique {k} for Label 1:", train[train['label'] == 1][f'unique_{k}'].mean())

features = ['lrs_len'] + [f'unique_{k}' for k in range(2, 6)]
X_train = train[features]
X_val = val[features]

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('String features RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
