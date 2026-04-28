import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's rethink the mapping. What if the characters are just categorical and we should use one-hot encoding for each position?
# The length is always 40.

def get_one_hot_features(df):
    features = []
    for s in df['symbol_series']:
        row = []
        for c in s:
            one_hot = [0] * 8
            char_idx = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}[c]
            one_hot[char_idx] = 1
            row.extend(one_hot)
        features.append(row)
    return np.array(features)

X_train = get_one_hot_features(train)
X_val = get_one_hot_features(val)

clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'One-Hot RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

clf_xgb = xgb.XGBClassifier(random_state=42, max_depth=3, n_estimators=100)
clf_xgb.fit(X_train, train['label'])
y_pred_xgb = clf_xgb.predict(X_val)
print(f'One-Hot XGB Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_xgb):.4f}')

from sklearn.linear_model import LogisticRegression
clf_lr = LogisticRegression(max_iter=1000, random_state=42)
clf_lr.fit(X_train, train['label'])
y_pred_lr = clf_lr.predict(X_val)
print(f'One-Hot LR Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_lr):.4f}')
