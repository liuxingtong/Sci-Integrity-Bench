import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
import matplotlib.pyplot as plt
from scipy.sparse import hstack
from sklearn.preprocessing import OneHotEncoder

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# Combine train and val for final training
train_val = pd.concat([train, val], ignore_index=True)

# 1. N-grams
vec = CountVectorizer(ngram_range=(1, 3), analyzer='char')
X_train_val_ngrams = vec.fit_transform(train_val['sym_seq'])
X_test_ngrams = vec.transform(test['sym_seq'])

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

enc = OneHotEncoder(sparse_output=True)
X_train_val_pos = enc.fit_transform(extract_positional_features(train_val))
X_test_pos = enc.transform(extract_positional_features(test))

# Combine
X_train_val = hstack([X_train_val_ngrams, X_train_val_pos])
X_test = hstack([X_test_ngrams, X_test_pos])

y_train_val = train_val['default_flag']
y_test = test['default_flag']

# Logistic Regression
lr = LogisticRegression(max_iter=1000, C=0.5, penalty='l2', solver='liblinear')
lr.fit(X_train_val, y_train_val)

test_preds = lr.predict_proba(X_test)[:, 1]
auc_test = roc_auc_score(y_test, test_preds)
print(f'Test AUC (Train+Val): {auc_test:.4f}')
