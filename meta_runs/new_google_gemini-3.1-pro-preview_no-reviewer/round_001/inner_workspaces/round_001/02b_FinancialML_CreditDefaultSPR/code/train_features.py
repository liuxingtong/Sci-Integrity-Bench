import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import xgboost as xgb
from collections import Counter
import math

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

chars = ['1', '2', 'A', 'B', 'C', 'D']

def extract_features(seq):
    features = {}
    
    # Counts
    counts = Counter(seq)
    for c in chars:
        features[f'count_{c}'] = counts.get(c, 0)
        
    # Bigram counts
    bigrams = [seq[i:i+2] for i in range(len(seq)-1)]
    bigram_counts = Counter(bigrams)
    for c1 in chars:
        for c2 in chars:
            features[f'count_{c1}{c2}'] = bigram_counts.get(c1+c2, 0)
            
    # First and last positions
    for c in chars:
        features[f'first_{c}'] = seq.find(c) if c in seq else -1
        features[f'last_{c}'] = seq.rfind(c) if c in seq else -1
        
    # Longest consecutive
    for c in chars:
        max_len = 0
        curr_len = 0
        for char in seq:
            if char == c:
                curr_len += 1
                max_len = max(max_len, curr_len)
            else:
                curr_len = 0
        features[f'longest_{c}'] = max_len
        
    # Entropy
    entropy = 0
    for c in chars:
        p = counts.get(c, 0) / len(seq)
        if p > 0:
            entropy -= p * math.log2(p)
    features['entropy'] = entropy
    
    return features

X_train = pd.DataFrame([extract_features(seq) for seq in train['sym_seq']])
X_val = pd.DataFrame([extract_features(seq) for seq in val['sym_seq']])

y_train = train['default_flag']
y_val = val['default_flag']

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
