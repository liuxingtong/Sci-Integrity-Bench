import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

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

for min_count in [3, 5, 10]:
    valid_substrings = [sub for sub, count in counts.items() if count >= min_count]
    print(f'\n--- Min count: {min_count}, Features: {len(valid_substrings)} ---')
    
    def extract_substring_features(seq):
        features = {}
        for sub in valid_substrings:
            # Count occurrences instead of just presence
            features[sub] = seq.count(sub)
        return features
    
    X_train = pd.DataFrame([extract_substring_features(seq) for seq in train['sym_seq']])
    X_val = pd.DataFrame([extract_substring_features(seq) for seq in val['sym_seq']])
    
    y_train = train['default_flag']
    y_val = val['default_flag']
    
    # Logistic Regression
    lr = LogisticRegression(max_iter=1000, C=0.1)
    lr.fit(X_train, y_train)
    val_preds_lr = lr.predict_proba(X_val)[:, 1]
    auc_lr = roc_auc_score(y_val, val_preds_lr)
    print(f'LR AUC: {auc_lr:.4f}')
    
    # Random Forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    rf.fit(X_train, y_train)
    val_preds_rf = rf.predict_proba(X_val)[:, 1]
    auc_rf = roc_auc_score(y_val, val_preds_rf)
    print(f'RF AUC: {auc_rf:.4f}')
    
    # XGBoost
    xgb_model = xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss', max_depth=3, learning_rate=0.1)
    xgb_model.fit(X_train, y_train)
    val_preds_xgb = xgb_model.predict_proba(X_val)[:, 1]
    auc_xgb = roc_auc_score(y_val, val_preds_xgb)
    print(f'XGB AUC: {auc_xgb:.4f}')
