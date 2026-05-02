import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

def seq_to_features(df):
    return pd.DataFrame([list(seq) for seq in df['sym_seq']])

X_train_cat = seq_to_features(train)
X_val_cat = seq_to_features(val)
X_test_cat = seq_to_features(test)

encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train = encoder.fit_transform(X_train_cat)
X_val = encoder.transform(X_val_cat)

y_train = train['default_flag']
y_val = val['default_flag']

# Logistic Regression
lr = LogisticRegression(max_iter=1000, C=1.0)
lr.fit(X_train, y_train)
val_preds_lr = lr.predict_proba(X_val)[:, 1]
auc_lr = roc_auc_score(y_val, val_preds_lr)
print(f'LR AUC: {auc_lr:.4f}')

# Random Forest
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
val_preds_rf = rf.predict_proba(X_val)[:, 1]
auc_rf = roc_auc_score(y_val, val_preds_rf)
print(f'RF AUC: {auc_rf:.4f}')

# XGBoost
xgb_model = xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss')
xgb_model.fit(X_train, y_train)
val_preds_xgb = xgb_model.predict_proba(X_val)[:, 1]
auc_xgb = roc_auc_score(y_val, val_preds_xgb)
print(f'XGB AUC: {auc_xgb:.4f}')
