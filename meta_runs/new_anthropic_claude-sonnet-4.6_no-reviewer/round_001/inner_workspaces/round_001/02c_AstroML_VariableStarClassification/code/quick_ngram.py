"""Quick n-gram optimization."""
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
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

def get_ngram_features(train_df, val_df, test_df, full_df, ngram_range):
    cv = CountVectorizer(analyzer='char', ngram_range=ngram_range)
    X_tr = cv.fit_transform(train_df['symbol_series']).toarray().astype(float)
    X_v  = cv.transform(val_df['symbol_series']).toarray().astype(float)
    X_te = cv.transform(test_df['symbol_series']).toarray().astype(float)
    X_full = cv.transform(full_df['symbol_series']).toarray().astype(float)
    for X in [X_tr, X_v, X_te, X_full]:
        rs = X.sum(axis=1, keepdims=True); rs[rs==0]=1; X /= rs
    return X_tr, X_v, X_te, X_full

print("=== Key n-gram experiments ===")

# Focus on the most promising: LR with (1,4) n-grams
for ngram_range in [(1,4), (2,4), (3,4), (1,3), (1,2), (1,1)]:
    X_tr, X_v, X_te, X_full = get_ngram_features(train, val, test, train_full, ngram_range)
    
    for C in [0.1, 1.0, 10.0]:
        clf = Pipeline([('sc', StandardScaler()),
                        ('clf', LogisticRegression(C=C, max_iter=300, class_weight='balanced', random_state=42))])
        clf.fit(X_tr, y_train)
        ba_v = balanced_accuracy_score(y_val, clf.predict(X_v))
        
        clf.fit(X_full, y_full)
        ba_t_full = balanced_accuracy_score(y_test, clf.predict(X_te))
        
        print(f"  LR(C={C}) ngram={ngram_range}: val_ba={ba_v:.4f}, test_ba_full={ba_t_full:.4f}")

print("\n=== Haar features ===")
X_tr_haar   = haar_features(train)
X_v_haar    = haar_features(val)
X_te_haar   = haar_features(test)
X_full_haar = haar_features(train_full)

for n_est in [100, 200]:
    clf = ExtraTreesClassifier(n_estimators=n_est, class_weight='balanced', random_state=42)
    clf.fit(X_tr_haar, y_train)
    ba_v = balanced_accuracy_score(y_val, clf.predict(X_v_haar))
    clf.fit(X_full_haar, y_full)
    ba_t_full = balanced_accuracy_score(y_test, clf.predict(X_te_haar))
    print(f"  ET(n={n_est}) haar: val_ba={ba_v:.4f}, test_ba_full={ba_t_full:.4f}")

print("\n=== CV on best approaches ===")
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# LR with (1,4) n-grams
X_tr14, X_v14, X_te14, X_full14 = get_ngram_features(train, val, test, train_full, (1,4))
clf_cv = Pipeline([('sc', StandardScaler()),
                   ('clf', LogisticRegression(C=1.0, max_iter=300, class_weight='balanced', random_state=42))])
scores = cross_val_score(clf_cv, X_full14, y_full, cv=skf, scoring='balanced_accuracy')
print(f"  LR(1,4) ngram CV: {scores.mean():.4f} +/- {scores.std():.4f}")

# ET haar
clf_cv2 = ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42)
scores2 = cross_val_score(clf_cv2, X_full_haar, y_full, cv=skf, scoring='balanced_accuracy')
print(f"  ET haar CV: {scores2.mean():.4f} +/- {scores2.std():.4f}")

# LR raw
X_full_raw = np.array([to_nums(s) for s in train_full['symbol_series']])
clf_cv3 = Pipeline([('sc', StandardScaler()),
                    ('clf', LogisticRegression(C=0.1, max_iter=300, class_weight='balanced', random_state=42))])
scores3 = cross_val_score(clf_cv3, X_full_raw, y_full, cv=skf, scoring='balanced_accuracy')
print(f"  LR raw CV: {scores3.mean():.4f} +/- {scores3.std():.4f}")

print("\nDone!")
