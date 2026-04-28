import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.preprocessing import StandardScaler

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

chars = sorted(list(set(''.join(train['symbol_series']))))
char_to_idx = {c: i for i, c in enumerate(chars)}

def get_transition_matrix(s):
    mat = np.zeros((len(chars), len(chars)))
    for i in range(len(s) - 1):
        c1 = s[i]
        c2 = s[i+1]
        mat[char_to_idx[c1], char_to_idx[c2]] += 1
    # Normalize
    row_sums = mat.sum(axis=1)
    # Avoid division by zero
    row_sums[row_sums == 0] = 1
    mat = mat / row_sums[:, np.newaxis]
    return mat.flatten()

def extract_features(df):
    features = []
    for s in df['symbol_series']:
        features.append(get_transition_matrix(s))
    return np.array(features)

X_train = extract_features(train)
y_train = train['label']

X_val = extract_features(val)
y_val = val['label']

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_val)
print(f'RF Val Balanced Acc: {balanced_accuracy_score(y_val, y_pred):.4f}')

clf_lr = LogisticRegression(max_iter=1000, random_state=42)
clf_lr.fit(X_train_scaled, y_train)
y_pred_lr = clf_lr.predict(X_val_scaled)
print(f'LR Val Balanced Acc: {balanced_accuracy_score(y_val, y_pred_lr):.4f}')
