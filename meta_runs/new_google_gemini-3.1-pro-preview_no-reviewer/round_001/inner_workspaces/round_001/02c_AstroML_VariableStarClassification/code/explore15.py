import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's look at the distance between identical characters
def get_distances(s):
    features = []
    for c in ['u', 'v', 'w', 'x', 'y', 'z', '.', '*']:
        indices = [i for i, char in enumerate(s) if char == c]
        if len(indices) > 1:
            diffs = np.diff(indices)
            features.extend([np.mean(diffs), np.std(diffs), np.max(diffs), np.min(diffs)])
        elif len(indices) == 1:
            features.extend([40, 0, 40, 40])
        else:
            features.extend([40, 0, 40, 40])
    return features

X_train = np.array([get_distances(s) for s in train['symbol_series']])
X_val = np.array([get_distances(s) for s in val['symbol_series']])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Distances RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
