import pandas as pd
import numpy as np
from collections import Counter
import math
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import xgboost as xgb

def extract_features(df):
    features = []
    chars = ['1', '2', 'A', 'B', 'C', 'D']
    
    for seq in df['sym_seq']:
        row_features = {}
        
        # 1. Character counts
        counts = Counter(seq)
        for c in chars:
            row_features[f'count_{c}'] = counts[c]
            
        # 2. Transitions (bigrams)
        for i in range(len(seq) - 1):
            bigram = seq[i:i+2]
            row_features[f'bigram_{bigram}'] = row_features.get(f'bigram_{bigram}', 0) + 1
            
        # 3. First/Last positions
        for c in chars:
            row_features[f'first_{c}'] = seq.find(c) if c in seq else -1
            row_features[f'last_{c}'] = seq.rfind(c) if c in seq else -1
            
        # 4. Longest run
        for c in chars:
            max_run = 0
            current_run = 0
            for char in seq:
                if char == c:
                    current_run += 1
                    max_run = max(max_run, current_run)
                else:
                    current_run = 0
            row_features[f'longest_run_{c}'] = max_run
            
        # 5. Entropy
        entropy = 0
        for count in counts.values():
            p = count / len(seq)
            entropy -= p * math.log2(p)
        row_features['entropy'] = entropy
        
        features.append(row_features)
        
    return pd.DataFrame(features).fillna(0)

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

X_train = extract_features(train)
y_train = train['default_flag']

X_val = extract_features(val)
# Ensure val has same columns as train
for col in X_train.columns:
    if col not in X_val.columns:
        X_val[col] = 0
X_val = X_val[X_train.columns]

y_val = val['default_flag']

print('Train shape:', X_train.shape)

model = xgb.XGBClassifier(eval_metric='logloss', random_state=42)
model.fit(X_train, y_train)
y_val_pred = model.predict_proba(X_val)[:, 1]
auc = roc_auc_score(y_val, y_val_pred)
print(f'XGBoost Val AUC: {auc:.4f}')

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
y_val_pred_rf = rf.predict_proba(X_val)[:, 1]
auc_rf = roc_auc_score(y_val, y_val_pred_rf)
print(f'Random Forest Val AUC: {auc_rf:.4f}')
