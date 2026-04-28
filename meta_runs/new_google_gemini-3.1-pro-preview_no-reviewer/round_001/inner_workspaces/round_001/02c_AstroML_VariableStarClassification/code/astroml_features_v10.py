import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# The baseline is 0.78. This is a huge gap.
# Let's look at the protocol again. "Classify variable vs non-variable sources using symbol_series features."
# In astronomy, variable stars have a changing magnitude over time.
# Non-variable stars have a constant magnitude (with some noise).
# If the characters represent magnitudes, then variable stars should have a higher variance.
# Let's try to map the characters to numbers again, but maybe the order is different.
# Let's try all possible permutations of the characters? No, that's 8! = 40320.
# Let's just use the variance of the character counts.

def get_var_features(df):
    features = []
    for s in df['symbol_series']:
        counts = [s.count(c) for c in ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']]
        features.append([
            np.var(counts),
            np.max(counts) - np.min(counts),
            np.sum([c > 0 for c in counts])
        ])
    return np.array(features)

X_train = get_var_features(train)
X_val = get_var_features(val)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'Var RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

# What if the characters are just a sequence of differences?
# Let's try to find the number of times the character changes.
def get_changes(df):
    features = []
    for s in df['symbol_series']:
        changes = sum([1 for i in range(1, len(s)) if s[i] != s[i-1]])
        features.append([changes])
    return np.array(features)

X_train_changes = get_changes(train)
X_val_changes = get_changes(val)

clf_changes = RandomForestClassifier(n_estimators=100, random_state=42)
clf_changes.fit(X_train_changes, train['label'])
y_pred_changes = clf_changes.predict(X_val_changes)
print(f'Changes RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_changes):.4f}')
