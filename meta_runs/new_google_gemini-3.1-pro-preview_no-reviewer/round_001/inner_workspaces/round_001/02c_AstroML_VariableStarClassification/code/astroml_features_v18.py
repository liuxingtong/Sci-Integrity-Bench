import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# The baseline is 0.78. This means there is a very simple and strong feature that we are missing.
# Let's look at the strings again.
# Is it possible that the strings are just a binary representation?
# e.g. * and . are 0, u-z are 1?

def get_binary_features(df):
    features = []
    for s in df['symbol_series']:
        bin_s = [0 if c in ['*', '.'] else 1 for c in s]
        features.append([
            np.mean(bin_s),
            np.var(bin_s),
            sum([1 for i in range(1, len(bin_s)) if bin_s[i] != bin_s[i-1]])
        ])
    return np.array(features)

X_train = get_binary_features(train)
X_val = get_binary_features(val)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'Binary RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

# What if the strings are just a sequence of 3 states?
# e.g. * and . are 0, u,v,w are 1, x,y,z are 2?
def get_ternary_features(df):
    features = []
    for s in df['symbol_series']:
        ter_s = [0 if c in ['*', '.'] else 1 if c in ['u', 'v', 'w'] else 2 for c in s]
        features.append([
            np.mean(ter_s),
            np.var(ter_s),
            sum([1 for i in range(1, len(ter_s)) if ter_s[i] != ter_s[i-1]])
        ])
    return np.array(features)

X_train_ter = get_ternary_features(train)
X_val_ter = get_ternary_features(val)

clf_ter = RandomForestClassifier(n_estimators=100, random_state=42)
clf_ter.fit(X_train_ter, train['label'])
y_pred_ter = clf_ter.predict(X_val_ter)
print(f'Ternary RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_ter):.4f}')
