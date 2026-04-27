import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's think about the physics of variable stars.
# They have periodic light curves.
# If the string is a phase-folded light curve, then the string is circular.
# s[0] is adjacent to s[-1].
# Let's try to extract features from the circular string.

def get_circular_transitions(s):
    chars = ['u', 'v', 'w', 'x', 'y', 'z', '.', '*']
    mat = np.zeros((8, 8))
    for i in range(len(s)):
        c1 = s[i]
        c2 = s[(i+1) % len(s)]
        if c1 in chars and c2 in chars:
            idx1 = chars.index(c1)
            idx2 = chars.index(c2)
            mat[idx1, idx2] += 1
    return mat.flatten()

X_train = np.array([get_circular_transitions(s) for s in train['symbol_series']])
X_val = np.array([get_circular_transitions(s) for s in val['symbol_series']])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Circular Transitions RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
