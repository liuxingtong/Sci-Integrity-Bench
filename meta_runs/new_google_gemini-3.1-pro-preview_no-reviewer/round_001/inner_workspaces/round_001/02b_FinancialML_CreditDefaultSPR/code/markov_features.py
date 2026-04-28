import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

chars = ['A', 'B', 'C', 'D', '1', '2']
char_to_idx = {c: i for i, c in enumerate(chars)}

def get_transition_matrix(seq):
    mat = np.zeros((6, 6))
    for i in range(len(seq) - 1):
        c1 = char_to_idx[seq[i]]
        c2 = char_to_idx[seq[i+1]]
        mat[c1, c2] += 1
    # Normalize
    row_sums = mat.sum(axis=1)
    for i in range(6):
        if row_sums[i] > 0:
            mat[i, :] /= row_sums[i]
    return mat.flatten()

def extract_features(df):
    features = []
    for seq in df['sym_seq']:
        features.append(get_transition_matrix(seq))
    return np.array(features)

X_train = extract_features(train)
y_train = train['default_flag']

X_val = extract_features(val)
y_val = val['default_flag']

# Logistic Regression
lr = LogisticRegression(max_iter=1000, C=1.0)
lr.fit(X_train, y_train)
val_preds_lr = lr.predict_proba(X_val)[:, 1]
auc_lr = roc_auc_score(y_val, val_preds_lr)
print(f'LR AUC: {auc_lr:.4f}')

# XGBoost
xgb_model = xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss')
xgb_model.fit(X_train, y_train)
val_preds_xgb = xgb_model.predict_proba(X_val)[:, 1]
auc_xgb = roc_auc_score(y_val, val_preds_xgb)
print(f'XGB AUC: {auc_xgb:.4f}')
