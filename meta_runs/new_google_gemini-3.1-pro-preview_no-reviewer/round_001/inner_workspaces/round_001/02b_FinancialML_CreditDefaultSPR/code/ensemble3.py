import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import Levenshtein
from hmmlearn import hmm
from collections import defaultdict

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# 1. Motif Features
def get_all_substrings(seqs, min_len, max_len):
    substrings = set()
    for seq in seqs:
        for i in range(len(seq)):
            for j in range(i + min_len, min(i + max_len + 1, len(seq) + 1)):
                substrings.add(seq[i:j])
    return list(substrings)

train_0 = train[train['default_flag'] == 0]['sym_seq']
train_1 = train[train['default_flag'] == 1]['sym_seq']

all_subs = get_all_substrings(train['sym_seq'], 2, 10)
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

X_train_motif = extract_motif_features(train, top_motifs)
X_val_motif = extract_motif_features(val, top_motifs)
X_test_motif = extract_motif_features(test, top_motifs)

motif_model = xgb.XGBClassifier(eval_metric='logloss', random_state=42)
motif_model.fit(X_train_motif, train['default_flag'])

val_pred_motif = motif_model.predict_proba(X_val_motif)[:, 1]
test_pred_motif = motif_model.predict_proba(X_test_motif)[:, 1]

# 2. Distance Features
def get_avg_distance(seq, ref_seqs):
    dists = [Levenshtein.distance(seq, ref) for ref in ref_seqs]
    return np.mean(dists)

train_0_list = train_0.tolist()
train_1_list = train_1.tolist()

val_pred_dist = []
for seq in val['sym_seq']:
    dist_0_avg = get_avg_distance(seq, train_0_list)
    dist_1_avg = get_avg_distance(seq, train_1_list)
    val_pred_dist.append(dist_0_avg - dist_1_avg)

test_pred_dist = []
for seq in test['sym_seq']:
    dist_0_avg = get_avg_distance(seq, train_0_list)
    dist_1_avg = get_avg_distance(seq, train_1_list)
    test_pred_dist.append(dist_0_avg - dist_1_avg)

# 3. HMM Features
chars = ['1', '2', 'A', 'B', 'C', 'D']
char_to_idx = {c: i for i, c in enumerate(chars)}

def encode_seq(seq):
    return np.array([char_to_idx[c] for c in seq]).reshape(-1, 1)

X_train_0_hmm = np.concatenate([encode_seq(s) for s in train_0])
lengths_0 = [len(s) for s in train_0]

X_train_1_hmm = np.concatenate([encode_seq(s) for s in train_1])
lengths_1 = [len(s) for s in train_1]

hmm_0 = hmm.CategoricalHMM(n_components=8, random_state=42, n_iter=50)
hmm_0.fit(X_train_0_hmm, lengths_0)

hmm_1 = hmm.CategoricalHMM(n_components=8, random_state=42, n_iter=50)
hmm_1.fit(X_train_1_hmm, lengths_1)

val_pred_hmm = []
for seq in val['sym_seq']:
    x = encode_seq(seq)
    score_0 = hmm_0.score(x)
    score_1 = hmm_1.score(x)
    val_pred_hmm.append(score_1 - score_0)

test_pred_hmm = []
for seq in test['sym_seq']:
    x = encode_seq(seq)
    score_0 = hmm_0.score(x)
    score_1 = hmm_1.score(x)
    test_pred_hmm.append(score_1 - score_0)

# Ensemble
val_pred_motif = np.array(val_pred_motif)
val_pred_dist = np.array(val_pred_dist)
val_pred_hmm = np.array(val_pred_hmm)

test_pred_motif = np.array(test_pred_motif)
test_pred_dist = np.array(test_pred_dist)
test_pred_hmm = np.array(test_pred_hmm)

# Normalize predictions to 0-1 range for simple averaging
def normalize(x):
    return (x - np.min(x)) / (np.max(x) - np.min(x))

val_pred_dist_norm = normalize(val_pred_dist)
val_pred_hmm_norm = normalize(val_pred_hmm)

test_pred_dist_norm = normalize(test_pred_dist)
test_pred_hmm_norm = normalize(test_pred_hmm)

# Try different weights
for w_motif in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
    for w_dist in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        for w_hmm in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
            if w_motif + w_dist + w_hmm == 0:
                continue
            
            val_pred_ensemble = (w_motif * val_pred_motif + w_dist * val_pred_dist_norm + w_hmm * val_pred_hmm_norm) / (w_motif + w_dist + w_hmm)
            val_auc = roc_auc_score(val['default_flag'], val_pred_ensemble)
            
            if val_auc > 0.62:
                print(f'Weights: Motif={w_motif}, Dist={w_dist}, HMM={w_hmm} -> Val AUC: {val_auc:.4f}')
