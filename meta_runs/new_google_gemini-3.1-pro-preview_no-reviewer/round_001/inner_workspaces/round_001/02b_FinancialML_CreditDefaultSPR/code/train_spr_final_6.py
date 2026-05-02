import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import os

os.makedirs('report/images', exist_ok=True)

train = pd.read_csv('outputs/train.csv')
val = pd.read_csv('outputs/val.csv')
test = pd.read_csv('outputs/test.csv')

def get_all_substrings(seq, min_len=1, max_len=20):
    substrings = []
    for i in range(len(seq)):
        for j in range(i + min_len, min(i + max_len + 1, len(seq) + 1)):
            substrings.append(seq[i:j])
    return substrings

all_train_substrings = []
for seq in train['sym_seq']:
    all_train_substrings.extend(get_all_substrings(seq, 1, 20))

from collections import Counter
counts = Counter(all_train_substrings)

# Let's try to use the motifs approach again, but with Logistic Regression and more careful selection
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
    if p + n >= 2:
        ratio = (p + 1) / (n + 1)
        motifs.append((sub, p, n, ratio))

best_auc = 0
best_k = 0
best_model = None
best_features = None

for k in [10, 20, 30, 40, 50]:
    motifs.sort(key=lambda x: x[3], reverse=True)
    top_pos = [m[0] for m in motifs[:k]]
    
    motifs.sort(key=lambda x: x[3])
    top_neg = [m[0] for m in motifs[:k]]
    
    selected_motifs = list(set(top_pos + top_neg))
    
    def extract_features(seq):
        features = {}
        for sub in selected_motifs:
            features[sub] = seq.count(sub)
        return features
    
    X_train = pd.DataFrame([extract_features(seq) for seq in train['sym_seq']])
    X_val = pd.DataFrame([extract_features(seq) for seq in val['sym_seq']])
    
    y_train = train['default_flag']
    y_val = val['default_flag']
    
    lr = LogisticRegression(max_iter=1000, C=1.0)
    lr.fit(X_train, y_train)
    val_preds_lr = lr.predict_proba(X_val)[:, 1]
    auc_lr = roc_auc_score(y_val, val_preds_lr)
    
    print(f'Top {k} motifs per class, Total: {len(selected_motifs)}, LR AUC: {auc_lr:.4f}')
    
    if auc_lr > best_auc:
        best_auc = auc_lr
        best_k = k
        best_model = lr
        best_features = selected_motifs

print(f'\nBest k: {best_k}, Best Val AUC: {best_auc:.4f}')

# Evaluate on test set
def extract_best_features(seq):
    features = {}
    for sub in best_features:
        features[sub] = seq.count(sub)
    return features

X_test = pd.DataFrame([extract_best_features(seq) for seq in test['sym_seq']])
y_test = test['default_flag']

test_preds = best_model.predict_proba(X_test)[:, 1]
test_auc = roc_auc_score(y_test, test_preds)
print(f'Test AUC: {test_auc:.4f}')
