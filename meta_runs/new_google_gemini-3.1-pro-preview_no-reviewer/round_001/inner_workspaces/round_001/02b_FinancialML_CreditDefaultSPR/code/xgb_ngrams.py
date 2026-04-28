import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import roc_auc_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

vec = CountVectorizer(ngram_range=(1, 5), analyzer='char')
X_train = vec.fit_transform(train['sym_seq'])
X_val = vec.transform(val['sym_seq'])

y_train = train['default_flag']
y_val = val['default_flag']

for max_depth in [3, 4, 5, 6]:
    for lr in [0.01, 0.05, 0.1]:
        xgb_model = xgb.XGBClassifier(n_estimators=300, max_depth=max_depth, learning_rate=lr, random_state=42, eval_metric='logloss')
        xgb_model.fit(X_train, y_train)
        val_preds = xgb_model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, val_preds)
        print(f'XGB (depth={max_depth}, lr={lr}) AUC: {auc:.4f}')
