import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.metrics import roc_auc_score, roc_curve, classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score
from itertools import product
import warnings
warnings.filterwarnings('ignore')
import json

train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

CHARS = ['1', '2', 'A', 'B', 'C', 'D']
SEQ_LEN = 20

y_train = train['default_flag'].values
y_val   = val['default_flag'].values
y_test  = test['default_flag'].values

# Combine train+val for final model
train_full = pd.concat([train, val], ignore_index=True)
y_full = train_full['default_flag'].values

# ── Minimal feature set: just positional one-hot + bigrams ──────────────────
def extract_minimal(df):
    seqs = df['sym_seq'].tolist()
    feats = {}
    # Positional one-hot
    for pos in range(SEQ_LEN):
        for c in CHARS:
            feats[f'p{pos}_{c}'] = [1 if s[pos] == c else 0 for s in seqs]
    # Character counts
    for c in CHARS:
        feats[f'cnt_{c}'] = [s.count(c) for s in seqs]
    # Bigrams
    for a, b in product(CHARS, CHARS):
        bg = a + b
        feats[f'bg_{bg}'] = [sum(1 for i in range(len(s)-1) if s[i:i+2] == bg) for s in seqs]
    return pd.DataFrame(feats)

X_train = extract_minimal(train)
X_val   = extract_minimal(val)
X_test  = extract_minimal(test)
X_full  = extract_minimal(train_full)

print(f'Feature matrix: {X_train.shape}')

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_val_sc   = scaler.transform(X_val)
X_test_sc  = scaler.transform(X_test)

scaler2 = StandardScaler()
X_full_sc  = scaler2.fit_transform(X_full)
X_test_sc2 = scaler2.transform(X_test)

# ── Systematic search for best model ────────────────────────────────────────
print('\n=== Systematic model search (train->val->test) ===')
best_val = 0
best_result = None

for C in [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]:
    model = LogisticRegression(max_iter=3000, C=C, random_state=42)
    model.fit(X_train_sc, y_train)
    val_auc  = roc_auc_score(y_val,  model.predict_proba(X_val_sc)[:, 1])
    test_auc = roc_auc_score(y_test, model.predict_proba(X_test_sc)[:, 1])
    print(f'  LR C={C}: Val={val_auc:.4f}  Test={test_auc:.4f}')
    if val_auc > best_val:
        best_val = val_auc
        best_result = ('LR', C, val_auc, test_auc, model.predict_proba(X_test_sc)[:, 1])

for C in [0.001, 0.01, 0.1, 1.0, 10.0]:
    for kernel in ['rbf', 'linear']:
        model = SVC(kernel=kernel, probability=True, C=C, random_state=42)
        model.fit(X_train_sc, y_train)
        val_auc  = roc_auc_score(y_val,  model.predict_proba(X_val_sc)[:, 1])
        test_auc = roc_auc_score(y_test, model.predict_proba(X_test_sc)[:, 1])
        print(f'  SVM {kernel} C={C}: Val={val_auc:.4f}  Test={test_auc:.4f}')
        if val_auc > best_val:
            best_val = val_auc
            best_result = (f'SVM_{kernel}', C, val_auc, test_auc, model.predict_proba(X_test_sc)[:, 1])

for hidden in [(32,), (64,), (128,), (64, 32), (128, 64), (256, 128, 64)]:
    for alpha in [0.001, 0.01, 0.1]:
        model = MLPClassifier(hidden_layer_sizes=hidden, alpha=alpha, max_iter=1000, random_state=42)
        model.fit(X_train_sc, y_train)
        val_auc  = roc_auc_score(y_val,  model.predict_proba(X_val_sc)[:, 1])
        test_auc = roc_auc_score(y_test, model.predict_proba(X_test_sc)[:, 1])
        print(f'  MLP {hidden} alpha={alpha}: Val={val_auc:.4f}  Test={test_auc:.4f}')
        if val_auc > best_val:
            best_val = val_auc
            best_result = (f'MLP_{hidden}', alpha, val_auc, test_auc, model.predict_proba(X_test_sc)[:, 1])

print(f'\nBest: {best_result[0]} param={best_result[1]}  Val={best_result[2]:.4f}  Test={best_result[3]:.4f}')

# ── Final model: LR with best C, trained on train only ──────────────────────
# Use LR C=0.1 as it was consistently best in earlier experiments
final_model = LogisticRegression(max_iter=3000, C=0.1, random_state=42)
final_model.fit(X_train_sc, y_train)
final_val_proba  = final_model.predict_proba(X_val_sc)[:, 1]
final_test_proba = final_model.predict_proba(X_test_sc)[:, 1]
final_val_auc  = roc_auc_score(y_val,  final_val_proba)
final_test_auc = roc_auc_score(y_test, final_test_proba)
print(f'\nFinal LR C=0.1: Val AUC={final_val_auc:.4f}  Test AUC={final_test_auc:.4f}')

# Also try the best found model
best_test_proba = best_result[4]
best_test_auc   = best_result[3]
best_val_auc    = best_result[2]

# Use whichever has better val AUC
if best_val_auc >= final_val_auc:
    chosen_name = best_result[0]
    chosen_val_auc  = best_val_auc
    chosen_test_auc = best_test_auc
    chosen_test_proba = best_test_proba
else:
    chosen_name = 'LR C=0.1'
    chosen_val_auc  = final_val_auc
    chosen_test_auc = final_test_auc
    chosen_test_proba = final_test_proba

print(f'\nChosen model: {chosen_name}  Val AUC={chosen_val_auc:.4f}  Test AUC={chosen_test_auc:.4f}')

# ── Save final results ────────────────────────────────────────────────────────
summary = {
    'final_model': chosen_name,
    'val_auc':    round(chosen_val_auc, 4),
    'test_auc':   round(chosen_test_auc, 4),
    'baseline_auc': 0.72,
    'lr_c01': {'val_auc': round(final_val_auc, 4), 'test_auc': round(final_test_auc, 4)}
}
with open('outputs/best_results.json', 'w') as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))

# Classification report
chosen_preds = (chosen_test_proba >= 0.5).astype(int)
print(f'\nClassification Report:')
print(classification_report(y_test, chosen_preds, target_names=['No Default', 'Default']))
