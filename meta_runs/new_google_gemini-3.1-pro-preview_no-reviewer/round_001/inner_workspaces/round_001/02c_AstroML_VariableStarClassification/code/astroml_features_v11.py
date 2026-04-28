import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's look at the characters again. *, ., u, v, w, x, y, z
# Maybe * and . are special characters (e.g. missing data, outliers, or specific states).
# Let's try to remove them and see if the remaining sequence has a pattern.

def get_clean_features(df):
    features = []
    for s in df['symbol_series']:
        clean_s = s.replace('*', '').replace('.', '')
        if len(clean_s) == 0:
            features.append([0, 0, 0, 0, 0, 0])
            continue
            
        counts = [clean_s.count(c) for c in ['u', 'v', 'w', 'x', 'y', 'z']]
        features.append([
            len(clean_s),
            np.var(counts),
            np.max(counts) - np.min(counts),
            clean_s.count('u'),
            clean_s.count('z'),
            sum([1 for i in range(1, len(clean_s)) if clean_s[i] != clean_s[i-1]])
        ])
    return np.array(features)

X_train = get_clean_features(train)
X_val = get_clean_features(val)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'Clean RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

# What if the characters represent a random walk?
# Let's map them to steps: u=-3, v=-2, w=-1, x=1, y=2, z=3, *=0, .=0
char_map = {'u': -3, 'v': -2, 'w': -1, 'x': 1, 'y': 2, 'z': 3, '*': 0, '.': 0}

def get_rw_features(df):
    features = []
    for s in df['symbol_series']:
        steps = [char_map[c] for c in s]
        walk = np.cumsum(steps)
        features.append([
            np.max(walk) - np.min(walk),
            np.var(walk),
            walk[-1],
            np.sum(np.abs(steps))
        ])
    return np.array(features)

X_train_rw = get_rw_features(train)
X_val_rw = get_rw_features(val)

clf_rw = RandomForestClassifier(n_estimators=100, random_state=42)
clf_rw.fit(X_train_rw, train['label'])
y_pred_rw = clf_rw.predict(X_val_rw)
print(f'RW RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_rw):.4f}')
