import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

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
    # Normalize rows to get probabilities
    row_sums = mat.sum(axis=1)
    mat[row_sums > 0] = mat[row_sums > 0] / row_sums[row_sums > 0, np.newaxis]
    return mat.flatten()

X_train = np.array([get_transition_matrix(s) for s in train['symbol_series']])
X_val = np.array([get_transition_matrix(s) for s in val['symbol_series']])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Normalized Transition Matrix RF Val Acc:', balanced_accuracy_score(y_val, val_pred))

model = SVC(probability=True, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Normalized Transition Matrix SVC Val Acc:', balanced_accuracy_score(y_val, val_pred))

model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Normalized Transition Matrix LR Val Acc:', balanced_accuracy_score(y_val, val_pred))
