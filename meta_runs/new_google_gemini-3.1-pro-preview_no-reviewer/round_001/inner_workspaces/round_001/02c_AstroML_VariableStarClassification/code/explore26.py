import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# Let's try to combine all the features we have so far.
# 1. Char n-grams (TF-IDF)
# 2. Transition matrix
# 3. Distances
# 4. Basic stats (counts)

# 1. Char n-grams
vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 5), max_features=2000)
X_train_tfidf = vectorizer.fit_transform(train['symbol_series']).toarray()
X_val_tfidf = vectorizer.transform(val['symbol_series']).toarray()

# 2. Transition matrix
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

X_train_trans = np.array([get_transition_matrix(s) for s in train['symbol_series']])
X_val_trans = np.array([get_transition_matrix(s) for s in val['symbol_series']])

# 3. Distances
def get_distances(s):
    features = []
    for c in chars:
        indices = [i for i, char in enumerate(s) if char == c]
        if len(indices) > 1:
            diffs = np.diff(indices)
            features.extend([np.mean(diffs), np.std(diffs), np.max(diffs), np.min(diffs)])
        elif len(indices) == 1:
            features.extend([40, 0, 40, 40])
        else:
            features.extend([40, 0, 40, 40])
    return features

X_train_dist = np.array([get_distances(s) for s in train['symbol_series']])
X_val_dist = np.array([get_distances(s) for s in val['symbol_series']])

# 4. Basic stats
def get_counts(s):
    return [s.count(c) for c in chars]

X_train_counts = np.array([get_counts(s) for s in train['symbol_series']])
X_val_counts = np.array([get_counts(s) for s in val['symbol_series']])

# Combine
X_train = np.concatenate([X_train_tfidf, X_train_trans, X_train_dist, X_train_counts], axis=1)
X_val = np.concatenate([X_val_tfidf, X_val_trans, X_val_dist, X_val_counts], axis=1)

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Combined RF Val Acc:', balanced_accuracy_score(y_val, val_pred))

model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Combined LR Val Acc:', balanced_accuracy_score(y_val, val_pred))

import xgboost as xgb
model = xgb.XGBClassifier(n_estimators=500, random_state=42, max_depth=6, learning_rate=0.05)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Combined XGB Val Acc:', balanced_accuracy_score(y_val, val_pred))
