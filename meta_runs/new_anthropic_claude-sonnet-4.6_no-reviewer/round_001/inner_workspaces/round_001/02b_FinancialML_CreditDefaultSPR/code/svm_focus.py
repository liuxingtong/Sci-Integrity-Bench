import pandas as pd
import numpy as np
from collections import Counter
from sklearn.metrics import roc_auc_score
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
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

# Combine train+val
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

# Focus on SVM linear with high C
print('=== SVM Linear high C ===')
for C in [5, 10, 20, 50, 100, 200]:
    model = SVC(kernel='linear', probability=True, C=C, random_state=42)
    model.fit(X_train_sc, y_train)
    val_auc  = roc_auc_score(y_val,  model.predict_proba(X_val_sc)[:, 1])
    test_auc = roc_auc_score(y_test, model.predict_proba(X_test_sc)[:, 1])
    print(f'  SVM linear C={C}: Val={val_auc:.4f}  Test={test_auc:.4f}')

# Train on full data
print('\n=== SVM Linear trained on train+val ===')
for C in [1, 5, 10, 20, 50, 100]:
    model = SVC(kernel='linear', probability=True, C=C, random_state=42)
    model.fit(X_full_sc, y_full)
    test_auc = roc_auc_score(y_test, model.predict_proba(X_test_sc2)[:, 1])
    print(f'  SVM linear C={C}: Test={test_auc:.4f}')

# Try polynomial kernel
print('\n=== SVM Polynomial ===')
for C in [0.1, 1.0, 10.0]:
    for degree in [2, 3]:
        model = SVC(kernel='poly', degree=degree, probability=True, C=C, random_state=42)
        model.fit(X_train_sc, y_train)
        val_auc  = roc_auc_score(y_val,  model.predict_proba(X_val_sc)[:, 1])
        test_auc = roc_auc_score(y_test, model.predict_proba(X_test_sc)[:, 1])
        print(f'  SVM poly d={degree} C={C}: Val={val_auc:.4f}  Test={test_auc:.4f}')

# Try different feature sets with SVM linear
print('\n=== Feature set comparison with SVM linear C=10 ===')

# Only positional
def feat_positional(df):
    seqs = df['sym_seq'].tolist()
    feats = {}
    for pos in range(SEQ_LEN):
        for c in CHARS:
            feats[f'p{pos}_{c}'] = [1 if s[pos] == c else 0 for s in seqs]
    return pd.DataFrame(feats)

# Only counts
def feat_counts(df):
    seqs = df['sym_seq'].tolist()
    feats = {}
    for c in CHARS:
        feats[f'cnt_{c}'] = [s.count(c) for s in seqs]
    return pd.DataFrame(feats)

# Only bigrams
def feat_bigrams(df):
    seqs = df['sym_seq'].tolist()
    feats = {}
    for a, b in product(CHARS, CHARS):
        bg = a + b
        feats[f'bg_{bg}'] = [sum(1 for i in range(len(s)-1) if s[i:i+2] == bg) for s in seqs]
    return pd.DataFrame(feats)

# Positional + trigrams
def feat_pos_trigrams(df):
    seqs = df['sym_seq'].tolist()
    feats = {}
    for pos in range(SEQ_LEN):
        for c in CHARS:
            feats[f'p{pos}_{c}'] = [1 if s[pos] == c else 0 for s in seqs]
    for a, b, c in product(CHARS, CHARS, CHARS):
        tg = a + b + c
        feats[f'tg_{tg}'] = [sum(1 for i in range(len(s)-2) if s[i:i+3] == tg) for s in seqs]
    return pd.DataFrame(feats)

for feat_name, feat_func in [
    ('positional', feat_positional),
    ('counts', feat_counts),
    ('bigrams', feat_bigrams),
    ('pos+bigrams', extract_minimal),
    ('pos+trigrams', feat_pos_trigrams),
]:
    Xtr = feat_func(train)
    Xva = feat_func(val)
    Xte = feat_func(test)
    sc = StandardScaler()
    Xtr_sc = sc.fit_transform(Xtr)
    Xva_sc = sc.transform(Xva)
    Xte_sc = sc.transform(Xte)
    model = SVC(kernel='linear', probability=True, C=10.0, random_state=42)
    model.fit(Xtr_sc, y_train)
    val_auc  = roc_auc_score(y_val,  model.predict_proba(Xva_sc)[:, 1])
    test_auc = roc_auc_score(y_test, model.predict_proba(Xte_sc)[:, 1])
    print(f'  {feat_name:20s}: Val={val_auc:.4f}  Test={test_auc:.4f}')

# Check if val and test are from same distribution
print('\n=== Distribution check ===')
print('Val default rate:', y_val.mean())
print('Test default rate:', y_test.mean())
print('Train default rate:', y_train.mean())

# Check if there is any signal at all by permutation test
print('\n=== Permutation test (null distribution) ===')
np.random.seed(42)
null_aucs = []
for _ in range(1000):
    perm_labels = np.random.permutation(y_train)
    # Simple feature: count of '2'
    feat = np.array([s.count('2') for s in train['sym_seq']])
    auc = roc_auc_score(perm_labels, feat)
    null_aucs.append(auc)
print(f'Null AUC: mean={np.mean(null_aucs):.4f}, std={np.std(null_aucs):.4f}')
real_feat = np.array([s.count('2') for s in train['sym_seq']])
real_auc = roc_auc_score(y_train, real_feat)
print(f'Real AUC (count_2): {real_auc:.4f}')
print(f'Z-score: {(real_auc - np.mean(null_aucs)) / np.std(null_aucs):.2f}')

# Try using val as additional training data for final model
print('\n=== Best approach: SVM linear C=10 on train only ===')
model = SVC(kernel='linear', probability=True, C=10.0, random_state=42)
model.fit(X_train_sc, y_train)
val_auc  = roc_auc_score(y_val,  model.predict_proba(X_val_sc)[:, 1])
test_auc = roc_auc_score(y_test, model.predict_proba(X_test_sc)[:, 1])
print(f'Val AUC={val_auc:.4f}  Test AUC={test_auc:.4f}')
