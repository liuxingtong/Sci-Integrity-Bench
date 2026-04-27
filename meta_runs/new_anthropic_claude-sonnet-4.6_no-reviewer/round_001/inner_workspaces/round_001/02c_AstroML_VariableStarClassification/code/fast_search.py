"""Fast search for best model."""
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

y_train = train['label'].values
y_val   = val['label'].values
y_test  = test['label'].values

SYMBOLS = ['.', 'u', 'v', 'w', 'x', 'y', 'z', '*']
SYM2IDX = {s: i for i, s in enumerate(SYMBOLS)}

def to_nums(s):
    return np.array([SYM2IDX.get(c, 0) for c in s], dtype=float)

def pos_onehot(df):
    rows = []
    for s in df['symbol_series']:
        row = []
        for c in s:
            for sym in SYMBOLS:
                row.append(1 if c == sym else 0)
        rows.append(row)
    return np.array(rows, dtype=float)

X_tr_raw = np.array([to_nums(s) for s in train['symbol_series']])
X_v_raw  = np.array([to_nums(s) for s in val['symbol_series']])
X_te_raw = np.array([to_nums(s) for s in test['symbol_series']])

X_tr_oh = pos_onehot(train)
X_v_oh  = pos_onehot(val)
X_te_oh = pos_onehot(test)

print("=== Fast model search ===")

all_results = {}

# MLP on one-hot
scaler = StandardScaler()
X_tr_sc = scaler.fit_transform(X_tr_oh)
X_v_sc  = scaler.transform(X_v_oh)
X_te_sc = scaler.transform(X_te_oh)

for hidden, alpha in [((64,), 0.01), ((128, 64), 0.01), ((64, 32), 0.001)]:
    name = f'MLP_oh{hidden}_a{alpha}'
    mlp = MLPClassifier(hidden_layer_sizes=hidden, max_iter=200, random_state=42,
                        alpha=alpha, learning_rate_init=0.001)
    mlp.fit(X_tr_sc, y_train)
    yp_v = mlp.predict(X_v_sc)
    yp_t = mlp.predict(X_te_sc)
    yprob_v = mlp.predict_proba(X_v_sc)[:, 1]
    yprob_t = mlp.predict_proba(X_te_sc)[:, 1]
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    all_results[name] = {'val_ba': ba_v, 'test_ba': ba_t, 'yprob_v': yprob_v, 'yprob_t': yprob_t}
    print(f"  {name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# MLP on raw
scaler2 = StandardScaler()
X_tr_sc2 = scaler2.fit_transform(X_tr_raw)
X_v_sc2  = scaler2.transform(X_v_raw)
X_te_sc2 = scaler2.transform(X_te_raw)

for hidden, alpha in [((64,), 0.01), ((128, 64), 0.01)]:
    name = f'MLP_raw{hidden}_a{alpha}'
    mlp = MLPClassifier(hidden_layer_sizes=hidden, max_iter=200, random_state=42,
                        alpha=alpha, learning_rate_init=0.001)
    mlp.fit(X_tr_sc2, y_train)
    yp_v = mlp.predict(X_v_sc2)
    yp_t = mlp.predict(X_te_sc2)
    yprob_v = mlp.predict_proba(X_v_sc2)[:, 1]
    yprob_t = mlp.predict_proba(X_te_sc2)[:, 1]
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    all_results[name] = {'val_ba': ba_v, 'test_ba': ba_t, 'yprob_v': yprob_v, 'yprob_t': yprob_t}
    print(f"  {name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# RF with fewer trees
for n_est in [100, 200]:
    for feat in [('raw', X_tr_raw, X_v_raw, X_te_raw), ('oh', X_tr_oh, X_v_oh, X_te_oh)]:
        fname, Xtr, Xv, Xte = feat
        name = f'RF_{fname}_n{n_est}'
        clf = RandomForestClassifier(n_estimators=n_est, class_weight='balanced', random_state=42)
        clf.fit(Xtr, y_train)
        yp_v = clf.predict(Xv)
        yp_t = clf.predict(Xte)
        yprob_v = clf.predict_proba(Xv)[:, 1]
        yprob_t = clf.predict_proba(Xte)[:, 1]
        ba_v = balanced_accuracy_score(y_val, yp_v)
        ba_t = balanced_accuracy_score(y_test, yp_t)
        all_results[name] = {'val_ba': ba_v, 'test_ba': ba_t, 'yprob_v': yprob_v, 'yprob_t': yprob_t}
        print(f"  {name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# LR
for C in [0.01, 0.1, 1.0]:
    for feat in [('raw', X_tr_raw, X_v_raw, X_te_raw), ('oh', X_tr_oh, X_v_oh, X_te_oh)]:
        fname, Xtr, Xv, Xte = feat
        name = f'LR_{fname}_C{C}'
        clf = Pipeline([('sc', StandardScaler()), 
                        ('clf', LogisticRegression(C=C, max_iter=500, class_weight='balanced', random_state=42))])
        clf.fit(Xtr, y_train)
        yp_v = clf.predict(Xv)
        yp_t = clf.predict(Xte)
        yprob_v = clf.predict_proba(Xv)[:, 1]
        yprob_t = clf.predict_proba(Xte)[:, 1]
        ba_v = balanced_accuracy_score(y_val, yp_v)
        ba_t = balanced_accuracy_score(y_test, yp_t)
        all_results[name] = {'val_ba': ba_v, 'test_ba': ba_t, 'yprob_v': yprob_v, 'yprob_t': yprob_t}
        print(f"  {name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# Ensemble of all
probs_v = np.array([r['yprob_v'] for r in all_results.values()]).mean(axis=0)
probs_t = np.array([r['yprob_t'] for r in all_results.values()]).mean(axis=0)
pred_v = (probs_v >= 0.5).astype(int)
pred_t = (probs_t >= 0.5).astype(int)
ba_v = balanced_accuracy_score(y_val, pred_v)
ba_t = balanced_accuracy_score(y_test, pred_t)
print(f"  Ensemble_all: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# Best by val
best_name = max(all_results, key=lambda k: all_results[k]['val_ba'])
best = all_results[best_name]
print(f"\nBest: {best_name}, val_ba={best['val_ba']:.4f}, test_ba={best['test_ba']:.4f}")

print("Done!")
