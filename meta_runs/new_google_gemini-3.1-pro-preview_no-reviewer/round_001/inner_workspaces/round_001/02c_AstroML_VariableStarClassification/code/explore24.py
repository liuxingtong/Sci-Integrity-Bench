import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# What if the symbols are NOT magnitudes?
# What if they are spectral types? O, B, A, F, G, K, M
# u, v, w, x, y, z -> 6 types. . and * are unknown.
# Variable stars might have specific spectral types or change spectral types.

# Let's try to count the number of transitions between different characters
def get_transition_counts(s):
    transitions = 0
    for i in range(len(s) - 1):
        if s[i] != s[i+1]:
            transitions += 1
    return transitions

train['transitions'] = train['symbol_series'].apply(get_transition_counts)
val['transitions'] = val['symbol_series'].apply(get_transition_counts)

print("Mean transitions for Label 0:", train[train['label'] == 0]['transitions'].mean())
print("Mean transitions for Label 1:", train[train['label'] == 1]['transitions'].mean())

# Let's try to count the number of unique characters in sliding windows
def get_window_unique(s, w):
    uniques = []
    for i in range(len(s) - w + 1):
        uniques.append(len(set(s[i:i+w])))
    return np.mean(uniques), np.std(uniques), np.max(uniques)

for w in [3, 5, 10]:
    train[f'win_{w}_mean'], train[f'win_{w}_std'], train[f'win_{w}_max'] = zip(*train['symbol_series'].apply(lambda x: get_window_unique(x, w)))
    val[f'win_{w}_mean'], val[f'win_{w}_std'], val[f'win_{w}_max'] = zip(*val['symbol_series'].apply(lambda x: get_window_unique(x, w)))

features = ['transitions'] + [f'win_{w}_{stat}' for w in [3, 5, 10] for stat in ['mean', 'std', 'max']]
X_train = train[features]
X_val = val[features]

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Window Unique RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
