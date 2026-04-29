import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# Combine train and val for motif discovery
train_full = pd.concat([train, val])

def get_all_substrings(seqs, min_len, max_len):
    substrings = set()
    for seq in seqs:
        for i in range(len(seq)):
            for j in range(i + min_len, min(i + max_len + 1, len(seq) + 1)):
                substrings.add(seq[i:j])
    return list(substrings)

train_0 = train_full[train_full['default_flag'] == 0]['sym_seq']
train_1 = train_full[train_full['default_flag'] == 1]['sym_seq']

all_subs = get_all_substrings(train_full['sym_seq'], 2, 10)

sub_counts_0 = {sub: sum(1 for seq in train_0 if sub in seq) for sub in all_subs}
sub_counts_1 = {sub: sum(1 for seq in train_1 if sub in seq) for sub in all_subs}

motif_scores = []
for sub in all_subs:
    p0 = (sub_counts_0[sub] + 1) / (len(train_0) + 2)
    p1 = (sub_counts_1[sub] + 1) / (len(train_1) + 2)
    score = abs(p1 - p0)
    motif_scores.append((score, sub))

motif_scores.sort(reverse=True)
top_motifs = [sub for score, sub in motif_scores[:29]]

def extract_motif_features(df, motifs):
    features = []
    for seq in df['sym_seq']:
        row = {f'has_{m}': 1 if m in seq else 0 for m in motifs}
        features.append(row)
    return pd.DataFrame(features)

X_train_full = extract_motif_features(train_full, top_motifs)
y_train_full = train_full['default_flag']

X_test = extract_motif_features(test, top_motifs)
y_test = test['default_flag']

model = xgb.XGBClassifier(eval_metric='logloss', random_state=42)
model.fit(X_train_full, y_train_full)

y_test_pred = model.predict_proba(X_test)[:, 1]
test_auc = roc_auc_score(y_test, y_test_pred)
print(f'Test AUC (Train+Val Motif Discovery): {test_auc:.4f}')
