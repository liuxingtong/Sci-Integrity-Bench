import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
import xgboost as xgb
from sklearn.feature_extraction.text import CountVectorizer

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# The baseline is 0.72. We need to find the right features.
# Let's try to extract motifs or patterns.

def get_all_substrings(seq, min_len=1, max_len=20):
    substrings = []
    for i in range(len(seq)):
        for j in range(i + min_len, min(i + max_len + 1, len(seq) + 1)):
            substrings.append(seq[i:j])
    return substrings

# Let's find the most discriminative substrings
all_train_substrings = []
for seq in train['sym_seq']:
    all_train_substrings.extend(get_all_substrings(seq, 1, 10))

from collections import Counter
counts = Counter(all_train_substrings)
# Keep substrings that appear at least 5 times
valid_substrings = [sub for sub, count in counts.items() if count >= 5]
print(f'Found {len(valid_substrings)} valid substrings')

def extract_substring_features(seq):
    features = {}
    for sub in valid_substrings:
        features[sub] = 1 if sub in seq else 0
    return features

X_train = pd.DataFrame([extract_substring_features(seq) for seq in train['sym_seq']])
X_val = pd.DataFrame([extract_substring_features(seq) for seq in val['sym_seq']])

y_train = train['default_flag']
y_val = val['default_flag']

# XGBoost
xgb_model = xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss')
xgb_model.fit(X_train, y_train)
val_preds_xgb = xgb_model.predict_proba(X_val)[:, 1]
auc_xgb = roc_auc_score(y_val, val_preds_xgb)
print(f'XGB AUC: {auc_xgb:.4f}')
