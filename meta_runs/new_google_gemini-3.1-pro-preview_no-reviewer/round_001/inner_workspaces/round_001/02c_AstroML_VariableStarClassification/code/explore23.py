import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's look at the problem again. "Variable star classification"
# The baseline is 0.78. This is very high.
# What if the symbols are just a simple encoding of a time series, and we need to look at the *differences* between adjacent symbols?

char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6, '.': np.nan, '*': np.nan}

def get_diff_features(s):
    num_s = [char_map[c] for c in s]
    num_s = pd.Series(num_s).interpolate(limit_direction='both').values
    
    if np.isnan(num_s).all():
        return [0] * 10
        
    diffs = np.diff(num_s)
    abs_diffs = np.abs(diffs)
    
    return [
        np.mean(diffs), np.std(diffs), np.max(diffs), np.min(diffs),
        np.mean(abs_diffs), np.std(abs_diffs), np.max(abs_diffs), np.min(abs_diffs),
        np.sum(diffs > 0), np.sum(diffs < 0)
    ]

X_train = np.array([get_diff_features(s) for s in train['symbol_series']])
X_val = np.array([get_diff_features(s) for s in val['symbol_series']])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Diff Features RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
