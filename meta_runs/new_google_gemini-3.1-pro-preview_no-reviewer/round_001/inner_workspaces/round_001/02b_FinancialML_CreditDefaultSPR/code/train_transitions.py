import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

chars = ['1', '2', 'A', 'B', 'C', 'D']
char_to_idx = {c: i for i, c in enumerate(chars)}

def get_transition_matrix(seq):
    mat = np.zeros((6, 6))
    for i in range(len(seq) - 1):
        c1 = seq[i]
        c2 = seq[i+1]
        mat[char_to_idx[c1], char_to_idx[c2]] += 1
    return mat.flatten()

X_train = np.array([get_transition_matrix(seq) for seq in train['sym_seq']])
X_val = np.array([get_transition_matrix(seq) for seq in val['sym_seq']])

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
