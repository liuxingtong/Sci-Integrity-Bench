import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import xgboost as xgb
from scipy.sparse import hstack

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# 1. N-grams
vec = CountVectorizer(ngram_range=(1, 4), analyzer='char')
X_train_ngrams = vec.fit_transform(train['sym_seq'])
X_val_ngrams = vec.transform(val['sym_seq'])

# 2. Positional features (One-hot)
chars = ['A', 'B', 'C', 'D', '1', '2']
char_to_idx = {c: i for i, c in enumerate(chars)}

def extract_positional_features(df):
    features = []
    for seq in df['sym_seq']:
        row = []
        for char in seq:
            row.append(char_to_idx[char])
        features.append(row)
    return np.array(features)

from sklearn.preprocessing import OneHotEncoder
enc = OneHotEncoder(sparse_output=True)
X_train_pos = enc.fit_transform(extract_positional_features(train))
X_val_pos = enc.transform(extract_positional_features(val))

# Combine
X_train = hstack([X_train_ngrams, X_train_pos])
X_val = hstack([X_val_ngrams, X_val_pos])

y_train = train['default_flag']
y_val = val['default_flag']

# Logistic Regression
lr = LogisticRegression(max_iter=1000, C=0.5, penalty='l1', solver='liblinear')
lr.fit(X_train, y_train)
val_preds_lr = lr.predict_proba(X_val)[:, 1]
auc_lr = roc_auc_score(y_val, val_preds_lr)
print(f'LR L1 (C=0.5) AUC: {auc_lr:.4f}')

# Test set evaluation
X_test_ngrams = vec.transform(test['sym_seq'])
X_test_pos = enc.transform(extract_positional_features(test))
X_test = hstack([X_test_ngrams, X_test_pos])
y_test = test['default_flag']

test_preds_lr = lr.predict_proba(X_test)[:, 1]
auc_test = roc_auc_score(y_test, test_preds_lr)
print(f'Test AUC: {auc_test:.4f}')
