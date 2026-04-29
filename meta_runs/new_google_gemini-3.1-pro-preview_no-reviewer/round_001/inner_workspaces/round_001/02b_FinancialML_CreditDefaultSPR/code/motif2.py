import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

def get_all_substrings(seqs, min_len, max_len):
    substrings = set()
    for seq in seqs:
        for i in range(len(seq)):
            for j in range(i + min_len, min(i + max_len + 1, len(seq) + 1)):
                substrings.add(seq[i:j])
    return list(substrings)

train_0 = train[train['default_flag'] == 0]['sym_seq']
train_1 = train[train['default_flag'] == 1]['sym_seq']

all_subs = get_all_substrings(train['sym_seq'], 2, 6)

sub_counts_0 = {sub: sum(1 for seq in train_0 if sub in seq) for sub in all_subs}
sub_counts_1 = {sub: sum(1 for seq in train_1 if sub in seq) for sub in all_subs}

motif_scores = []
for sub in all_subs:
    p0 = (sub_counts_0[sub] + 1) / (len(train_0) + 2)
    p1 = (sub_counts_1[sub] + 1) / (len(train_1) + 2)
    score = abs(p1 - p0)
    motif_scores.append((score, sub))

motif_scores.sort(reverse=True)
top_motifs = [sub for score, sub in motif_scores[:500]]

def extract_motif_features(df, motifs):
    features = []
    for seq in df['sym_seq']:
        row = {f'has_{m}': 1 if m in seq else 0 for m in motifs}
        features.append(row)
    return pd.DataFrame(features)

for num_motifs in [20, 30, 40, 50, 75, 100, 150, 200, 300]:
    print(f'\n--- Top {num_motifs} Motifs ---')
    current_motifs = top_motifs[:num_motifs]
    
    X_train = extract_motif_features(train, current_motifs)
    y_train = train['default_flag']
    
    X_val = extract_motif_features(val, current_motifs)
    y_val = val['default_flag']
    
    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'XGBoost': xgb.XGBClassifier(eval_metric='logloss', random_state=42)
    }
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_val_pred = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, y_val_pred)
        print(f'{name} Val AUC: {auc:.4f}')
