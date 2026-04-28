import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import xgboost as xgb
from collections import Counter

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

chars = ['A', 'B', 'C', 'D', '1', '2']

def extract_features(df):
    features = []
    for seq in df['sym_seq']:
        row = []
        # 1. Character counts
        counts = Counter(seq)
        for c in chars:
            row.append(counts.get(c, 0))
            
        # 2. Transition counts (bigrams)
        bigrams = [seq[i:i+2] for i in range(len(seq)-1)]
        bigram_counts = Counter(bigrams)
        for c1 in chars:
            for c2 in chars:
                row.append(bigram_counts.get(c1+c2, 0))
                
        # 3. Position of first occurrence
        for c in chars:
            row.append(seq.find(c))
            
        # 4. Position of last occurrence
        for c in chars:
            row.append(seq.rfind(c))
            
        features.append(row)
    return np.array(features)

X_train = extract_features(train)
y_train = train['default_flag']

X_val = extract_features(val)
y_val = val['default_flag']

# XGBoost
xgb_model = xgb.XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42, eval_metric='logloss')
xgb_model.fit(X_train, y_train)
val_preds_xgb = xgb_model.predict_proba(X_val)[:, 1]
auc_xgb = roc_auc_score(y_val, val_preds_xgb)
print(f'XGB AUC: {auc_xgb:.4f}')

# Random Forest
rf = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
rf.fit(X_train, y_train)
val_preds_rf = rf.predict_proba(X_val)[:, 1]
auc_rf = roc_auc_score(y_val, val_preds_rf)
print(f'RF AUC: {auc_rf:.4f}')
