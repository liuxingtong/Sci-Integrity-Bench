import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import roc_auc_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

X_train_text = train['sym_seq']
y_train = train['default_flag']

X_val_text = val['sym_seq']
y_val = val['default_flag']

X_test_text = test['sym_seq']
y_test = test['default_flag']

ngram_range = (3, 5)
print(f'\n--- TF-IDF N-gram range: {ngram_range} ---')
vectorizer = TfidfVectorizer(ngram_range=ngram_range, analyzer='char')
X_train = vectorizer.fit_transform(X_train_text)
X_val = vectorizer.transform(X_val_text)
X_test = vectorizer.transform(X_test_text)

model = xgb.XGBClassifier(eval_metric='logloss', random_state=42)
model.fit(X_train, y_train)

y_val_pred = model.predict_proba(X_val)[:, 1]
val_auc = roc_auc_score(y_val, y_val_pred)
print(f'XGBoost Val AUC: {val_auc:.4f}')

y_test_pred = model.predict_proba(X_test)[:, 1]
test_auc = roc_auc_score(y_test, y_test_pred)
print(f'XGBoost Test AUC: {test_auc:.4f}')
