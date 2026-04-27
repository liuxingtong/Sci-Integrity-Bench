import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's combine transition matrix and distances
chars = ['u', 'v', 'w', 'x', 'y', 'z', '.', '*']

def get_transition_matrix(s):
    mat = np.zeros((8, 8))
    for i in range(len(s) - 1):
        c1 = s[i]
        c2 = s[i+1]
        if c1 in chars and c2 in chars:
            idx1 = chars.index(c1)
            idx2 = chars.index(c2)
            mat[idx1, idx2] += 1
    return mat.flatten()

def get_distances(s):
    features = []
    for c in chars:
        indices = [i for i, char in enumerate(s) if char == c]
        if len(indices) > 1:
            diffs = np.diff(indices)
            features.extend([np.mean(diffs), np.std(diffs), np.max(diffs), np.min(diffs)])
        elif len(indices) == 1:
            features.extend([40, 0, 40, 40])
        else:
            features.extend([40, 0, 40, 40])
    return features

def get_features(s):
    return np.concatenate([get_transition_matrix(s), get_distances(s)])

X_train = np.array([get_features(s) for s in train['symbol_series']])
X_val = np.array([get_features(s) for s in val['symbol_series']])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Combined RF Val Acc:', balanced_accuracy_score(y_val, val_pred))

model = xgb.XGBClassifier(n_estimators=500, random_state=42, max_depth=6, learning_rate=0.05)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Combined XGB Val Acc:', balanced_accuracy_score(y_val, val_pred))
