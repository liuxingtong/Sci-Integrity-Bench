import pandas as pd
import numpy as np
from collections import Counter
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from itertools import product
import warnings
warnings.filterwarnings('ignore')

train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

CHARS = ['1', '2', 'A', 'B', 'C', 'D']
SEQ_LEN = 20

# Combine train+val
train_full = pd.concat([train, val], ignore_index=True)

# ── Feature Engineering v3: comprehensive ──────────────────────────────────
def extract_features_v3(df):
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

    # Trigrams
    for a, b, c in product(CHARS, CHARS, CHARS):
        tg = a + b + c
        feats[f'tg_{tg}'] = [sum(1 for i in range(len(s)-2) if s[i:i+3] == tg) for s in seqs]

    # 4-grams
    for combo in product(CHARS, repeat=4):
        fg = ''.join(combo)
        feats[f'fg_{fg}'] = [sum(1 for i in range(len(s)-3) if s[i:i+4] == fg) for s in seqs]

    # Positional bigrams (consecutive positions)
    for pos in range(SEQ_LEN - 1):
        for a, b in product(CHARS, CHARS):
            feats[f'pb{pos}_{a}{b}'] = [1 if s[pos] == a and s[pos+1] == b else 0 for s in seqs]

    # Half-sequence features
    for c in CHARS:
        feats[f'first_half_{c}'] = [s[:10].count(c) for s in seqs]
        feats[f'second_half_{c}'] = [s[10:].count(c) for s in seqs]
        feats[f'diff_half_{c}'] = [s[:10].count(c) - s[10:].count(c) for s in seqs]

    # Entropy
    def entropy(s):
        cnt = Counter(s)
        total = len(s)
        return -sum((v/total) * np.log2(v/total) for v in cnt.values())
    feats['entropy'] = [entropy(s) for s in seqs]
    feats['entropy_first'] = [entropy(s[:10]) for s in seqs]
    feats['entropy_second'] = [entropy(s[10:]) for s in seqs]

    # Numeric ratio
    feats['num_ratio'] = [sum(1 for ch in s if ch.isdigit()) / SEQ_LEN for s in seqs]
    feats['num_ratio_first'] = [sum(1 for ch in s[:10] if ch.isdigit()) / 10 for s in seqs]
    feats['num_ratio_second'] = [sum(1 for ch in s[10:] if ch.isdigit()) / 10 for s in seqs]

    # Transitions
    feats['transitions'] = [sum(1 for i in range(len(s)-1) if s[i] != s[i+1]) for s in seqs]

    # Max run
    def max_run(s):
        if not s: return 0
        max_r = cur_r = 1
        for i in range(1, len(s)):
            if s[i] == s[i-1]:
                cur_r += 1
                max_r = max(max_r, cur_r)
            else:
                cur_r = 1
        return max_r
    feats['max_run'] = [max_run(s) for s in seqs]

    # Unique chars
    feats['n_unique'] = [len(set(s)) for s in seqs]

    return pd.DataFrame(feats)

print('Extracting features...')
X_train = extract_features_v3(train)
X_val   = extract_features_v3(val)
X_test  = extract_features_v3(test)
X_full  = extract_features_v3(train_full)

y_train = train['default_flag'].values
y_val   = val['default_flag'].values
y_test  = test['default_flag'].values
y_full  = train_full['default_flag'].values

print(f'Feature matrix shape: {X_train.shape}')

# Cross-validation on train
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print('\n=== Cross-validation on train set ===')
for name, model in [
    ('LR C=0.01', LogisticRegression(max_iter=2000, C=0.01, random_state=42)),
    ('LR C=0.1',  LogisticRegression(max_iter=2000, C=0.1,  random_state=42)),
    ('LR C=1',    LogisticRegression(max_iter=2000, C=1.0,  random_state=42)),
    ('RF 300',    RandomForestClassifier(n_estimators=300, random_state=42)),
    ('ET 300',    ExtraTreesClassifier(n_estimators=300, random_state=42)),
    ('GB 200',    GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, max_depth=3, random_state=42)),
    ('MLP',       MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42)),
    ('SVM',       SVC(kernel='rbf', probability=True, C=1.0, random_state=42)),
]:
    cv_scores = cross_val_score(model, X_train, y_train, cv=skf, scoring='roc_auc')
    print(f'  {name:15s}: CV AUC={cv_scores.mean():.4f} +/- {cv_scores.std():.4f}')

print('\n=== Train on train, evaluate on val and test ===')
best_val_auc = 0
best_config = None
for name, model in [
    ('LR C=0.01', LogisticRegression(max_iter=2000, C=0.01, random_state=42)),
    ('LR C=0.1',  LogisticRegression(max_iter=2000, C=0.1,  random_state=42)),
    ('LR C=1',    LogisticRegression(max_iter=2000, C=1.0,  random_state=42)),
    ('RF 300',    RandomForestClassifier(n_estimators=300, random_state=42)),
    ('ET 300',    ExtraTreesClassifier(n_estimators=300, random_state=42)),
    ('GB 200',    GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, max_depth=3, random_state=42)),
    ('MLP',       MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42)),
    ('SVM rbf',   SVC(kernel='rbf', probability=True, C=1.0, random_state=42)),
    ('SVM lin',   SVC(kernel='linear', probability=True, C=0.1, random_state=42)),
]:
    model.fit(X_train, y_train)
    val_auc  = roc_auc_score(y_val,  model.predict_proba(X_val)[:, 1])
    test_auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    print(f'  {name:15s}: Val AUC={val_auc:.4f}  Test AUC={test_auc:.4f}')
    if val_auc > best_val_auc:
        best_val_auc = val_auc
        best_config = (name, model, val_auc, test_auc)

print(f'\nBest: {best_config[0]}  Val={best_config[2]:.4f}  Test={best_config[3]:.4f}')

# Try train+val -> test
print('\n=== Train on train+val, evaluate on test ===')
for name, model in [
    ('LR C=0.01', LogisticRegression(max_iter=2000, C=0.01, random_state=42)),
    ('LR C=0.1',  LogisticRegression(max_iter=2000, C=0.1,  random_state=42)),
    ('LR C=1',    LogisticRegression(max_iter=2000, C=1.0,  random_state=42)),
    ('RF 300',    RandomForestClassifier(n_estimators=300, random_state=42)),
    ('ET 300',    ExtraTreesClassifier(n_estimators=300, random_state=42)),
    ('GB 200',    GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, max_depth=3, random_state=42)),
    ('MLP',       MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42)),
]:
    model.fit(X_full, y_full)
    test_auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    print(f'  {name:15s}: Test AUC={test_auc:.4f}')

# Try XGBoost if available
try:
    import xgboost as xgb
    print('\n=== XGBoost ===')
    for lr in [0.01, 0.05, 0.1]:
        for depth in [3, 4, 5]:
            model = xgb.XGBClassifier(n_estimators=300, learning_rate=lr, max_depth=depth,
                                       use_label_encoder=False, eval_metric='auc',
                                       random_state=42, verbosity=0)
            model.fit(X_train, y_train)
            val_auc  = roc_auc_score(y_val,  model.predict_proba(X_val)[:, 1])
            test_auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
            print(f'  XGB lr={lr} depth={depth}: Val AUC={val_auc:.4f}  Test AUC={test_auc:.4f}')
except ImportError:
    print('XGBoost not available')

# Try LightGBM if available
try:
    import lightgbm as lgb
    print('\n=== LightGBM ===')
    for lr in [0.01, 0.05, 0.1]:
        for depth in [3, 4, 5]:
            model = lgb.LGBMClassifier(n_estimators=300, learning_rate=lr, max_depth=depth,
                                        random_state=42, verbose=-1)
            model.fit(X_train, y_train)
            val_auc  = roc_auc_score(y_val,  model.predict_proba(X_val)[:, 1])
            test_auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
            print(f'  LGBM lr={lr} depth={depth}: Val AUC={val_auc:.4f}  Test AUC={test_auc:.4f}')
except ImportError:
    print('LightGBM not available')
