import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's think about the problem again. Variable vs non-variable stars.
# The characters are *, ., u, v, w, x, y, z.
# What if the characters represent the *change* in magnitude, not the magnitude itself?
# e.g. u = large decrease, v = medium decrease, w = small decrease, x = small increase, y = medium increase, z = large increase.
# * and . could be missing data or no change.
# If this is the case, then variable stars should have more u, v, y, z.
# Non-variable stars should have more w, x, *, .

def get_change_features(df):
    features = []
    for s in df['symbol_series']:
        counts = [s.count(c) for c in ['u', 'v', 'y', 'z']]
        counts_small = [s.count(c) for c in ['w', 'x', '*', '.']]
        features.append([
            np.sum(counts),
            np.sum(counts_small),
            np.sum(counts) / (np.sum(counts_small) + 1)
        ])
    return np.array(features)

X_train = get_change_features(train)
X_val = get_change_features(val)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'Change RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

# Let's check the mean of these features for each class.
train['large_change'] = train['symbol_series'].apply(lambda s: sum([s.count(c) for c in ['u', 'v', 'y', 'z']]))
train['small_change'] = train['symbol_series'].apply(lambda s: sum([s.count(c) for c in ['w', 'x', '*', '.']]))

print(train.groupby('label')[['large_change', 'small_change']].mean())
