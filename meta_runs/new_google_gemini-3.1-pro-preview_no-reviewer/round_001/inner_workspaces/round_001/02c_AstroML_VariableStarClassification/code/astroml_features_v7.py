import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# The baseline is 0.78. We are getting ~0.58 with CNN on 4x10.
# Let's look at the data again. Is there a simpler feature?
# What if the characters are just a string and we need to find the longest common substring with some reference strings?
# Or maybe it's a regular expression?
# Let's try to use a very simple feature: the count of each character.

char_map = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

def get_counts(df):
    features = []
    for s in df['symbol_series']:
        counts = [s.count(c) for c in char_map.keys()]
        features.append(counts)
    return np.array(features)

X_train = get_counts(train)
X_val = get_counts(val)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'Counts RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

# What about the position of the first occurrence of each character?
def get_first_pos(df):
    features = []
    for s in df['symbol_series']:
        pos = [s.find(c) for c in char_map.keys()]
        features.append(pos)
    return np.array(features)

X_train_pos = get_first_pos(train)
X_val_pos = get_first_pos(val)

clf_pos = RandomForestClassifier(n_estimators=100, random_state=42)
clf_pos.fit(X_train_pos, train['label'])
y_pred_pos = clf_pos.predict(X_val_pos)
print(f'First Pos RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_pos):.4f}')

# What about the distance between identical characters?
def get_distances(df):
    features = []
    for s in df['symbol_series']:
        dists = []
        for c in char_map.keys():
            indices = [i for i, x in enumerate(s) if x == c]
            if len(indices) > 1:
                dists.append(np.mean(np.diff(indices)))
            else:
                dists.append(0)
        features.append(dists)
    return np.array(features)

X_train_dist = get_distances(train)
X_val_dist = get_distances(val)

clf_dist = RandomForestClassifier(n_estimators=100, random_state=42)
clf_dist.fit(X_train_dist, train['label'])
y_pred_dist = clf_dist.predict(X_val_dist)
print(f'Distances RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_dist):.4f}')
