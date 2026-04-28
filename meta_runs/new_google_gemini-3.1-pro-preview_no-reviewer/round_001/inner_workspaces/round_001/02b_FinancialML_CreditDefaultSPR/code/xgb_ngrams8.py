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

for n_est in [30, 40, 50, 60, 70]:
    xgb_model = xgb.XGBClassifier(n_estimators=n_est, max_depth=7, learning_rate=0.1, random_state=42, eval_metric='logloss')
    xgb_model.fit(X_train, y_train)
    val_preds = xgb_model.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, val_preds)
    print(f'XGB (n_est={n_est}) AUC: {auc:.4f}')
