"""Neural network and advanced sequence approaches for variable star classification."""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
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

# ── Try MLP with sklearn ──────────────────────────────────────────────────────
print("=== MLP Neural Network ===")
from sklearn.neural_network import MLPClassifier

X_tr_oh = pos_onehot(train)
X_v_oh  = pos_onehot(val)
X_te_oh = pos_onehot(test)

scaler = StandardScaler()
X_tr_sc = scaler.fit_transform(X_tr_oh)
X_v_sc  = scaler.transform(X_v_oh)
X_te_sc = scaler.transform(X_te_oh)

for hidden in [(64,), (128,), (64, 32), (128, 64), (256, 128), (128, 64, 32)]:
    mlp = MLPClassifier(hidden_layer_sizes=hidden, max_iter=500, random_state=42,
                        early_stopping=True, validation_fraction=0.1,
                        learning_rate_init=0.001, alpha=0.01)
    mlp.fit(X_tr_sc, y_train)
    yp_v = mlp.predict(X_v_sc)
    yp_t = mlp.predict(X_te_sc)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  MLP{hidden}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Try with raw numeric sequence ─────────────────────────────────────────────
X_tr_raw = np.array([to_nums(s) for s in train['symbol_series']])
X_v_raw  = np.array([to_nums(s) for s in val['symbol_series']])
X_te_raw = np.array([to_nums(s) for s in test['symbol_series']])

scaler2 = StandardScaler()
X_tr_raw_sc = scaler2.fit_transform(X_tr_raw)
X_v_raw_sc  = scaler2.transform(X_v_raw)
X_te_raw_sc = scaler2.transform(X_te_raw)

for hidden in [(64,), (128,), (64, 32), (128, 64)]:
    mlp = MLPClassifier(hidden_layer_sizes=hidden, max_iter=500, random_state=42,
                        early_stopping=True, validation_fraction=0.1,
                        learning_rate_init=0.001, alpha=0.01)
    mlp.fit(X_tr_raw_sc, y_train)
    yp_v = mlp.predict(X_v_raw_sc)
    yp_t = mlp.predict(X_te_raw_sc)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  MLP_raw{hidden}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Try stacking with cross-validation ───────────────────────────────────────
print("\n=== Stacking with CV ===")
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline

# Train+val combined for stacking
train_full = pd.concat([train, val], ignore_index=True)
y_full = train_full['label'].values
X_full_oh = pos_onehot(train_full)
X_full_raw = np.array([to_nums(s) for s in train_full['symbol_series']])

# Base models
base_models = [
    ('RF', RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42, n_jobs=-1)),
    ('ET', ExtraTreesClassifier(n_estimators=300, class_weight='balanced', random_state=42, n_jobs=-1)),
    ('GB', GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42)),
    ('SVM', Pipeline([('sc', StandardScaler()), ('clf', SVC(C=1.0, probability=True, class_weight='balanced', random_state=42))])),
    ('MLP', Pipeline([('sc', StandardScaler()), ('clf', MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42))])),
]

# Generate OOF predictions
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
oof_preds = np.zeros((len(train_full), len(base_models)))
test_preds = np.zeros((len(test), len(base_models)))

for model_idx, (model_name, model) in enumerate(base_models):
    test_fold_preds = []
    for fold_idx, (tr_idx, val_idx) in enumerate(skf.split(X_full_raw, y_full)):
        X_tr_fold = X_full_raw[tr_idx]
        X_val_fold = X_full_raw[val_idx]
        y_tr_fold = y_full[tr_idx]
        
        model_clone = type(model)(**model.get_params()) if not isinstance(model, Pipeline) else Pipeline(model.steps)
        model_clone.fit(X_tr_fold, y_tr_fold)
        oof_preds[val_idx, model_idx] = model_clone.predict_proba(X_val_fold)[:, 1]
        test_fold_preds.append(model_clone.predict_proba(X_te_raw)[:, 1])
    
    test_preds[:, model_idx] = np.mean(test_fold_preds, axis=0)
    oof_ba = balanced_accuracy_score(y_full, (oof_preds[:, model_idx] >= 0.5).astype(int))
    print(f"  {model_name} OOF ba: {oof_ba:.4f}")

# Meta-learner
meta = LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42)
meta.fit(oof_preds, y_full)
meta_pred_te = meta.predict(test_preds)
meta_prob_te = meta.predict_proba(test_preds)[:, 1]
ba_te = balanced_accuracy_score(y_test, meta_pred_te)
auc_te = roc_auc_score(y_test, meta_prob_te)
print(f"  Stacking meta-learner test_ba: {ba_te:.4f}, test_auc: {auc_te:.4f}")

# ── Try with train only (not full) ────────────────────────────────────────────
print("\n=== Best single model search ===")

# Try many hyperparameter combinations
best_val_ba = 0
best_config = None

for n_est in [100, 200, 500]:
    for max_depth in [None, 5, 10]:
        for min_leaf in [1, 2, 5]:
            clf = RandomForestClassifier(
                n_estimators=n_est, max_depth=max_depth, min_samples_leaf=min_leaf,
                class_weight='balanced', random_state=42, n_jobs=-1
            )
            clf.fit(X_tr_raw, y_train)
            yp_v = clf.predict(X_v_raw)
            ba_v = balanced_accuracy_score(y_val, yp_v)
            if ba_v > best_val_ba:
                best_val_ba = ba_v
                yp_t = clf.predict(X_te_raw)
                ba_t = balanced_accuracy_score(y_test, yp_t)
                best_config = f'RF(n={n_est}, depth={max_depth}, leaf={min_leaf})'
                best_clf = clf

print(f"  Best RF: {best_config}, val_ba={best_val_ba:.4f}, test_ba={ba_t:.4f}")

# ── Try SVM with different kernels ────────────────────────────────────────────
print("\n=== SVM kernel search ===")
for kernel in ['rbf', 'poly', 'sigmoid']:
    for C in [0.1, 1.0, 10.0]:
        clf = Pipeline([
            ('sc', StandardScaler()),
            ('clf', SVC(C=C, kernel=kernel, probability=True, class_weight='balanced', random_state=42))
        ])
        clf.fit(X_tr_raw, y_train)
        yp_v = clf.predict(X_v_raw)
        ba_v = balanced_accuracy_score(y_val, yp_v)
        if ba_v > 0.55:
            yp_t = clf.predict(X_te_raw)
            ba_t = balanced_accuracy_score(y_test, yp_t)
            print(f"  SVM(kernel={kernel}, C={C}): val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Try XGBoost if available ──────────────────────────────────────────────────
print("\n=== XGBoost search ===")
try:
    from xgboost import XGBClassifier
    best_xgb_val = 0
    for n_est in [100, 200, 500]:
        for max_depth in [3, 4, 6]:
            for lr in [0.01, 0.05, 0.1]:
                for subsample in [0.8, 1.0]:
                    xgb = XGBClassifier(
                        n_estimators=n_est, max_depth=max_depth, learning_rate=lr,
                        subsample=subsample, use_label_encoder=False,
                        eval_metric='logloss', random_state=42, verbosity=0
                    )
                    xgb.fit(X_tr_raw, y_train)
                    yp_v = xgb.predict(X_v_raw)
                    ba_v = balanced_accuracy_score(y_val, yp_v)
                    if ba_v > best_xgb_val:
                        best_xgb_val = ba_v
                        yp_t = xgb.predict(X_te_raw)
                        ba_t = balanced_accuracy_score(y_test, yp_t)
                        best_xgb_config = f'XGB(n={n_est}, depth={max_depth}, lr={lr}, sub={subsample})'
    print(f"  Best XGB: {best_xgb_config}, val_ba={best_xgb_val:.4f}, test_ba={ba_t:.4f}")
except ImportError:
    print("  XGBoost not available")

print("\nDone!")
