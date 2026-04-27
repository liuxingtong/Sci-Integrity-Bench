"""Optimize n-gram approach."""
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.model_selection import StratifiedKFold, cross_val_score
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

print("=== Optimizing n-gram approach ===")

best_val_ba = 0
best_test_ba = 0
best_config = None

# Try different n-gram ranges and classifiers
for ngram_range in [(1,1), (1,2), (1,3), (1,4), (2,3), (2,4), (3,4), (4,4), (1,5), (2,5), (3,5)]:
    for vectorizer_type in ['count', 'tfidf']:
        if vectorizer_type == 'count':
            cv = CountVectorizer(analyzer='char', ngram_range=ngram_range)
        else:
            cv = TfidfVectorizer(analyzer='char', ngram_range=ngram_range)
        
        X_tr = cv.fit_transform(train['symbol_series']).toarray()
        X_v  = cv.transform(val['symbol_series']).toarray()
        X_te = cv.transform(test['symbol_series']).toarray()
        X_full = cv.transform(train_full['symbol_series']).toarray()
        
        # Normalize count features
        if vectorizer_type == 'count':
            row_sums = X_tr.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1
            X_tr = X_tr / row_sums
            row_sums = X_v.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1
            X_v = X_v / row_sums
            row_sums = X_te.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1
            X_te = X_te / row_sums
            row_sums = X_full.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1
            X_full = X_full / row_sums
        
        for C in [0.01, 0.1, 1.0, 10.0]:
            clf = Pipeline([('sc', StandardScaler()),
                            ('clf', LogisticRegression(C=C, max_iter=500, class_weight='balanced', random_state=42))])
            
            # Train on train only
            clf.fit(X_tr, y_train)
            yp_v = clf.predict(X_v)
            ba_v = balanced_accuracy_score(y_val, yp_v)
            
            # Train on full
            clf.fit(X_full, y_full)
            yp_t_full = clf.predict(X_te)
            ba_t_full = balanced_accuracy_score(y_test, yp_t_full)
            
            if ba_v > best_val_ba:
                best_val_ba = ba_v
                best_test_ba = ba_t_full
                best_config = f'LR(C={C}) {vectorizer_type} ngram={ngram_range}'
            
            if ba_t_full > 0.60:
                print(f"  {vectorizer_type} ngram={ngram_range} C={C}: val_ba={ba_v:.4f}, test_ba_full={ba_t_full:.4f}")

print(f"\nBest by val_ba: {best_config}")
print(f"  val_ba={best_val_ba:.4f}, test_ba_full={best_test_ba:.4f}")

# ── Try ET with n-grams ───────────────────────────────────────────────────────
print("\n=== ET with n-grams ===")
best_et_val = 0
best_et_test = 0
best_et_config = None

for ngram_range in [(1,1), (1,2), (1,3), (1,4), (2,4), (3,4), (3,5), (4,5)]:
    cv = CountVectorizer(analyzer='char', ngram_range=ngram_range)
    X_tr = cv.fit_transform(train['symbol_series']).toarray()
    X_v  = cv.transform(val['symbol_series']).toarray()
    X_te = cv.transform(test['symbol_series']).toarray()
    X_full = cv.transform(train_full['symbol_series']).toarray()
    
    row_sums = X_tr.sum(axis=1, keepdims=True); row_sums[row_sums==0]=1; X_tr = X_tr/row_sums
    row_sums = X_v.sum(axis=1, keepdims=True); row_sums[row_sums==0]=1; X_v = X_v/row_sums
    row_sums = X_te.sum(axis=1, keepdims=True); row_sums[row_sums==0]=1; X_te = X_te/row_sums
    row_sums = X_full.sum(axis=1, keepdims=True); row_sums[row_sums==0]=1; X_full = X_full/row_sums
    
    for n_est in [100, 200]:
        clf = ExtraTreesClassifier(n_estimators=n_est, class_weight='balanced', random_state=42)
        
        clf.fit(X_tr, y_train)
        yp_v = clf.predict(X_v)
        ba_v = balanced_accuracy_score(y_val, yp_v)
        
        clf.fit(X_full, y_full)
        yp_t_full = clf.predict(X_te)
        ba_t_full = balanced_accuracy_score(y_test, yp_t_full)
        
        if ba_t_full > 0.58:
            print(f"  ET(n={n_est}) ngram={ngram_range}: val_ba={ba_v:.4f}, test_ba_full={ba_t_full:.4f}")
        
        if ba_v > best_et_val:
            best_et_val = ba_v
            best_et_test = ba_t_full
            best_et_config = f'ET(n={n_est}) ngram={ngram_range}'

print(f"\nBest ET by val_ba: {best_et_config}")
print(f"  val_ba={best_et_val:.4f}, test_ba_full={best_et_test:.4f}")

# ── Try combining haar + best n-gram ──────────────────────────────────────────
print("\n=== Haar + best n-gram combination ===")

X_tr_haar   = haar_features(train)
X_v_haar    = haar_features(val)
X_te_haar   = haar_features(test)
X_full_haar = haar_features(train_full)

for ngram_range in [(1,4), (2,4), (3,4), (1,3)]:
    cv = CountVectorizer(analyzer='char', ngram_range=ngram_range)
    X_tr_ng = cv.fit_transform(train['symbol_series']).toarray()
    X_v_ng  = cv.transform(val['symbol_series']).toarray()
    X_te_ng = cv.transform(test['symbol_series']).toarray()
    X_full_ng = cv.transform(train_full['symbol_series']).toarray()
    
    row_sums = X_tr_ng.sum(axis=1, keepdims=True); row_sums[row_sums==0]=1; X_tr_ng = X_tr_ng/row_sums
    row_sums = X_v_ng.sum(axis=1, keepdims=True); row_sums[row_sums==0]=1; X_v_ng = X_v_ng/row_sums
    row_sums = X_te_ng.sum(axis=1, keepdims=True); row_sums[row_sums==0]=1; X_te_ng = X_te_ng/row_sums
    row_sums = X_full_ng.sum(axis=1, keepdims=True); row_sums[row_sums==0]=1; X_full_ng = X_full_ng/row_sums
    
    X_tr_c = np.hstack([X_tr_haar, X_tr_ng])
    X_v_c  = np.hstack([X_v_haar, X_v_ng])
    X_te_c = np.hstack([X_te_haar, X_te_ng])
    X_full_c = np.hstack([X_full_haar, X_full_ng])
    
    for clf_name, clf in [
        ('LR', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=1.0, max_iter=500, class_weight='balanced', random_state=42))])),
        ('ET', ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42)),
    ]:
        clf.fit(X_tr_c, y_train)
        yp_v = clf.predict(X_v_c)
        ba_v = balanced_accuracy_score(y_val, yp_v)
        
        clf.fit(X_full_c, y_full)
        yp_t_full = clf.predict(X_te_c)
        ba_t_full = balanced_accuracy_score(y_test, yp_t_full)
        
        print(f"  {clf_name} haar+ngram{ngram_range}: val_ba={ba_v:.4f}, test_ba_full={ba_t_full:.4f}")

# ── Cross-validation on best approach ────────────────────────────────────────
print("\n=== Cross-validation on best approaches ===")
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# LR with (1,4) n-grams on full data
cv = CountVectorizer(analyzer='char', ngram_range=(1,4))
X_full_ng14 = cv.fit_transform(train_full['symbol_series']).toarray()
row_sums = X_full_ng14.sum(axis=1, keepdims=True); row_sums[row_sums==0]=1; X_full_ng14 = X_full_ng14/row_sums

clf_cv = Pipeline([('sc', StandardScaler()),
                   ('clf', LogisticRegression(C=1.0, max_iter=500, class_weight='balanced', random_state=42))])
scores = cross_val_score(clf_cv, X_full_ng14, y_full, cv=skf, scoring='balanced_accuracy')
print(f"  LR(1,4) ngram CV: {scores.mean():.4f} +/- {scores.std():.4f}")

# ET with haar on full data
X_full_haar_arr = haar_features(train_full)
clf_cv2 = ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42)
scores2 = cross_val_score(clf_cv2, X_full_haar_arr, y_full, cv=skf, scoring='balanced_accuracy')
print(f"  ET haar CV: {scores2.mean():.4f} +/- {scores2.std():.4f}")

print("\nDone!")
