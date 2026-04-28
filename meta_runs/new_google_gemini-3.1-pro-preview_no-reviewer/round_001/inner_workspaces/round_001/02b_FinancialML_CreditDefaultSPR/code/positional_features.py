import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

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

X_train = extract_positional_features(train)
y_train = train['default_flag']

X_val = extract_positional_features(val)
y_val = val['default_flag']

# One-hot encode
from sklearn.preprocessing import OneHotEncoder
enc = OneHotEncoder(sparse_output=False)
X_train_oh = enc.fit_transform(X_train)
X_val_oh = enc.transform(X_val)

# Logistic Regression
lr = LogisticRegression(max_iter=1000, C=1.0)
lr.fit(X_train_oh, y_train)
val_preds_lr = lr.predict_proba(X_val_oh)[:, 1]
auc_lr = roc_auc_score(y_val, val_preds_lr)
print(f'LR AUC: {auc_lr:.4f}')

# Random Forest
rf = RandomForestClassifier(n_estimators=200, random_state=42)
rf.fit(X_train_oh, y_train)
val_preds_rf = rf.predict_proba(X_val_oh)[:, 1]
auc_rf = roc_auc_score(y_val, val_preds_rf)
print(f'RF AUC: {auc_rf:.4f}')

# XGBoost
xgb_model = xgb.XGBClassifier(n_estimators=200, random_state=42, eval_metric='logloss')
xgb_model.fit(X_train_oh, y_train)
val_preds_xgb = xgb_model.predict_proba(X_val_oh)[:, 1]
auc_xgb = roc_auc_score(y_val, val_preds_xgb)
print(f'XGB AUC: {auc_xgb:.4f}')
