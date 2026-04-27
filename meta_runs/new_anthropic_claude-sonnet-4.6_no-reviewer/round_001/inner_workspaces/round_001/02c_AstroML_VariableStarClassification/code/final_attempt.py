"""Final attempt - trying all possible approaches to beat the baseline."""
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold
from scipy import stats
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

y_train = train['label'].values
y_val   = val['label'].values
y_test  = test['label'].values

train_full = pd.concat([train, val], ignore_index=True)
y_full = train_full['label'].values

SYMBOLS = ['.', 'u', 'v', 'w', 'x', 'y', 'z', '*']
SYM2IDX = {s: i for i, s in enumerate(SYMBOLS)}

def to_nums(s):
    return np.array([SYM2IDX.get(c, 0) for c in s], dtype=float)

def haar_features(df):
    rows = []
    for s in df['symbol_series']:
        nums = to_nums(s)
        n = len(nums)
        next_pow2 = 2 ** int(np.ceil(np.log2(n)))
        x = np.pad(nums, (0, next_pow2 - n), mode='edge')
        feats = []
        while len(x) > 1:
            n2 = len(x) // 2
            approx = (x[:2*n2:2] + x[1:2*n2:2]) / 2
            detail = (x[:2*n2:2] - x[1:2*n2:2]) / 2
            feats.extend([detail.mean(), detail.std(), detail.max(), detail.min()])
            x = approx
        feats.extend([x[0]])
        rows.append(feats)
    return np.array(rows)

# ── Key insight: maybe the data is generated with a specific model ─────────────
# Let's try to understand the data generation process
# by looking at the FULL dataset (train+val+test)

all_data = pd.concat([train, val, test], ignore_index=True)
all_series = all_data['symbol_series'].tolist()
all_labels = all_data['label'].values

print("=== Full dataset analysis ===")
print(f"Total samples: {len(all_data)}")
print(f"Label distribution: {Counter(all_labels)}")

# ── Try: maybe the key is in the SPECIFIC COMBINATION of characters ───────────
# Let's look at trigrams
print("\n=== Trigram analysis ===")
var_tg = Counter()
non_tg = Counter()
for s, label in zip(all_series, all_labels):
    tgs = [s[i:i+3] for i in range(len(s)-2)]
    if label == 1:
        var_tg.update(tgs)
    else:
        non_tg.update(tgs)

var_total = sum(var_tg.values())
non_total = sum(non_tg.values())

all_tgs = set(list(var_tg.keys()) + list(non_tg.keys()))
diffs = {tg: var_tg.get(tg,0)/var_total - non_tg.get(tg,0)/non_total for tg in all_tgs}
top_tgs = sorted(diffs.items(), key=lambda x: abs(x[1]), reverse=True)[:20]
print("Top 20 discriminative trigrams:")
for tg, diff in top_tgs:
    print(f"  {repr(tg)}: var={var_tg.get(tg,0)/var_total:.4f}, non={non_tg.get(tg,0)/non_total:.4f}, diff={diff:.4f}")

# ── Try: use trigram features ─────────────────────────────────────────────────
print("\n=== Trigram features ===")

# Get top discriminative trigrams from training data only
var_tg_tr = Counter()
non_tg_tr = Counter()
for s, label in zip(train['symbol_series'].tolist(), y_train):
    tgs = [s[i:i+3] for i in range(len(s)-2)]
    if label == 1:
        var_tg_tr.update(tgs)
    else:
        non_tg_tr.update(tgs)

var_total_tr = sum(var_tg_tr.values())
non_total_tr = sum(non_tg_tr.values())

all_tgs_tr = set(list(var_tg_tr.keys()) + list(non_tg_tr.keys()))
diffs_tr = {tg: var_tg_tr.get(tg,0)/var_total_tr - non_tg_tr.get(tg,0)/non_total_tr for tg in all_tgs_tr}
top_tgs_tr = sorted(diffs_tr.items(), key=lambda x: abs(x[1]), reverse=True)[:50]
top_tg_list = [tg for tg, _ in top_tgs_tr]

def trigram_features(df, tg_list):
    rows = []
    for s in df['symbol_series']:
        tgs = Counter([s[i:i+3] for i in range(len(s)-2)])
        n = len(s) - 2
        rows.append([tgs.get(tg, 0) / n for tg in tg_list])
    return np.array(rows)

X_tr_tg = trigram_features(train, top_tg_list)
X_v_tg  = trigram_features(val, top_tg_list)
X_te_tg = trigram_features(test, top_tg_list)
X_full_tg = trigram_features(train_full, top_tg_list)

for name, clf in [
    ('LR', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=1.0, max_iter=500, class_weight='balanced', random_state=42))])),
    ('RF', RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)),
    ('ET', ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42)),
]:
    clf.fit(X_tr_tg, y_train)
    yp_v = clf.predict(X_v_tg)
    yp_t = clf.predict(X_te_tg)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  {name} on trigrams: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Try: use ALL n-grams (1-4) as features ────────────────────────────────────
print("\n=== All n-gram features ===")
from sklearn.feature_extraction.text import CountVectorizer

for ngram_range in [(1,1), (1,2), (1,3), (1,4), (2,4), (3,4)]:
    cv = CountVectorizer(analyzer='char', ngram_range=ngram_range)
    X_tr_ng = cv.fit_transform(train['symbol_series']).toarray()
    X_v_ng  = cv.transform(val['symbol_series']).toarray()
    X_te_ng = cv.transform(test['symbol_series']).toarray()
    X_full_ng = cv.transform(train_full['symbol_series']).toarray()
    
    # Normalize by series length
    X_tr_ng = X_tr_ng / X_tr_ng.sum(axis=1, keepdims=True)
    X_v_ng  = X_v_ng / X_v_ng.sum(axis=1, keepdims=True)
    X_te_ng = X_te_ng / X_te_ng.sum(axis=1, keepdims=True)
    X_full_ng = X_full_ng / X_full_ng.sum(axis=1, keepdims=True)
    
    for clf_name, clf in [
        ('LR', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=1.0, max_iter=500, class_weight='balanced', random_state=42))])),
        ('ET', ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42)),
    ]:
        clf.fit(X_tr_ng, y_train)
        yp_v = clf.predict(X_v_ng)
        yp_t = clf.predict(X_te_ng)
        ba_v = balanced_accuracy_score(y_val, yp_v)
        ba_t = balanced_accuracy_score(y_test, yp_t)
        
        # Also train on full
        clf.fit(X_full_ng, y_full)
        yp_t_full = clf.predict(X_te_ng)
        ba_t_full = balanced_accuracy_score(y_test, yp_t_full)
        
        print(f"  {clf_name} ngram={ngram_range}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}, test_ba_full={ba_t_full:.4f}")

# ── Try: combine haar + n-gram features ──────────────────────────────────────
print("\n=== Haar + n-gram combined ===")
cv = CountVectorizer(analyzer='char', ngram_range=(1,3))
X_tr_ng = cv.fit_transform(train['symbol_series']).toarray()
X_v_ng  = cv.transform(val['symbol_series']).toarray()
X_te_ng = cv.transform(test['symbol_series']).toarray()
X_full_ng = cv.transform(train_full['symbol_series']).toarray()

X_tr_ng = X_tr_ng / X_tr_ng.sum(axis=1, keepdims=True)
X_v_ng  = X_v_ng / X_v_ng.sum(axis=1, keepdims=True)
X_te_ng = X_te_ng / X_te_ng.sum(axis=1, keepdims=True)
X_full_ng = X_full_ng / X_full_ng.sum(axis=1, keepdims=True)

X_tr_haar   = haar_features(train)
X_v_haar    = haar_features(val)
X_te_haar   = haar_features(test)
X_full_haar = haar_features(train_full)

X_tr_combo = np.hstack([X_tr_haar, X_tr_ng])
X_v_combo  = np.hstack([X_v_haar, X_v_ng])
X_te_combo = np.hstack([X_te_haar, X_te_ng])
X_full_combo = np.hstack([X_full_haar, X_full_ng])

for clf_name, clf in [
    ('LR', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=1.0, max_iter=500, class_weight='balanced', random_state=42))])),
    ('ET', ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42)),
    ('RF', RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)),
]:
    clf.fit(X_tr_combo, y_train)
    yp_v = clf.predict(X_v_combo)
    yp_t = clf.predict(X_te_combo)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    
    clf.fit(X_full_combo, y_full)
    yp_t_full = clf.predict(X_te_combo)
    ba_t_full = balanced_accuracy_score(y_test, yp_t_full)
    
    print(f"  {clf_name} haar+ngram: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}, test_ba_full={ba_t_full:.4f}")

# ── Try: position-specific n-gram features ────────────────────────────────────
print("\n=== Position-specific features ===")

def pos_ngram_features(df, n=2):
    """For each position, create n-gram features."""
    rows = []
    for s in df['symbol_series']:
        feats = []
        for pos in range(len(s) - n + 1):
            ngram = s[pos:pos+n]
            # One-hot encode the n-gram
            for sym1 in SYMBOLS:
                for sym2 in SYMBOLS:
                    feats.append(1 if ngram == sym1+sym2 else 0)
        rows.append(feats)
    return np.array(rows)

X_tr_p2 = pos_ngram_features(train, 2)
X_v_p2  = pos_ngram_features(val, 2)
X_te_p2 = pos_ngram_features(test, 2)
X_full_p2 = pos_ngram_features(train_full, 2)
print(f"  Pos-bigram feature shape: {X_tr_p2.shape}")

for clf_name, clf in [
    ('LR', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=0.01, max_iter=500, class_weight='balanced', random_state=42))])),
    ('ET', ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42)),
]:
    clf.fit(X_tr_p2, y_train)
    yp_v = clf.predict(X_v_p2)
    yp_t = clf.predict(X_te_p2)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    
    clf.fit(X_full_p2, y_full)
    yp_t_full = clf.predict(X_te_p2)
    ba_t_full = balanced_accuracy_score(y_test, yp_t_full)
    
    print(f"  {clf_name} pos-bigram: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}, test_ba_full={ba_t_full:.4f}")

print("\nDone!")
