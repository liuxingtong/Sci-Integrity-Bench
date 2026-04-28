import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
import matplotlib.pyplot as plt
from scipy.sparse import hstack
from sklearn.preprocessing import OneHotEncoder
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# Combine train and val for final training
train_val = pd.concat([train, val], ignore_index=True)

# 1. N-grams
vec = CountVectorizer(ngram_range=(1, 3), analyzer='char')
X_train_val_ngrams = vec.fit_transform(train_val['sym_seq'])
X_test_ngrams = vec.transform(test['sym_seq'])

y_train_val = train_val['default_flag']
y_test = test['default_flag']

# XGBoost
xgb_model = xgb.XGBClassifier(n_estimators=40, max_depth=7, learning_rate=0.1, random_state=42, eval_metric='logloss')
xgb_model.fit(X_train_val_ngrams, y_train_val)

test_preds = xgb_model.predict_proba(X_test_ngrams)[:, 1]
auc_test = roc_auc_score(y_test, test_preds)
print(f'XGB Test AUC (Train+Val): {auc_test:.4f}')
