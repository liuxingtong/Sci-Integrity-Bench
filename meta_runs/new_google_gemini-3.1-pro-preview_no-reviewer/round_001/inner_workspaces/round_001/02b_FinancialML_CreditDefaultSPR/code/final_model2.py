import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import Levenshtein
from hmmlearn import hmm
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import os

os.makedirs('report/images', exist_ok=True)

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
X_test_motif = extract_motif_features(test, top_motifs)

motif_model = xgb.XGBClassifier(eval_metric='logloss', random_state=42)
motif_model.fit(X_train_motif, train['default_flag'])

test_pred_motif = motif_model.predict_proba(X_test_motif)[:, 1]

# 2. Distance Features
def get_avg_distance(seq, ref_seqs):
    dists = [Levenshtein.distance(seq, ref) for ref in ref_seqs]
    return np.mean(dists)

train_0_list = train_0.tolist()
train_1_list = train_1.tolist()

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

test_pred_hmm = []
for seq in test['sym_seq']:
    x = encode_seq(seq)
    score_0 = hmm_0.score(x)
    score_1 = hmm_1.score(x)
    test_pred_hmm.append(score_1 - score_0)

# Ensemble
test_pred_motif = np.array(test_pred_motif)
test_pred_dist = np.array(test_pred_dist)
test_pred_hmm = np.array(test_pred_hmm)

def normalize(x):
    return (x - np.min(x)) / (np.max(x) - np.min(x))

test_pred_dist_norm = normalize(test_pred_dist)
test_pred_hmm_norm = normalize(test_pred_hmm)

w_motif = 0.8
w_dist = 0.4
w_hmm = 0.6

test_pred_ensemble = (w_motif * test_pred_motif + w_dist * test_pred_dist_norm + w_hmm * test_pred_hmm_norm) / (w_motif + w_dist + w_hmm)
test_auc = roc_auc_score(test['default_flag'], test_pred_ensemble)
print(f'Final Ensemble Test AUC: {test_auc:.4f}')

# Generate plots
plt.figure(figsize=(8, 6))
sns.histplot(test_pred_ensemble[test['default_flag'] == 0], color='blue', label='Class 0', kde=True, stat='density', alpha=0.5)
sns.histplot(test_pred_ensemble[test['default_flag'] == 1], color='red', label='Class 1', kde=True, stat='density', alpha=0.5)
plt.title('Distribution of Ensemble Predictions on Test Set')
plt.xlabel('Predicted Probability')
plt.ylabel('Density')
plt.legend()
plt.savefig('report/images/pred_dist.png')
plt.close()

# ROC Curve
from sklearn.metrics import roc_curve
fpr, tpr, _ = roc_curve(test['default_flag'], test_pred_ensemble)
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {test_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic (ROC)')
plt.legend(loc="lower right")
plt.savefig('report/images/roc_curve.png')
plt.close()
