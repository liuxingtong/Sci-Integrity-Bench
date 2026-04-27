import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's look at the transition matrix between characters
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

X_train = np.array([get_transition_matrix(s) for s in train['symbol_series']])
X_val = np.array([get_transition_matrix(s) for s in val['symbol_series']])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

val_pred = model.predict(X_val)
print('Transition Matrix Val Acc:', balanced_accuracy_score(y_val, val_pred))

# Let's try 3-gram transitions
def get_3gram_transitions(s):
    mat = np.zeros((8, 8, 8))
    for i in range(len(s) - 2):
        c1 = s[i]
        c2 = s[i+1]
        c3 = s[i+2]
        if c1 in chars and c2 in chars and c3 in chars:
            idx1 = chars.index(c1)
            idx2 = chars.index(c2)
            idx3 = chars.index(c3)
            mat[idx1, idx2, idx3] += 1
    return mat.flatten()

X_train_3 = np.array([get_3gram_transitions(s) for s in train['symbol_series']])
X_val_3 = np.array([get_3gram_transitions(s) for s in val['symbol_series']])

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train_3, y_train)

val_pred = model.predict(X_val_3)
print('3-gram Transition Matrix Val Acc:', balanced_accuracy_score(y_val, val_pred))
