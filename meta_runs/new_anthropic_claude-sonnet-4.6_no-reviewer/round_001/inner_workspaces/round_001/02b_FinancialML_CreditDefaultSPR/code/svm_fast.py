import pandas as pd
import numpy as np
from collections import Counter
from sklearn.metrics import roc_auc_score
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from itertools import product
import warnings
warnings.filterwarnings('ignore')

train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

CHARS = ['1', '2', 'A', 'B', 'C', 'D']
SEQ_LEN = 20

y_train = train['default_flag'].values
y_val   = val['default_flag'].values
y_test  = test['default_flag'].values

train_full = pd.concat([train, val], ignore_index=True)
y_full = train_full['default_flag'].values

def extract_minimal(df):
    seqs = df['sym_seq'].tolist()
    feats = {}
    for pos in range(SEQ_LEN):
        for c in CHARS:
            feats[f'p{pos}_{c}'] = [1 if s[pos] == c else 0 for s in seqs]
    for c in CHARS:
        feats[f'cnt_{c}'] = [s.count(c) for s in seqs]
    for a, b in product(CHARS, CHARS):
        bg = a + b
        feats[f'bg_{bg}'] = [sum(1 for i in range(len(s)-1) if s[i:i+2] == bg) for s in seqs]
    return pd.DataFrame(feats)

X_train = extract_minimal(train)
X_val   = extract_minimal(val)
X_test  = extract_minimal(test)
X_full  = extract_minimal(train_full)

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_val_sc   = scaler.transform(X_val)
X_test_sc  = scaler.transform(X_test)

scaler2 = StandardScaler()
X_full_sc  = scaler2.fit_transform(X_full)
X_test_sc2 = scaler2.transform(X_test)

# LinearSVC is much faster than SVC(kernel='linear')
print('=== LinearSVC (fast) ===')
for C in [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]:
    model = LinearSVC(C=C, max_iter=5000, random_state=42)
    cal = CalibratedClassifierCV(model, cv=3)
    cal.fit(X_train_sc, y_train)
    val_auc  = roc_auc_score(y_val,  cal.predict_proba(X_val_sc)[:, 1])
    test_auc = roc_auc_score(y_test, cal.predict_proba(X_test_sc)[:, 1])
    print(f'  LinearSVC C={C}: Val={val_auc:.4f}  Test={test_auc:.4f}')

# LR with different solvers
print('\n=== LR different solvers ===')
for C in [0.001, 0.01, 0.1, 1.0, 10.0]:
    for solver in ['lbfgs', 'liblinear', 'saga']:
        model = LogisticRegression(C=C, solver=solver, max_iter=3000, random_state=42)
        model.fit(X_train_sc, y_train)
        val_auc  = roc_auc_score(y_val,  model.predict_proba(X_val_sc)[:, 1])
        test_auc = roc_auc_score(y_test, model.predict_proba(X_test_sc)[:, 1])
        print(f'  LR C={C} {solver}: Val={val_auc:.4f}  Test={test_auc:.4f}')

# Train on full data
print('\n=== LR trained on train+val ===')
for C in [0.001, 0.01, 0.1, 1.0]:
    model = LogisticRegression(C=C, max_iter=3000, random_state=42)
    model.fit(X_full_sc, y_full)
    test_auc = roc_auc_score(y_test, model.predict_proba(X_test_sc2)[:, 1])
    print(f'  LR C={C} (train+val): Test={test_auc:.4f}')

# Permutation test
print('\n=== Permutation test ===')
np.random.seed(42)
null_aucs = []
for _ in range(500):
    perm_labels = np.random.permutation(y_train)
    feat = np.array([s.count('2') for s in train['sym_seq']])
    auc = roc_auc_score(perm_labels, feat)
    null_aucs.append(auc)
print(f'Null AUC: mean={np.mean(null_aucs):.4f}, std={np.std(null_aucs):.4f}')
real_feat = np.array([s.count('2') for s in train['sym_seq']])
real_auc = roc_auc_score(y_train, real_feat)
print(f'Real AUC (count_2): {real_auc:.4f}')
print(f'Z-score: {(real_auc - np.mean(null_aucs)) / np.std(null_aucs):.2f}')
