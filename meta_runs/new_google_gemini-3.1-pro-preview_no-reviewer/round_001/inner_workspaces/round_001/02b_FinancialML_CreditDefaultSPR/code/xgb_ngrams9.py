import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import roc_auc_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

vec = CountVectorizer(ngram_range=(1, 3), analyzer='char')
X_train = vec.fit_transform(train['sym_seq'])
X_val = vec.transform(val['sym_seq'])
X_test = vec.transform(test['sym_seq'])

y_train = train['default_flag']
y_val = val['default_flag']
y_test = test['default_flag']

xgb_model = xgb.XGBClassifier(n_estimators=40, max_depth=7, learning_rate=0.1, random_state=42, eval_metric='logloss')
xgb_model.fit(X_train, y_train)
val_preds = xgb_model.predict_proba(X_val)[:, 1]
auc_val = roc_auc_score(y_val, val_preds)
print(f'XGB Val AUC: {auc_val:.4f}')

test_preds = xgb_model.predict_proba(X_test)[:, 1]
auc_test = roc_auc_score(y_test, test_preds)
print(f'XGB Test AUC: {auc_test:.4f}')
