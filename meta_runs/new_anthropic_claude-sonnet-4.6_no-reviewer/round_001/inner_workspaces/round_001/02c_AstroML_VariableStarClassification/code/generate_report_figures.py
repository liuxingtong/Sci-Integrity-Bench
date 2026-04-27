"""Generate all figures for the final report."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.metrics import (
    balanced_accuracy_score, accuracy_score, roc_auc_score, f1_score,
    confusion_matrix, classification_report, roc_curve
)
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.feature_extraction.text import CountVectorizer
from scipy import stats
from scipy.stats import chi2_contingency
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# ── Load data ────────────────────────────────────────────────────────────────
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

# ── Prepare features ─────────────────────────────────────────────────────────
print("Preparing features...")
X_tr_raw   = np.array([to_nums(s) for s in train['symbol_series']])
X_v_raw    = np.array([to_nums(s) for s in val['symbol_series']])
X_te_raw   = np.array([to_nums(s) for s in test['symbol_series']])
X_full_raw = np.array([to_nums(s) for s in train_full['symbol_series']])

X_tr_haar   = haar_features(train)
X_v_haar    = haar_features(val)
X_te_haar   = haar_features(test)
X_full_haar = haar_features(train_full)

X_tr_ng, X_v_ng, X_te_ng, X_full_ng = get_ngram_features(train, val, test, train_full, (1,4))

# ── Train models ─────────────────────────────────────────────────────────────
print("Training models...")

# Model 1: LR on raw (train only)
lr_raw = Pipeline([('sc', StandardScaler()),
                   ('clf', LogisticRegression(C=0.1, max_iter=300, class_weight='balanced', random_state=42))])
lr_raw.fit(X_tr_raw, y_train)
yp_v_lr = lr_raw.predict(X_v_raw)
yp_t_lr = lr_raw.predict(X_te_raw)
yprob_v_lr = lr_raw.predict_proba(X_v_raw)[:, 1]
yprob_t_lr = lr_raw.predict_proba(X_te_raw)[:, 1]

# Model 2: ET on Haar (train only)
et_haar = ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42)
et_haar.fit(X_tr_haar, y_train)
yp_v_et = et_haar.predict(X_v_haar)
yp_t_et = et_haar.predict(X_te_haar)
yprob_v_et = et_haar.predict_proba(X_v_haar)[:, 1]
yprob_t_et = et_haar.predict_proba(X_te_haar)[:, 1]

# Model 3: RF on Haar (train only)
rf_haar = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
rf_haar.fit(X_tr_haar, y_train)
yp_v_rf = rf_haar.predict(X_v_haar)
yp_t_rf = rf_haar.predict(X_te_haar)
yprob_v_rf = rf_haar.predict_proba(X_v_haar)[:, 1]
yprob_t_rf = rf_haar.predict_proba(X_te_haar)[:, 1]

# Model 4: LR on n-gram (train only)
lr_ng = Pipeline([('sc', StandardScaler()),
                  ('clf', LogisticRegression(C=1.0, max_iter=300, class_weight='balanced', random_state=42))])
lr_ng.fit(X_tr_ng, y_train)
yp_v_ng = lr_ng.predict(X_v_ng)
yp_t_ng = lr_ng.predict(X_te_ng)
yprob_v_ng = lr_ng.predict_proba(X_v_ng)[:, 1]
yprob_t_ng = lr_ng.predict_proba(X_te_ng)[:, 1]

# Best model: ET on Haar (train+val)
best_model = ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42)
best_model.fit(X_full_haar, y_full)
best_pred = best_model.predict(X_te_haar)
best_prob = best_model.predict_proba(X_te_haar)[:, 1]
best_ba = balanced_accuracy_score(y_test, best_pred)
best_auc = roc_auc_score(y_test, best_prob)
best_f1 = f1_score(y_test, best_pred)
best_acc = accuracy_score(y_test, best_pred)

print(f"Best model (ET_haar, train+val): test_ba={best_ba:.4f}, test_auc={best_auc:.4f}")

# Cross-validation
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_et = cross_val_score(ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42),
                        X_full_haar, y_full, cv=skf, scoring='balanced_accuracy')
cv_lr = cross_val_score(Pipeline([('sc', StandardScaler()),
                                   ('clf', LogisticRegression(C=0.1, max_iter=300, class_weight='balanced', random_state=42))]),
                        X_full_raw, y_full, cv=skf, scoring='balanced_accuracy')
cv_rf = cross_val_score(RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42),
                        X_full_haar, y_full, cv=skf, scoring='balanced_accuracy')
cv_ng = cross_val_score(Pipeline([('sc', StandardScaler()),
                                   ('clf', LogisticRegression(C=1.0, max_iter=300, class_weight='balanced', random_state=42))]),
                        X_full_ng, y_full, cv=skf, scoring='balanced_accuracy')

print(f"CV ET_haar: {cv_et.mean():.4f} +/- {cv_et.std():.4f}")
print(f"CV LR_raw: {cv_lr.mean():.4f} +/- {cv_lr.std():.4f}")
print(f"CV RF_haar: {cv_rf.mean():.4f} +/- {cv_rf.std():.4f}")
print(f"CV LR_ng14: {cv_ng.mean():.4f} +/- {cv_ng.std():.4f}")

# ── Save key metrics ──────────────────────────────────────────────────────────
metrics = {
    'best_model': 'ET_haar (train+val)',
    'test_ba': best_ba,
    'test_auc': best_auc,
    'test_f1': best_f1,
    'test_acc': best_acc,
    'baseline': 0.78,
    'cv_et_mean': cv_et.mean(),
    'cv_et_std': cv_et.std(),
    'cv_lr_mean': cv_lr.mean(),
    'cv_lr_std': cv_lr.std(),
}
with open('outputs/final_metrics.txt', 'w') as f:
    for k, v in metrics.items():
        f.write(f"{k}: {v}\n")

# ── Figure 1: Data Overview ───────────────────────────────────────────────────
print("\nGenerating Figure 1: Data Overview...")
fig = plt.figure(figsize=(16, 10))
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)
fig.suptitle('Variable Star Classification — Data Overview', fontsize=15, fontweight='bold', y=1.01)

# 1a: Label distribution
ax = fig.add_subplot(gs[0, 0])
for i, (split_name, df, color) in enumerate([('Train', train, '#2196F3'), ('Val', val, '#FF9800'), ('Test', test, '#4CAF50')]):
    counts = df['label'].value_counts().sort_index()
    x = np.array([0, 1])
    offset = (i - 1) * 0.27
    bars = ax.bar(x + offset, counts.values, width=0.24, label=split_name, color=color, alpha=0.85, edgecolor='black', linewidth=0.5)
ax.set_title('Label Distribution by Split', fontweight='bold')
ax.set_ylabel('Count')
ax.set_xticks([0, 1])
ax.set_xticklabels(['Non-Variable', 'Variable'])
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

# 1b: Example series
ax = fig.add_subplot(gs[0, 1])
example_var = train[train['label']==1]['symbol_series'].iloc[0]
example_nonvar = train[train['label']==0]['symbol_series'].iloc[0]
nums_var = to_nums(example_var)
nums_nonvar = to_nums(example_nonvar)
ax.plot(nums_var, 'r-o', markersize=3, label='Variable', alpha=0.8, linewidth=1.5)
ax.plot(nums_nonvar, 'b-s', markersize=3, label='Non-Variable', alpha=0.8, linewidth=1.5)
ax.set_title('Example Symbol Series', fontweight='bold')
ax.set_xlabel('Time Step')
ax.set_ylabel('Symbol Value')
ax.set_yticks(range(8))
ax.set_yticklabels(SYMBOLS)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# 1c: Symbol frequency by class
ax = fig.add_subplot(gs[0, 2])
var_series = ''.join(train[train['label']==1]['symbol_series'].tolist())
non_series = ''.join(train[train['label']==0]['symbol_series'].tolist())
var_freq = [var_series.count(s) / len(var_series) for s in SYMBOLS]
non_freq = [non_series.count(s) / len(non_series) for s in SYMBOLS]
x = np.arange(len(SYMBOLS))
width = 0.35
ax.bar(x - width/2, non_freq, width, label='Non-Variable', color='#2196F3', alpha=0.8, edgecolor='black', linewidth=0.5)
ax.bar(x + width/2, var_freq, width, label='Variable', color='#F44336', alpha=0.8, edgecolor='black', linewidth=0.5)
ax.set_title('Symbol Frequency by Class', fontweight='bold')
ax.set_xlabel('Symbol')
ax.set_ylabel('Frequency')
ax.set_xticks(x)
ax.set_xticklabels(SYMBOLS)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

# 1d: Position-wise mean difference
ax = fig.add_subplot(gs[1, 0])
var_pos_means = []
non_pos_means = []
for pos in range(40):
    var_vals = [SYM2IDX.get(s[pos], 0) for s in train[train['label']==1]['symbol_series']]
    non_vals = [SYM2IDX.get(s[pos], 0) for s in train[train['label']==0]['symbol_series']]
    var_pos_means.append(np.mean(var_vals))
    non_pos_means.append(np.mean(non_vals))
diffs_pos = np.array(var_pos_means) - np.array(non_pos_means)
colors_pos = ['#F44336' if d > 0 else '#2196F3' for d in diffs_pos]
ax.bar(range(40), diffs_pos, color=colors_pos, alpha=0.8)
ax.axhline(0, color='black', linewidth=0.8)
ax.set_title('Position-wise Mean Difference (Var − Non-Var)', fontweight='bold')
ax.set_xlabel('Position in Series')
ax.set_ylabel('Mean Difference')
ax.grid(True, alpha=0.3, axis='y')

# 1e: Chi-squared statistics per position
ax = fig.add_subplot(gs[1, 1])
chi2_stats = []
for pos in range(40):
    var_chars = Counter([s[pos] for s in train[train['label']==1]['symbol_series']])
    non_chars = Counter([s[pos] for s in train[train['label']==0]['symbol_series']])
    contingency = np.array([[var_chars.get(sym, 0) for sym in SYMBOLS],
                             [non_chars.get(sym, 0) for sym in SYMBOLS]])
    chi2, p, dof, expected = chi2_contingency(contingency)
    chi2_stats.append(chi2)
colors_chi2 = ['#F44336' if c > 14.07 else '#2196F3' for c in chi2_stats]
ax.bar(range(40), chi2_stats, color=colors_chi2, alpha=0.8)
ax.axhline(14.07, color='red', linestyle='--', linewidth=1.5, label='p=0.05 threshold')
ax.set_title('Position-wise Chi-squared Statistics', fontweight='bold')
ax.set_xlabel('Position in Series')
ax.set_ylabel('Chi-squared')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

# 1f: Haar wavelet features distribution
ax = fig.add_subplot(gs[1, 2])
for label, color, name in [(0, '#2196F3', 'Non-Variable'), (1, '#F44336', 'Variable')]:
    mask = y_train == label
    ax.hist(X_tr_haar[mask, 1], bins=20, alpha=0.6, color=color, label=name,
            edgecolor='black', linewidth=0.3, density=True)
ax.set_title('Haar L1 Detail Std by Class', fontweight='bold')
ax.set_xlabel('Haar Wavelet Detail Std')
ax.set_ylabel('Density')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

plt.savefig('report/images/fig1_data_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1_data_overview.png")

# ── Figure 2: Model Comparison ────────────────────────────────────────────────
print("Generating Figure 2: Model Comparison...")
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('Model Performance Comparison', fontsize=14, fontweight='bold')

# Model results
model_data = [
    ('LR\n(Raw)', balanced_accuracy_score(y_val, yp_v_lr), balanced_accuracy_score(y_test, yp_t_lr),
     roc_auc_score(y_val, yprob_v_lr), roc_auc_score(y_test, yprob_t_lr)),
    ('ET\n(Haar)', balanced_accuracy_score(y_val, yp_v_et), balanced_accuracy_score(y_test, yp_t_et),
     roc_auc_score(y_val, yprob_v_et), roc_auc_score(y_test, yprob_t_et)),
    ('RF\n(Haar)', balanced_accuracy_score(y_val, yp_v_rf), balanced_accuracy_score(y_test, yp_t_rf),
     roc_auc_score(y_val, yprob_v_rf), roc_auc_score(y_test, yprob_t_rf)),
    ('LR\n(N-gram)', balanced_accuracy_score(y_val, yp_v_ng), balanced_accuracy_score(y_test, yp_t_ng),
     roc_auc_score(y_val, yprob_v_ng), roc_auc_score(y_test, yprob_t_ng)),
    ('ET\n(Haar+Full)', None, best_ba, None, best_auc),
]

# 2a: Balanced accuracy
ax = axes[0]
names = [m[0] for m in model_data]
val_bas = [m[1] for m in model_data]
test_bas = [m[2] for m in model_data]
x = np.arange(len(names))
width = 0.35
bars1 = ax.bar(x - width/2, [v if v is not None else 0 for v in val_bas], width,
               label='Validation', color='#2196F3', alpha=0.8, edgecolor='black', linewidth=0.5)
bars2 = ax.bar(x + width/2, test_bas, width,
               label='Test', color='#F44336', alpha=0.8, edgecolor='black', linewidth=0.5)
ax.axhline(0.78, color='green', linestyle='--', linewidth=2, label='Baseline (0.78)')
ax.axhline(0.5, color='gray', linestyle=':', linewidth=1.5, label='Random (0.50)')
for i, (v, t) in enumerate(zip(val_bas, test_bas)):
    if v is not None:
        ax.text(i - width/2, v + 0.01, f'{v:.2f}', ha='center', va='bottom', fontsize=7)
    ax.text(i + width/2, t + 0.01, f'{t:.2f}', ha='center', va='bottom', fontsize=7)
ax.set_title('Balanced Accuracy', fontweight='bold')
ax.set_ylabel('Balanced Accuracy')
ax.set_xticks(x)
ax.set_xticklabels(names, fontsize=9)
ax.set_ylim(0.3, 0.85)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

# 2b: AUC
ax = axes[1]
val_aucs = [m[3] for m in model_data]
test_aucs = [m[4] for m in model_data]
bars1 = ax.bar(x - width/2, [v if v is not None else 0 for v in val_aucs], width,
               label='Validation', color='#2196F3', alpha=0.8, edgecolor='black', linewidth=0.5)
bars2 = ax.bar(x + width/2, test_aucs, width,
               label='Test', color='#F44336', alpha=0.8, edgecolor='black', linewidth=0.5)
ax.axhline(0.5, color='gray', linestyle=':', linewidth=1.5, label='Random (0.50)')
ax.set_title('ROC-AUC', fontweight='bold')
ax.set_ylabel('AUC')
ax.set_xticks(x)
ax.set_xticklabels(names, fontsize=9)
ax.set_ylim(0.3, 0.85)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

# 2c: ROC curves
ax = axes[2]
for name, yprob, color, lw in [
    ('LR (Raw)', yprob_t_lr, '#9C27B0', 1.5),
    ('ET (Haar)', yprob_t_et, '#FF9800', 1.5),
    ('RF (Haar)', yprob_t_rf, '#009688', 1.5),
    ('LR (N-gram)', yprob_t_ng, '#795548', 1.5),
    ('ET (Haar+Full)', best_prob, 'black', 2.5),
]:
    fpr, tpr, _ = roc_curve(y_test, yprob)
    auc = roc_auc_score(y_test, yprob)
    ax.plot(fpr, tpr, color=color, linewidth=lw, label=f'{name} (AUC={auc:.3f})')
ax.plot([0, 1], [0, 1], 'gray', linestyle='--', linewidth=1, label='Random')
ax.set_title('ROC Curves (Test Set)', fontweight='bold')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig2_model_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_model_comparison.png")

# ── Figure 3: Best Model Analysis ────────────────────────────────────────────
print("Generating Figure 3: Best Model Analysis...")
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle(f'Best Model Analysis: ExtraTrees + Haar Wavelets (Train+Val → Test)', fontsize=13, fontweight='bold')

# 3a: Confusion matrix
ax = axes[0]
cm = confusion_matrix(y_test, best_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['Non-Variable', 'Variable'],
            yticklabels=['Non-Variable', 'Variable'],
            annot_kws={'size': 14})
ax.set_title(f'Confusion Matrix\nBal.Acc={best_ba:.3f}, AUC={best_auc:.3f}, F1={best_f1:.3f}', fontweight='bold')
ax.set_xlabel('Predicted Label')
ax.set_ylabel('True Label')

# 3b: Prediction probability distribution
ax = axes[1]
for label, color, name in [(0, '#2196F3', 'Non-Variable'), (1, '#F44336', 'Variable')]:
    mask = y_test == label
    ax.hist(best_prob[mask], bins=20, alpha=0.6, color=color, label=name,
            edgecolor='black', linewidth=0.5, density=True)
ax.axvline(0.5, color='black', linestyle='--', linewidth=2, label='Decision Threshold')
ax.set_title('Prediction Probability Distribution', fontweight='bold')
ax.set_xlabel('P(Variable)')
ax.set_ylabel('Density')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# 3c: Cross-validation scores
ax = axes[2]
cv_data = [
    ('ET\n(Haar)', cv_et),
    ('RF\n(Haar)', cv_rf),
    ('LR\n(Raw)', cv_lr),
    ('LR\n(N-gram)', cv_ng),
]
cv_names = [d[0] for d in cv_data]
cv_means = [d[1].mean() for d in cv_data]
cv_stds = [d[1].std() for d in cv_data]
x = np.arange(len(cv_names))
bars = ax.bar(x, cv_means, yerr=cv_stds, capsize=6, color='#2196F3', alpha=0.8,
              edgecolor='black', linewidth=0.5, error_kw={'linewidth': 2})
ax.axhline(0.78, color='green', linestyle='--', linewidth=2, label='Baseline (0.78)')
ax.axhline(0.5, color='gray', linestyle=':', linewidth=1.5, label='Random (0.50)')
for i, (m, s) in enumerate(zip(cv_means, cv_stds)):
    ax.text(i, m + s + 0.01, f'{m:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
ax.set_title('5-Fold CV Balanced Accuracy (Train+Val)', fontweight='bold')
ax.set_ylabel('Balanced Accuracy')
ax.set_xticks(x)
ax.set_xticklabels(cv_names, fontsize=9)
ax.set_ylim(0.3, 0.85)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/fig3_best_model.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3_best_model.png")

# ── Figure 4: Feature Analysis ────────────────────────────────────────────────
print("Generating Figure 4: Feature Analysis...")
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle('Feature Analysis for Variable Star Classification', fontsize=14, fontweight='bold')

# 4a: Haar feature importance
ax = axes[0, 0]
haar_feat_names = []
for level in range(5):
    for stat in ['mean', 'std', 'max', 'min']:
        haar_feat_names.append(f'L{level+1}_{stat}')
haar_feat_names.append('approx')

clf_fi = ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42)
clf_fi.fit(X_tr_haar, y_train)
importances = clf_fi.feature_importances_
top_n = min(15, len(importances))
top_idx = np.argsort(importances)[::-1][:top_n]
top_names = [haar_feat_names[i] if i < len(haar_feat_names) else f'feat_{i}' for i in top_idx]
colors_imp = ['#F44336' if importances[i] > np.median(importances) else '#2196F3' for i in top_idx]
ax.barh(range(top_n), importances[top_idx][::-1], color=colors_imp[::-1], alpha=0.8, edgecolor='black', linewidth=0.5)
ax.set_yticks(range(top_n))
ax.set_yticklabels(top_names[::-1], fontsize=8)
ax.set_title('Top Haar Feature Importances (ET)', fontweight='bold')
ax.set_xlabel('Importance')
ax.grid(True, alpha=0.3, axis='x')

# 4b: Haar level 1 detail std by class
ax = axes[0, 1]
for label, color, name in [(0, '#2196F3', 'Non-Variable'), (1, '#F44336', 'Variable')]:
    mask = y_train == label
    ax.hist(X_tr_haar[mask, 1], bins=20, alpha=0.6, color=color, label=name,
            edgecolor='black', linewidth=0.3, density=True)
ax.set_title('Haar L1 Detail Std by Class', fontweight='bold')
ax.set_xlabel('Value')
ax.set_ylabel('Density')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# 4c: Haar level 2 detail std by class
ax = axes[0, 2]
for label, color, name in [(0, '#2196F3', 'Non-Variable'), (1, '#F44336', 'Variable')]:
    mask = y_train == label
    ax.hist(X_tr_haar[mask, 5], bins=20, alpha=0.6, color=color, label=name,
            edgecolor='black', linewidth=0.3, density=True)
ax.set_title('Haar L2 Detail Std by Class', fontweight='bold')
ax.set_xlabel('Value')
ax.set_ylabel('Density')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# 4d: Scatter plot of Haar features
ax = axes[1, 0]
for label, color, name, marker in [(0, '#2196F3', 'Non-Variable', 'o'), (1, '#F44336', 'Variable', '^')]:
    mask = y_train == label
    ax.scatter(X_tr_haar[mask, 0], X_tr_haar[mask, 1],
               c=color, alpha=0.3, s=15, label=name, marker=marker)
ax.set_xlabel('Haar L1 Detail Mean')
ax.set_ylabel('Haar L1 Detail Std')
ax.set_title('Haar Feature Space (L1)', fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# 4e: Std distribution by class
ax = axes[1, 1]
for label, color, name in [(0, '#2196F3', 'Non-Variable'), (1, '#F44336', 'Variable')]:
    stds = [to_nums(s).std() for s in train[train['label']==label]['symbol_series']]
    ax.hist(stds, bins=20, alpha=0.6, color=color, label=name, edgecolor='black', linewidth=0.3, density=True)
ax.set_title('Series Std Dev by Class', fontweight='bold')
ax.set_xlabel('Standard Deviation')
ax.set_ylabel('Density')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# 4f: Prediction probability scatter
ax = axes[1, 2]
for label, color, name in [(0, '#2196F3', 'Non-Variable'), (1, '#F44336', 'Variable')]:
    mask = y_test == label
    ax.scatter(np.where(mask)[0], best_prob[mask], c=color, alpha=0.5, s=20, label=name)
ax.axhline(0.5, color='black', linestyle='--', linewidth=1.5, label='Threshold')
ax.set_title('Test Set Prediction Probabilities', fontweight='bold')
ax.set_xlabel('Sample Index')
ax.set_ylabel('P(Variable)')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig4_feature_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig4_feature_analysis.png")

# ── Save final predictions ────────────────────────────────────────────────────
pd.DataFrame({
    'object_id': test['object_id'],
    'true_label': y_test,
    'pred_label': best_pred,
    'pred_prob': best_prob
}).to_csv('outputs/final_predictions.csv', index=False)

print("\n=== FINAL SUMMARY ===")
print(f"Best model: ET_haar (train+val)")
print(f"Test Balanced Accuracy: {best_ba:.4f}")
print(f"Test Accuracy:          {best_acc:.4f}")
print(f"Test AUC:               {best_auc:.4f}")
print(f"Test F1:                {best_f1:.4f}")
print(f"Baseline:               0.78")
print(f"CV (5-fold) ET_haar:    {cv_et.mean():.4f} +/- {cv_et.std():.4f}")
print(f"CV (5-fold) LR_raw:     {cv_lr.mean():.4f} +/- {cv_lr.std():.4f}")
print("\nClassification Report:")
print(classification_report(y_test, best_pred, target_names=['Non-Variable', 'Variable']))
print("Done!")
