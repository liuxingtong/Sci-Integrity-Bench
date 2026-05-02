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

# We found that min_count=9 with presence features gave XGB AUC 0.6001
# Let's try to optimize this further

best_auc = 0
best_min_count = 0
best_model = None
best_features = None

for min_count in [8, 9, 10, 11, 12]:
    valid_substrings = [sub for sub, count in counts.items() if count >= min_count]
    
    def extract_substring_features(seq):
        features = {}
        for sub in valid_substrings:
            features[sub] = 1 if sub in seq else 0
        return features
    
    X_train = pd.DataFrame([extract_substring_features(seq) for seq in train['sym_seq']])
    X_val = pd.DataFrame([extract_substring_features(seq) for seq in val['sym_seq']])
    
    y_train = train['default_flag']
    y_val = val['default_flag']
    
    xgb_model = xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss', max_depth=3, learning_rate=0.1)
    xgb_model.fit(X_train, y_train)
    val_preds_xgb = xgb_model.predict_proba(X_val)[:, 1]
    auc_xgb = roc_auc_score(y_val, val_preds_xgb)
    
    print(f'Min count: {min_count}, Features: {len(valid_substrings)}, XGB AUC: {auc_xgb:.4f}')
    
    if auc_xgb > best_auc:
        best_auc = auc_xgb
        best_min_count = min_count
        best_model = xgb_model
        best_features = valid_substrings

print(f'\nBest Min Count: {best_min_count}, Best Val AUC: {best_auc:.4f}')

# Evaluate on test set
def extract_best_features(seq):
    features = {}
    for sub in best_features:
        features[sub] = 1 if sub in seq else 0
    return features

X_test = pd.DataFrame([extract_best_features(seq) for seq in test['sym_seq']])
y_test = test['default_flag']

test_preds = best_model.predict_proba(X_test)[:, 1]
test_auc = roc_auc_score(y_test, test_preds)
print(f'Test AUC: {test_auc:.4f}')

# Plot ROC curve
from sklearn.metrics import roc_curve
fpr, tpr, _ = roc_curve(y_test, test_preds)
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, label=f'XGBoost (AUC = {test_auc:.4f})')
plt.plot([0, 1], [0, 1], 'k--')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve on Test Set')
plt.legend()
plt.savefig('report/images/roc_curve.png')
plt.close()
