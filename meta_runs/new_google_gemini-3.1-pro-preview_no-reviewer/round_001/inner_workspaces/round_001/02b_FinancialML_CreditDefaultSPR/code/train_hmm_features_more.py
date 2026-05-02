import pandas as pd
import numpy as np
from hmmlearn import hmm
from sklearn.metrics import roc_auc_score
import xgboost as xgb
from sklearn.linear_model import LogisticRegression

train = pd.read_csv('outputs/train.csv')
val = pd.read_csv('outputs/val.csv')
test = pd.read_csv('outputs/test.csv')

chars = ['1', '2', 'A', 'B', 'C', 'D']
char_to_idx = {c: i for i, c in enumerate(chars)}

def seq_to_idx(seq):
    return np.array([[char_to_idx[c]] for c in seq])

train_0 = train[train['default_flag'] == 0]
train_1 = train[train['default_flag'] == 1]

X_train_0 = np.concatenate([seq_to_idx(seq) for seq in train_0['sym_seq']])
lengths_0 = [len(seq) for seq in train_0['sym_seq']]

X_train_1 = np.concatenate([seq_to_idx(seq) for seq in train_1['sym_seq']])
lengths_1 = [len(seq) for seq in train_1['sym_seq']]

models_0 = []
models_1 = []

for n_components in range(2, 10):
    model_0 = hmm.CategoricalHMM(n_components=n_components, random_state=42, n_iter=100)
    model_0.fit(X_train_0, lengths_0)
    models_0.append(model_0)
    
    model_1 = hmm.CategoricalHMM(n_components=n_components, random_state=42, n_iter=100)
    model_1.fit(X_train_1, lengths_1)
    models_1.append(model_1)

def extract_hmm_features(seq):
    x = seq_to_idx(seq)
    features = {}
    for i, (m0, m1) in enumerate(zip(models_0, models_1)):
        features[f'hmm_0_{i}'] = m0.score(x)
        features[f'hmm_1_{i}'] = m1.score(x)
        features[f'hmm_diff_{i}'] = m1.score(x) - m0.score(x)
    return features

X_train = pd.DataFrame([extract_hmm_features(seq) for seq in train['sym_seq']])
X_val = pd.DataFrame([extract_hmm_features(seq) for seq in val['sym_seq']])

y_train = train['default_flag']
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
