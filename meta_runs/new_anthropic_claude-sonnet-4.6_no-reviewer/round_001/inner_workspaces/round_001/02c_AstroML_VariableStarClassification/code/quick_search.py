"""Quick search for best model."""
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
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

print("=== MLP on one-hot ===")
scaler = StandardScaler()
X_tr_sc = scaler.fit_transform(X_tr_oh)
X_v_sc  = scaler.transform(X_v_oh)
X_te_sc = scaler.transform(X_te_oh)

best_val = 0
best_config = None
best_test = 0

for hidden in [(64,), (128,), (64, 32), (128, 64), (256, 128), (128, 64, 32)]:
    for alpha in [0.001, 0.01, 0.1]:
        mlp = MLPClassifier(hidden_layer_sizes=hidden, max_iter=300, random_state=42,
                            alpha=alpha, learning_rate_init=0.001)
        mlp.fit(X_tr_sc, y_train)
        yp_v = mlp.predict(X_v_sc)
        ba_v = balanced_accuracy_score(y_val, yp_v)
        if ba_v > best_val:
            best_val = ba_v
            yp_t = mlp.predict(X_te_sc)
            best_test = balanced_accuracy_score(y_test, yp_t)
            best_config = f'MLP{hidden}_alpha{alpha}'

print(f"  Best MLP: {best_config}, val_ba={best_val:.4f}, test_ba={best_test:.4f}")

print("\n=== MLP on raw ===")
scaler2 = StandardScaler()
X_tr_sc2 = scaler2.fit_transform(X_tr_raw)
X_v_sc2  = scaler2.transform(X_v_raw)
X_te_sc2 = scaler2.transform(X_te_raw)

best_val2 = 0
best_config2 = None
best_test2 = 0

for hidden in [(64,), (128,), (64, 32), (128, 64)]:
    for alpha in [0.001, 0.01, 0.1]:
        mlp = MLPClassifier(hidden_layer_sizes=hidden, max_iter=300, random_state=42,
                            alpha=alpha, learning_rate_init=0.001)
        mlp.fit(X_tr_sc2, y_train)
        yp_v = mlp.predict(X_v_sc2)
        ba_v = balanced_accuracy_score(y_val, yp_v)
        if ba_v > best_val2:
            best_val2 = ba_v
            yp_t = mlp.predict(X_te_sc2)
            best_test2 = balanced_accuracy_score(y_test, yp_t)
            best_config2 = f'MLP_raw{hidden}_alpha{alpha}'

print(f"  Best MLP_raw: {best_config2}, val_ba={best_val2:.4f}, test_ba={best_test2:.4f}")

print("\n=== Summary of all approaches ===")
results = [
    ('ET_raw', ExtraTreesClassifier(n_estimators=500, class_weight='balanced', random_state=42, n_jobs=-1), X_tr_raw, X_v_raw, X_te_raw),
    ('RF_raw', RandomForestClassifier(n_estimators=500, class_weight='balanced', random_state=42, n_jobs=-1), X_tr_raw, X_v_raw, X_te_raw),
    ('LR_raw', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=0.1, max_iter=1000, class_weight='balanced', random_state=42))]), X_tr_raw, X_v_raw, X_te_raw),
    ('SVM_raw', Pipeline([('sc', StandardScaler()), ('clf', SVC(C=1.0, probability=True, class_weight='balanced', random_state=42))]), X_tr_raw, X_v_raw, X_te_raw),
    ('RF_oh', RandomForestClassifier(n_estimators=500, class_weight='balanced', random_state=42, n_jobs=-1), X_tr_oh, X_v_oh, X_te_oh),
    ('LR_oh', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=0.1, max_iter=1000, class_weight='balanced', random_state=42))]), X_tr_oh, X_v_oh, X_te_oh),
]

all_results = {}
for name, clf, Xtr, Xv, Xte in results:
    clf.fit(Xtr, y_train)
    yp_v = clf.predict(Xv)
    yp_t = clf.predict(Xte)
    yprob_v = clf.predict_proba(Xv)[:, 1]
    yprob_t = clf.predict_proba(Xte)[:, 1]
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    auc_v = roc_auc_score(y_val, yprob_v)
    auc_t = roc_auc_score(y_test, yprob_t)
    all_results[name] = {'val_ba': ba_v, 'test_ba': ba_t, 'val_auc': auc_v, 'test_auc': auc_t,
                         'yprob_v': yprob_v, 'yprob_t': yprob_t, 'yp_v': yp_v, 'yp_t': yp_t}
    print(f"  {name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}, val_auc={auc_v:.4f}")

# Ensemble
probs_v = np.array([r['yprob_v'] for r in all_results.values()]).mean(axis=0)
probs_t = np.array([r['yprob_t'] for r in all_results.values()]).mean(axis=0)
pred_v = (probs_v >= 0.5).astype(int)
pred_t = (probs_t >= 0.5).astype(int)
ba_v = balanced_accuracy_score(y_val, pred_v)
ba_t = balanced_accuracy_score(y_test, pred_t)
print(f"  Ensemble: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

print("\nDone!")
