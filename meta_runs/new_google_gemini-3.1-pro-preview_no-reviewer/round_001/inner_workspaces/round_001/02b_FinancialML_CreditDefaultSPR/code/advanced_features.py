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
vec = TfidfVectorizer(ngram_range=(1, 4), analyzer='char')
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
lr = LogisticRegression(max_iter=1000, C=0.1)
lr.fit(X_train, y_train)
val_preds_lr = lr.predict_proba(X_val)[:, 1]
auc_lr = roc_auc_score(y_val, val_preds_lr)
print(f'LR AUC: {auc_lr:.4f}')

# Random Forest
rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
rf.fit(X_train, y_train)
val_preds_rf = rf.predict_proba(X_val)[:, 1]
auc_rf = roc_auc_score(y_val, val_preds_rf)
print(f'RF AUC: {auc_rf:.4f}')

# XGBoost
xgb_model = xgb.XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42, eval_metric='logloss')
xgb_model.fit(X_train, y_train)
val_preds_xgb = xgb_model.predict_proba(X_val)[:, 1]
auc_xgb = roc_auc_score(y_val, val_preds_xgb)
print(f'XGB AUC: {auc_xgb:.4f}')
