import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from collections import Counter

train = pd.read_csv('outputs/train.csv')
val = pd.read_csv('outputs/val.csv')
test = pd.read_csv('outputs/test.csv')

def get_all_substrings(seq, min_len=1, max_len=20):
    substrings = []
    for i in range(len(seq)):
        for j in range(i + min_len, min(i + max_len + 1, len(seq) + 1)):
            substrings.append(seq[i:j])
    return substrings

pos_seqs = train[train['default_flag'] == 1]['sym_seq']
neg_seqs = train[train['default_flag'] == 0]['sym_seq']

pos_substrings = []
for seq in pos_seqs:
    pos_substrings.extend(list(set(get_all_substrings(seq, 1, 20))))
    
neg_substrings = []
for seq in neg_seqs:
    neg_substrings.extend(list(set(get_all_substrings(seq, 1, 20))))

pos_counts = Counter(pos_substrings)
neg_counts = Counter(neg_substrings)

all_substrings = set(pos_counts.keys()).union(set(neg_counts.keys()))

motifs = []
for sub in all_substrings:
    p = pos_counts.get(sub, 0)
    n = neg_counts.get(sub, 0)
    if p + n >= 5:
        ratio = (p + 1) / (n + 1)
        motifs.append((sub, p, n, ratio))

for k in [10, 20, 50, 100, 200, 500]:
    motifs.sort(key=lambda x: x[3], reverse=True)
    top_pos = [m[0] for m in motifs[:k]]
    
    motifs.sort(key=lambda x: x[3])
    top_neg = [m[0] for m in motifs[:k]]
    
    selected_motifs = list(set(top_pos + top_neg))
    print(f'\n--- Top {k} motifs per class, Total: {len(selected_motifs)} ---')
    
    def extract_features(seq):
        features = {}
        for sub in selected_motifs:
            features[sub] = seq.count(sub)
        return features
    
    X_train = pd.DataFrame([extract_features(seq) for seq in train['sym_seq']])
    X_val = pd.DataFrame([extract_features(seq) for seq in val['sym_seq']])
    
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
