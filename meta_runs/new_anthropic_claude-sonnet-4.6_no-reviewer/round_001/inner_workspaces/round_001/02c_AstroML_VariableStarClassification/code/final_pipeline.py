"""Final pipeline for variable star classification.

Best approach: ExtraTreesClassifier with Haar wavelet features,
trained on train+val combined.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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
from scipy import stats
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

# ── Feature extraction ────────────────────────────────────────────────────────
def haar_features(df):
    """Haar wavelet decomposition features."""
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

def extract_stats(df):
    """Statistical features from symbol series."""
    rows = []
    for _, row in df.iterrows():
        s = row['symbol_series']
        nums = to_nums(s)
        n = len(nums)
        cnt = Counter(s)
        diffs = np.diff(nums)
        feat = []
        
        # Basic statistics
        feat.extend([
            nums.mean(), nums.std(), nums.var(), nums.min(), nums.max(),
            nums.max()-nums.min(), np.median(nums),
            np.percentile(nums, 25), np.percentile(nums, 75),
            np.percentile(nums, 75)-np.percentile(nums, 25),
            stats.skew(nums), stats.kurtosis(nums),
            np.mean(np.abs(nums - nums.mean()))
        ])
        
        # Character frequencies
        for sym in SYMBOLS:
            feat.append(cnt.get(sym, 0) / n)
        
        # Variability indicators
        feat.extend([
            len(set(s)),
            sum(1 for c in s if c in ('z', '*')) / n,
            sum(1 for c in s if c in ('.', 'u')) / n,
            sum(1 for c in s if c in ('.', '*')) / n
        ])
        
        # Transition features
        feat.extend([
            np.sum(diffs != 0), np.mean(np.abs(diffs)), np.std(diffs),
            np.max(np.abs(diffs)), np.sum(np.abs(diffs) >= 3),
            np.sum(np.diff(np.sign(diffs)) != 0),
            np.sum(diffs > 0), np.sum(diffs < 0)
        ])
        
        # Run-length features
        runs = []
        cur_run = 1
        for i in range(1, n):
            if s[i] == s[i-1]:
                cur_run += 1
            else:
                runs.append(cur_run)
                cur_run = 1
        runs.append(cur_run)
        feat.extend([max(runs), np.mean(runs), len(runs)])
        
        # Positional features
        half = n // 2
        feat.extend([
            nums[:half].mean(), nums[half:].mean(),
            nums[half:].mean()-nums[:half].mean(),
            nums[:half].std(), nums[half:].std(),
            np.polyfit(np.arange(n), nums, 1)[0]
        ])
        
        # Autocorrelation
        for lag in [1, 2, 3, 4, 5]:
            if n > lag + 1:
                corr = np.corrcoef(nums[:-lag], nums[lag:])[0, 1]
                feat.append(corr if not np.isnan(corr) else 0)
            else:
                feat.append(0)
        
        # Entropy
        probs = np.array([cnt.get(sym, 0) / n for sym in SYMBOLS])
        probs_nz = probs[probs > 0]
        feat.append(-np.sum(probs_nz * np.log(probs_nz)))
        
        # FFT features
        fft = np.fft.rfft(nums - nums.mean())
        fft_power = np.abs(fft)**2
        for i in range(1, 6):
            feat.append(fft_power[i] if len(fft_power) > i else 0)
        feat.append(np.argmax(fft_power[1:]) + 1 if len(fft_power) > 1 else 0)
        
        # Local extrema
        feat.extend([
            sum(1 for i in range(1, n-1) if nums[i] > nums[i-1] and nums[i] > nums[i+1]),
            sum(1 for i in range(1, n-1) if nums[i] < nums[i-1] and nums[i] < nums[i+1])
        ])
        
        rows.append(feat)
    return np.array(rows)

print("Extracting features...")
X_tr_raw   = np.array([to_nums(s) for s in train['symbol_series']])
X_v_raw    = np.array([to_nums(s) for s in val['symbol_series']])
X_te_raw   = np.array([to_nums(s) for s in test['symbol_series']])
X_full_raw = np.array([to_nums(s) for s in train_full['symbol_series']])

X_tr_haar   = haar_features(train)
X_v_haar    = haar_features(val)
X_te_haar   = haar_features(test)
X_full_haar = haar_features(train_full)

X_tr_stats   = extract_stats(train)
X_v_stats    = extract_stats(val)
X_te_stats   = extract_stats(test)
X_full_stats = extract_stats(train_full)

X_tr_comb   = np.hstack([X_tr_raw, X_tr_haar, X_tr_stats])
X_v_comb    = np.hstack([X_v_raw, X_v_haar, X_v_stats])
X_te_comb   = np.hstack([X_te_raw, X_te_haar, X_te_stats])
X_full_comb = np.hstack([X_full_raw, X_full_haar, X_full_stats])

print(f"Feature shapes: raw={X_tr_raw.shape[1]}, haar={X_tr_haar.shape[1]}, stats={X_tr_stats.shape[1]}, comb={X_tr_comb.shape[1]}")

# ── Model definitions ─────────────────────────────────────────────────────────
models_train_only = {
    'ET_raw': (ExtraTreesClassifier(n_estimators=200, class_weight='balanced', random_state=42), X_tr_raw, X_v_raw, X_te_raw),
    'ET_haar': (ExtraTreesClassifier(n_estimators=200, class_weight='balanced', random_state=42), X_tr_haar, X_v_haar, X_te_haar),
    'RF_haar': (RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42), X_tr_haar, X_v_haar, X_te_haar),
    'ET_comb': (ExtraTreesClassifier(n_estimators=200, class_weight='balanced', random_state=42), X_tr_comb, X_v_comb, X_te_comb),
    'RF_comb': (RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42), X_tr_comb, X_v_comb, X_te_comb),
    'LR_raw': (Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=0.1, max_iter=500, class_weight='balanced', random_state=42))]), X_tr_raw, X_v_raw, X_te_raw),
}

models_full = {
    'ET_haar_full': (ExtraTreesClassifier(n_estimators=200, class_weight='balanced', random_state=42), X_full_haar, X_te_haar),
    'RF_haar_full': (RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42), X_full_haar, X_te_haar),
    'ET_comb_full': (ExtraTreesClassifier(n_estimators=200, class_weight='balanced', random_state=42), X_full_comb, X_te_comb),
    'RF_comb_full': (RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42), X_full_comb, X_te_comb),
}

# ── Train-only evaluation ─────────────────────────────────────────────────────
print("\nTrain-only models (val and test):")
train_results = {}
for name, (clf, Xtr, Xv, Xte) in models_train_only.items():
    clf.fit(Xtr, y_train)
    yp_v = clf.predict(Xv)
    yp_t = clf.predict(Xte)
    yprob_v = clf.predict_proba(Xv)[:, 1]
    yprob_t = clf.predict_proba(Xte)[:, 1]
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    auc_v = roc_auc_score(y_val, yprob_v)
    auc_t = roc_auc_score(y_test, yprob_t)
    train_results[name] = {
        'val_ba': ba_v, 'test_ba': ba_t, 'val_auc': auc_v, 'test_auc': auc_t,
        'yp_v': yp_v, 'yp_t': yp_t, 'yprob_v': yprob_v, 'yprob_t': yprob_t
    }
    print(f"  {name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}, val_auc={auc_v:.4f}")

# ── Full data evaluation ──────────────────────────────────────────────────────
print("\nFull data models (test only):")
full_results = {}
for name, (clf, Xfull, Xte) in models_full.items():
    clf.fit(Xfull, y_full)
    yp_t = clf.predict(Xte)
    yprob_t = clf.predict_proba(Xte)[:, 1]
    ba_t = balanced_accuracy_score(y_test, yp_t)
    auc_t = roc_auc_score(y_test, yprob_t)
    full_results[name] = {
        'test_ba': ba_t, 'test_auc': auc_t,
        'yp_t': yp_t, 'yprob_t': yprob_t
    }
    print(f"  {name}: test_ba={ba_t:.4f}, test_auc={auc_t:.4f}")

# ── Cross-validation ──────────────────────────────────────────────────────────
print("\nCross-validation (5-fold on train+val):")
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

cv_models = [
    ('ET_haar', ExtraTreesClassifier(n_estimators=200, class_weight='balanced', random_state=42), X_full_haar),
    ('RF_haar', RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42), X_full_haar),
    ('ET_comb', ExtraTreesClassifier(n_estimators=200, class_weight='balanced', random_state=42), X_full_comb),
    ('LR_raw', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=0.1, max_iter=500, class_weight='balanced', random_state=42))]), X_full_raw),
]

cv_results = {}
for name, clf, X in cv_models:
    scores = cross_val_score(clf, X, y_full, cv=skf, scoring='balanced_accuracy')
    cv_results[name] = scores
    print(f"  {name}: CV ba={scores.mean():.4f} +/- {scores.std():.4f}")

# ── Best model selection ──────────────────────────────────────────────────────
# Use ET_haar trained on full data as the best model
best_model = ExtraTreesClassifier(n_estimators=200, class_weight='balanced', random_state=42)
best_model.fit(X_full_haar, y_full)
best_pred = best_model.predict(X_te_haar)
best_prob = best_model.predict_proba(X_te_haar)[:, 1]
best_ba = balanced_accuracy_score(y_test, best_pred)
best_auc = roc_auc_score(y_test, best_prob)
best_f1 = f1_score(y_test, best_pred)
best_acc = accuracy_score(y_test, best_pred)

print(f"\n=== BEST MODEL: ET_haar (train+val) ===")
print(f"Test Balanced Accuracy: {best_ba:.4f}")
print(f"Test Accuracy:          {best_acc:.4f}")
print(f"Test AUC:               {best_auc:.4f}")
print(f"Test F1:                {best_f1:.4f}")
print(f"Baseline:               0.78")
print("\nClassification Report:")
print(classification_report(y_test, best_pred, target_names=['Non-Variable', 'Variable']))

# ── Save results ──────────────────────────────────────────────────────────────
pd.DataFrame({
    'object_id': test['object_id'],
    'true_label': y_test,
    'pred_label': best_pred,
    'pred_prob': best_prob
}).to_csv('outputs/final_predictions.csv', index=False)

# Save all results
all_results_df = pd.DataFrame([
    {'model': k, 'split': 'train_only', 'val_ba': v['val_ba'], 'test_ba': v['test_ba'],
     'val_auc': v['val_auc'], 'test_auc': v['test_auc']}
    for k, v in train_results.items()
] + [
    {'model': k, 'split': 'full', 'val_ba': None, 'test_ba': v['test_ba'],
     'val_auc': None, 'test_auc': v['test_auc']}
    for k, v in full_results.items()
])
all_results_df.to_csv('outputs/all_results.csv', index=False)
print("\nAll results:")
print(all_results_df.to_string())

# ── Generate figures ──────────────────────────────────────────────────────────
print("\nGenerating figures...")

# ── Figure 1: Data Overview ───────────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(15, 9))
fig.suptitle('Variable Star Classification — Data Overview', fontsize=14, fontweight='bold')

# 1a: Label distribution
ax = axes[0, 0]
for split_name, df, color in [('Train', train, 'steelblue'), ('Val', val, 'orange'), ('Test', test, 'green')]:
    counts = df['label'].value_counts().sort_index()
    x = np.array([0, 1])
    offset = {'Train': -0.25, 'Val': 0, 'Test': 0.25}[split_name]
    ax.bar(x + offset, counts.values, width=0.22, label=split_name, alpha=0.8)
ax.set_title('Label Distribution by Split')
ax.set_ylabel('Count')
ax.set_xticks([0, 1])
ax.set_xticklabels(['Non-Variable (0)', 'Variable (1)'])
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# 1b: Example series
ax = axes[0, 1]
example_var = train[train['label']==1]['symbol_series'].iloc[0]
example_nonvar = train[train['label']==0]['symbol_series'].iloc[0]
nums_var = to_nums(example_var)
nums_nonvar = to_nums(example_nonvar)
ax.plot(nums_var, 'r-o', markersize=3, label='Variable', alpha=0.8)
ax.plot(nums_nonvar, 'b-s', markersize=3, label='Non-Variable', alpha=0.8)
ax.set_title('Example Symbol Series')
ax.set_xlabel('Time Step')
ax.set_ylabel('Symbol Value')
ax.set_yticks(range(8))
ax.set_yticklabels(SYMBOLS)
ax.legend()
ax.grid(True, alpha=0.3)

# 1c: Symbol frequency by class
ax = axes[0, 2]
var_series = ''.join(train[train['label']==1]['symbol_series'].tolist())
non_series = ''.join(train[train['label']==0]['symbol_series'].tolist())
var_freq = [var_series.count(s) / len(var_series) for s in SYMBOLS]
non_freq = [non_series.count(s) / len(non_series) for s in SYMBOLS]
x = np.arange(len(SYMBOLS))
width = 0.35
ax.bar(x - width/2, non_freq, width, label='Non-Variable', color='steelblue', alpha=0.8)
ax.bar(x + width/2, var_freq, width, label='Variable', color='tomato', alpha=0.8)
ax.set_title('Symbol Frequency by Class')
ax.set_xlabel('Symbol')
ax.set_ylabel('Frequency')
ax.set_xticks(x)
ax.set_xticklabels(SYMBOLS)
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# 1d: Position-wise mean difference
ax = axes[1, 0]
var_pos_means = []
non_pos_means = []
for pos in range(40):
    var_vals = [SYM2IDX.get(s[pos], 0) for s in train[train['label']==1]['symbol_series']]
    non_vals = [SYM2IDX.get(s[pos], 0) for s in train[train['label']==0]['symbol_series']]
    var_pos_means.append(np.mean(var_vals))
    non_pos_means.append(np.mean(non_vals))
diffs = np.array(var_pos_means) - np.array(non_pos_means)
colors = ['tomato' if d > 0 else 'steelblue' for d in diffs]
ax.bar(range(40), diffs, color=colors, alpha=0.8)
ax.axhline(0, color='black', linewidth=0.5)
ax.set_title('Position-wise Mean Difference (Var - Non-Var)')
ax.set_xlabel('Position')
ax.set_ylabel('Mean Difference')
ax.grid(True, alpha=0.3, axis='y')

# 1e: Distribution of std by class
ax = axes[1, 1]
for label, color, name in [(0, 'steelblue', 'Non-Variable'), (1, 'tomato', 'Variable')]:
    stds = [to_nums(s).std() for s in train[train['label']==label]['symbol_series']]
    ax.hist(stds, bins=20, alpha=0.6, color=color, label=name, edgecolor='black', linewidth=0.5)
ax.set_title('Distribution of Series Std Dev by Class')
ax.set_xlabel('Standard Deviation')
ax.set_ylabel('Count')
ax.legend()
ax.grid(True, alpha=0.3)

# 1f: Haar wavelet features
ax = axes[1, 2]
for label, color, name in [(0, 'steelblue', 'Non-Variable'), (1, 'tomato', 'Variable')]:
    mask = y_train == label
    haar_std = X_tr_haar[mask, 1]  # std of first detail level
    ax.hist(haar_std, bins=20, alpha=0.6, color=color, label=name, edgecolor='black', linewidth=0.5)
ax.set_title('Haar Detail Std (Level 1) by Class')
ax.set_xlabel('Haar Detail Std')
ax.set_ylabel('Count')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig1_data_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1_data_overview.png")

# ── Figure 2: Model Comparison ────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Model Performance Comparison', fontsize=14, fontweight='bold')

# 2a: Val vs Test balanced accuracy (train-only models)
ax = axes[0]
model_names = list(train_results.keys())
val_bas = [train_results[m]['val_ba'] for m in model_names]
test_bas = [train_results[m]['test_ba'] for m in model_names]
x = np.arange(len(model_names))
width = 0.35
bars1 = ax.bar(x - width/2, val_bas, width, label='Validation', color='steelblue', alpha=0.8)
bars2 = ax.bar(x + width/2, test_bas, width, label='Test', color='tomato', alpha=0.8)
ax.axhline(0.78, color='green', linestyle='--', linewidth=2, label='Baseline (0.78)')
ax.axhline(0.5, color='gray', linestyle=':', linewidth=1, label='Random (0.50)')
ax.set_title('Balanced Accuracy (Train-only Models)')
ax.set_ylabel('Balanced Accuracy')
ax.set_xticks(x)
ax.set_xticklabels([m.replace('_', '\n') for m in model_names], fontsize=7)
ax.set_ylim(0.3, 0.85)
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3, axis='y')

# 2b: Full data models test performance
ax = axes[1]
full_names = list(full_results.keys())
full_bas = [full_results[m]['test_ba'] for m in full_names]
full_aucs = [full_results[m]['test_auc'] for m in full_names]
x = np.arange(len(full_names))
width = 0.35
ax.bar(x - width/2, full_bas, width, label='Balanced Acc', color='steelblue', alpha=0.8)
ax.bar(x + width/2, full_aucs, width, label='AUC', color='tomato', alpha=0.8)
ax.axhline(0.78, color='green', linestyle='--', linewidth=2, label='Baseline (0.78)')
ax.axhline(0.5, color='gray', linestyle=':', linewidth=1, label='Random (0.50)')
ax.set_title('Test Performance (Train+Val Models)')
ax.set_ylabel('Score')
ax.set_xticks(x)
ax.set_xticklabels([m.replace('_full', '').replace('_', '\n') for m in full_names], fontsize=7)
ax.set_ylim(0.3, 0.85)
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3, axis='y')

# 2c: ROC curves
ax = axes[2]
# Best train-only models
for name in ['ET_haar', 'RF_haar', 'ET_comb']:
    fpr, tpr, _ = roc_curve(y_test, train_results[name]['yprob_t'])
    ax.plot(fpr, tpr, label=f"{name} (AUC={train_results[name]['test_auc']:.3f})", linewidth=1.5)
# Best full model
fpr, tpr, _ = roc_curve(y_test, best_prob)
ax.plot(fpr, tpr, 'k-', linewidth=2.5, label=f"ET_haar_full (AUC={best_auc:.3f})")
ax.plot([0, 1], [0, 1], 'gray', linestyle='--', label='Random')
ax.set_title('ROC Curves (Test Set)')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig2_model_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_model_comparison.png")

# ── Figure 3: Best Model Analysis ────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Best Model Analysis (ET + Haar Features, Train+Val)', fontsize=14, fontweight='bold')

# 3a: Confusion matrix
ax = axes[0]
cm = confusion_matrix(y_test, best_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['Non-Variable', 'Variable'],
            yticklabels=['Non-Variable', 'Variable'])
ax.set_title(f'Confusion Matrix\n(Bal.Acc={best_ba:.3f}, AUC={best_auc:.3f})')
ax.set_xlabel('Predicted')
ax.set_ylabel('True')

# 3b: Prediction probability distribution
ax = axes[1]
for label, color, name in [(0, 'steelblue', 'Non-Variable'), (1, 'tomato', 'Variable')]:
    mask = y_test == label
    ax.hist(best_prob[mask], bins=20, alpha=0.6, color=color, label=name,
            edgecolor='black', linewidth=0.5, density=True)
ax.axvline(0.5, color='black', linestyle='--', linewidth=1.5, label='Threshold')
ax.set_title('Prediction Probability Distribution')
ax.set_xlabel('Predicted Probability (Variable)')
ax.set_ylabel('Density')
ax.legend()
ax.grid(True, alpha=0.3)

# 3c: Cross-validation scores
ax = axes[2]
cv_names = list(cv_results.keys())
cv_means = [cv_results[k].mean() for k in cv_names]
cv_stds = [cv_results[k].std() for k in cv_names]
x = np.arange(len(cv_names))
ax.bar(x, cv_means, yerr=cv_stds, capsize=5, color='steelblue', alpha=0.8, edgecolor='black')
ax.axhline(0.78, color='green', linestyle='--', linewidth=2, label='Baseline (0.78)')
ax.axhline(0.5, color='gray', linestyle=':', linewidth=1, label='Random (0.50)')
ax.set_title('5-Fold CV Balanced Accuracy (Train+Val)')
ax.set_ylabel('Balanced Accuracy')
ax.set_xticks(x)
ax.set_xticklabels([n.replace('_', '\n') for n in cv_names], fontsize=8)
ax.set_ylim(0.3, 0.85)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/fig3_best_model.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3_best_model.png")

# ── Figure 4: Feature Analysis ────────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(15, 9))
fig.suptitle('Feature Analysis', fontsize=14, fontweight='bold')

# 4a: Haar feature importance
ax = axes[0, 0]
haar_feat_names = []
for level in range(5):
    for stat in ['mean', 'std', 'max', 'min']:
        haar_feat_names.append(f'L{level+1}_{stat}')
haar_feat_names.append('approx')

# Train a model on train only for feature importance
clf_fi = ExtraTreesClassifier(n_estimators=200, class_weight='balanced', random_state=42)
clf_fi.fit(X_tr_haar, y_train)
importances = clf_fi.feature_importances_
top_n = min(15, len(importances))
top_idx = np.argsort(importances)[::-1][:top_n]
top_names = [haar_feat_names[i] if i < len(haar_feat_names) else f'feat_{i}' for i in top_idx]
ax.barh(range(top_n), importances[top_idx][::-1], color='steelblue', alpha=0.8, edgecolor='black', linewidth=0.5)
ax.set_yticks(range(top_n))
ax.set_yticklabels(top_names[::-1], fontsize=8)
ax.set_title('Top Haar Feature Importances')
ax.set_xlabel('Importance')
ax.grid(True, alpha=0.3, axis='x')

# 4b: Haar level 1 detail mean by class
ax = axes[0, 1]
for label, color, name in [(0, 'steelblue', 'Non-Variable'), (1, 'tomato', 'Variable')]:
    mask = y_train == label
    ax.hist(X_tr_haar[mask, 0], bins=20, alpha=0.6, color=color, label=name,
            edgecolor='black', linewidth=0.5, density=True)
ax.set_title('Haar L1 Detail Mean by Class')
ax.set_xlabel('Value')
ax.set_ylabel('Density')
ax.legend()
ax.grid(True, alpha=0.3)

# 4c: Haar level 1 detail std by class
ax = axes[0, 2]
for label, color, name in [(0, 'steelblue', 'Non-Variable'), (1, 'tomato', 'Variable')]:
    mask = y_train == label
    ax.hist(X_tr_haar[mask, 1], bins=20, alpha=0.6, color=color, label=name,
            edgecolor='black', linewidth=0.5, density=True)
ax.set_title('Haar L1 Detail Std by Class')
ax.set_xlabel('Value')
ax.set_ylabel('Density')
ax.legend()
ax.grid(True, alpha=0.3)

# 4d: Position-wise chi-squared statistics
ax = axes[1, 0]
from scipy.stats import chi2_contingency
chi2_stats = []
for pos in range(40):
    var_chars = Counter([s[pos] for s in train[train['label']==1]['symbol_series']])
    non_chars = Counter([s[pos] for s in train[train['label']==0]['symbol_series']])
    contingency = np.array([[var_chars.get(sym, 0) for sym in SYMBOLS],
                             [non_chars.get(sym, 0) for sym in SYMBOLS]])
    chi2, p, dof, expected = chi2_contingency(contingency)
    chi2_stats.append(chi2)
colors_chi2 = ['tomato' if c > 14 else 'steelblue' for c in chi2_stats]
ax.bar(range(40), chi2_stats, color=colors_chi2, alpha=0.8)
ax.axhline(14.07, color='red', linestyle='--', linewidth=1.5, label='p=0.05 threshold')
ax.set_title('Position-wise Chi-squared Statistics')
ax.set_xlabel('Position')
ax.set_ylabel('Chi-squared')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# 4e: Scatter plot of Haar features
ax = axes[1, 1]
for label, color, name, marker in [(0, 'steelblue', 'Non-Variable', 'o'), (1, 'tomato', 'Variable', '^')]:
    mask = y_train == label
    ax.scatter(X_tr_haar[mask, 0], X_tr_haar[mask, 1],
               c=color, alpha=0.3, s=15, label=name, marker=marker)
ax.set_xlabel('Haar L1 Detail Mean')
ax.set_ylabel('Haar L1 Detail Std')
ax.set_title('Haar Feature Space')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# 4f: Prediction probability vs true label
ax = axes[1, 2]
for label, color, name in [(0, 'steelblue', 'Non-Variable'), (1, 'tomato', 'Variable')]:
    mask = y_test == label
    ax.scatter(np.where(mask)[0], best_prob[mask], c=color, alpha=0.5, s=15, label=name)
ax.axhline(0.5, color='black', linestyle='--', linewidth=1.5, label='Threshold')
ax.set_title('Prediction Probabilities (Test Set)')
ax.set_xlabel('Sample Index')
ax.set_ylabel('Predicted Probability (Variable)')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig4_feature_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig4_feature_analysis.png")

print("\n=== SUMMARY ===")
print(f"Best model: ET_haar (train+val)")
print(f"Test Balanced Accuracy: {best_ba:.4f}")
print(f"Test AUC: {best_auc:.4f}")
print(f"Test F1: {best_f1:.4f}")
print(f"Baseline: 0.78")
print(f"Gap to baseline: {0.78 - best_ba:.4f}")
print("\nDone!")
