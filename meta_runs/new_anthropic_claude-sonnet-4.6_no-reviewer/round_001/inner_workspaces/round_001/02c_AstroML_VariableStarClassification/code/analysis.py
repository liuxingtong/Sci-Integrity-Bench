"""Variable Star Classification from symbol_series features."""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import (
    balanced_accuracy_score, accuracy_score, classification_report,
    confusion_matrix, roc_auc_score, roc_curve, f1_score
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

# ── Reproducibility ──────────────────────────────────────────────────────────
np.random.seed(42)

# ── Load data ────────────────────────────────────────────────────────────────
train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

print(f"Train: {train.shape}, Val: {val.shape}, Test: {test.shape}")
print(f"Train label dist: {train['label'].value_counts().to_dict()}")
print(f"Val   label dist: {val['label'].value_counts().to_dict()}")
print(f"Test  label dist: {test['label'].value_counts().to_dict()}")

# ── Symbol mapping ───────────────────────────────────────────────────────────
# Characters represent discretized brightness levels
# Order: . u v w x y z * (. = missing/low, * = high/variable)
SYMBOLS = ['.', 'u', 'v', 'w', 'x', 'y', 'z', '*']
SYM2IDX = {s: i for i, s in enumerate(SYMBOLS)}

def series_to_numeric(s):
    """Convert symbol string to numeric array."""
    return np.array([SYM2IDX.get(c, 0) for c in s], dtype=float)

# ── Feature Engineering ───────────────────────────────────────────────────────
def extract_features(df):
    """Extract rich features from symbol_series."""
    feats = []
    for _, row in df.iterrows():
        s = row['symbol_series']
        nums = series_to_numeric(s)
        n = len(nums)
        
        feat = {}
        
        # --- Basic statistics ---
        feat['mean']   = nums.mean()
        feat['std']    = nums.std()
        feat['min']    = nums.min()
        feat['max']    = nums.max()
        feat['range']  = nums.max() - nums.min()
        feat['median'] = np.median(nums)
        feat['q25']    = np.percentile(nums, 25)
        feat['q75']    = np.percentile(nums, 75)
        feat['iqr']    = feat['q75'] - feat['q25']
        feat['skew']   = pd.Series(nums).skew()
        feat['kurt']   = pd.Series(nums).kurt()
        
        # --- Character frequency features ---
        cnt = Counter(s)
        for sym in SYMBOLS:
            feat[f'freq_{sym}'] = cnt.get(sym, 0) / n
        
        # --- Variability indicators ---
        # Number of unique symbols
        feat['n_unique'] = len(set(s))
        # Fraction of high-value symbols (z, *)
        feat['frac_high'] = sum(1 for c in s if c in ('z', '*')) / n
        # Fraction of low-value symbols (., u)
        feat['frac_low']  = sum(1 for c in s if c in ('.', 'u')) / n
        # Fraction of mid-value symbols
        feat['frac_mid']  = sum(1 for c in s if c in ('v', 'w', 'x', 'y')) / n
        
        # --- Transition features ---
        diffs = np.diff(nums)
        feat['n_transitions']   = np.sum(diffs != 0)
        feat['mean_abs_diff']   = np.mean(np.abs(diffs))
        feat['std_diff']        = np.std(diffs)
        feat['max_abs_diff']    = np.max(np.abs(diffs)) if len(diffs) > 0 else 0
        feat['n_large_jumps']   = np.sum(np.abs(diffs) >= 3)  # large jumps
        feat['n_sign_changes']  = np.sum(np.diff(np.sign(diffs)) != 0)
        
        # --- Run-length features ---
        # Longest run of same symbol
        runs = []
        cur_run = 1
        for i in range(1, n):
            if s[i] == s[i-1]:
                cur_run += 1
            else:
                runs.append(cur_run)
                cur_run = 1
        runs.append(cur_run)
        feat['max_run']  = max(runs)
        feat['mean_run'] = np.mean(runs)
        feat['n_runs']   = len(runs)
        
        # --- Positional features ---
        # First half vs second half statistics
        half = n // 2
        feat['mean_first_half'] = nums[:half].mean()
        feat['mean_second_half'] = nums[half:].mean()
        feat['diff_halves'] = feat['mean_second_half'] - feat['mean_first_half']
        feat['std_first_half'] = nums[:half].std()
        feat['std_second_half'] = nums[half:].std()
        
        # --- Autocorrelation features ---
        if n > 2:
            feat['autocorr_lag1'] = pd.Series(nums).autocorr(lag=1)
            feat['autocorr_lag2'] = pd.Series(nums).autocorr(lag=2)
            feat['autocorr_lag3'] = pd.Series(nums).autocorr(lag=3)
        else:
            feat['autocorr_lag1'] = 0
            feat['autocorr_lag2'] = 0
            feat['autocorr_lag3'] = 0
        
        # --- Entropy-like features ---
        probs = np.array([cnt.get(sym, 0) / n for sym in SYMBOLS])
        probs = probs[probs > 0]
        feat['entropy'] = -np.sum(probs * np.log(probs))
        
        # --- N-gram features (bigrams) ---
        bigrams = [s[i:i+2] for i in range(n-1)]
        # Count transitions between high and low
        feat['n_high_to_low'] = sum(1 for bg in bigrams if bg[0] in ('z','*') and bg[1] in ('.','u'))
        feat['n_low_to_high'] = sum(1 for bg in bigrams if bg[0] in ('.','u') and bg[1] in ('z','*'))
        
        # --- Position of extremes ---
        feat['pos_max'] = np.argmax(nums) / n
        feat['pos_min'] = np.argmin(nums) / n
        
        feats.append(feat)
    
    return pd.DataFrame(feats)

print("\nExtracting features...")
X_train = extract_features(train)
X_val   = extract_features(val)
X_test  = extract_features(test)

y_train = train['label'].values
y_val   = val['label'].values
y_test  = test['label'].values

print(f"Feature matrix shape: {X_train.shape}")
print(f"Features: {X_train.columns.tolist()}")

# Fill NaN (from autocorr on short series)
X_train = X_train.fillna(0)
X_val   = X_val.fillna(0)
X_test  = X_test.fillna(0)

# ── Model Training ────────────────────────────────────────────────────────────
models = {
    'Random Forest': RandomForestClassifier(n_estimators=300, max_depth=None,
                                             min_samples_leaf=2, random_state=42,
                                             class_weight='balanced'),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, max_depth=4,
                                                     learning_rate=0.05, random_state=42),
    'Logistic Regression': Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42))
    ]),
    'SVM': Pipeline([
        ('scaler', StandardScaler()),
        ('clf', SVC(C=1.0, kernel='rbf', probability=True, class_weight='balanced', random_state=42))
    ]),
}

results = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    
    # Validation metrics
    y_val_pred = model.predict(X_val)
    y_val_prob = model.predict_proba(X_val)[:, 1]
    
    bal_acc = balanced_accuracy_score(y_val, y_val_pred)
    acc     = accuracy_score(y_val, y_val_pred)
    f1      = f1_score(y_val, y_val_pred)
    auc     = roc_auc_score(y_val, y_val_prob)
    
    results[name] = {
        'model': model,
        'val_bal_acc': bal_acc,
        'val_acc': acc,
        'val_f1': f1,
        'val_auc': auc,
        'y_val_pred': y_val_pred,
        'y_val_prob': y_val_prob,
    }
    print(f"{name}: Bal.Acc={bal_acc:.4f}, Acc={acc:.4f}, F1={f1:.4f}, AUC={auc:.4f}")

# ── Best model on test set ────────────────────────────────────────────────────
best_name = max(results, key=lambda k: results[k]['val_bal_acc'])
best_model = results[best_name]['model']
print(f"\nBest model: {best_name}")

y_test_pred = best_model.predict(X_test)
y_test_prob = best_model.predict_proba(X_test)[:, 1]

test_bal_acc = balanced_accuracy_score(y_test, y_test_pred)
test_acc     = accuracy_score(y_test, y_test_pred)
test_f1      = f1_score(y_test, y_test_pred)
test_auc     = roc_auc_score(y_test, y_test_prob)

print(f"Test Balanced Accuracy: {test_bal_acc:.4f}")
print(f"Test Accuracy:          {test_acc:.4f}")
print(f"Test F1:                {test_f1:.4f}")
print(f"Test AUC:               {test_auc:.4f}")
print("\nClassification Report (Test):")
print(classification_report(y_test, y_test_pred, target_names=['Non-Variable', 'Variable']))

# Also evaluate all models on test
print("\nAll models on test set:")
for name, res in results.items():
    model = res['model']
    yp = model.predict(X_test)
    yprob = model.predict_proba(X_test)[:, 1]
    ba = balanced_accuracy_score(y_test, yp)
    au = roc_auc_score(y_test, yprob)
    results[name]['test_bal_acc'] = ba
    results[name]['test_auc'] = au
    results[name]['y_test_pred'] = yp
    results[name]['y_test_prob'] = yprob
    print(f"  {name}: Bal.Acc={ba:.4f}, AUC={au:.4f}")

# ── Feature Importance ───────────────────────────────────────────────────────
if hasattr(best_model, 'feature_importances_'):
    importances = best_model.feature_importances_
else:
    importances = best_model.named_steps['clf'].coef_[0]

feat_names = X_train.columns.tolist()
feat_imp = pd.Series(importances, index=feat_names).sort_values(ascending=False)
print("\nTop 15 features:")
print(feat_imp.head(15))

# ── Save outputs ─────────────────────────────────────────────────────────────
feat_imp.to_csv('outputs/feature_importances.csv')

test_preds = pd.DataFrame({
    'object_id': test['object_id'],
    'true_label': y_test,
    'pred_label': y_test_pred,
    'pred_prob': y_test_prob
})
test_preds.to_csv('outputs/test_predictions.csv', index=False)

# Save all model results
results_summary = pd.DataFrame([
    {'model': k, 'val_bal_acc': v['val_bal_acc'], 'val_auc': v['val_auc'],
     'test_bal_acc': v['test_bal_acc'], 'test_auc': v['test_auc']}
    for k, v in results.items()
])
results_summary.to_csv('outputs/model_comparison.csv', index=False)
print("\nResults summary:")
print(results_summary.to_string())

# ── Figures ───────────────────────────────────────────────────────────────────
print("\nGenerating figures...")

# ── Figure 1: Data Overview ───────────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(15, 9))
fig.suptitle('Variable Star Classification — Data Overview', fontsize=14, fontweight='bold')

# 1a: Label distribution
ax = axes[0, 0]
label_counts = train['label'].value_counts().sort_index()
ax.bar(['Non-Variable (0)', 'Variable (1)'], label_counts.values,
       color=['steelblue', 'tomato'], edgecolor='black', alpha=0.8)
ax.set_title('Training Set Label Distribution')
ax.set_ylabel('Count')
for i, v in enumerate(label_counts.values):
    ax.text(i, v + 2, str(v), ha='center', fontweight='bold')

# 1b: Example symbol series
ax = axes[0, 1]
example_var = train[train['label'] == 1]['symbol_series'].iloc[0]
example_nonvar = train[train['label'] == 0]['symbol_series'].iloc[0]
nums_var = series_to_numeric(example_var)
nums_nonvar = series_to_numeric(example_nonvar)
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
var_series = ''.join(train[train['label'] == 1]['symbol_series'].tolist())
non_series = ''.join(train[train['label'] == 0]['symbol_series'].tolist())
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

# 1d: Distribution of std by class
ax = axes[1, 0]
for label, color, name in [(0, 'steelblue', 'Non-Variable'), (1, 'tomato', 'Variable')]:
    subset = X_train[y_train == label]['std']
    ax.hist(subset, bins=20, alpha=0.6, color=color, label=name, edgecolor='black', linewidth=0.5)
ax.set_title('Distribution of Series Std Dev by Class')
ax.set_xlabel('Standard Deviation')
ax.set_ylabel('Count')
ax.legend()
ax.grid(True, alpha=0.3)

# 1e: Distribution of entropy by class
ax = axes[1, 1]
for label, color, name in [(0, 'steelblue', 'Non-Variable'), (1, 'tomato', 'Variable')]:
    subset = X_train[y_train == label]['entropy']
    ax.hist(subset, bins=20, alpha=0.6, color=color, label=name, edgecolor='black', linewidth=0.5)
ax.set_title('Distribution of Symbol Entropy by Class')
ax.set_xlabel('Entropy')
ax.set_ylabel('Count')
ax.legend()
ax.grid(True, alpha=0.3)

# 1f: Distribution of n_transitions by class
ax = axes[1, 2]
for label, color, name in [(0, 'steelblue', 'Non-Variable'), (1, 'tomato', 'Variable')]:
    subset = X_train[y_train == label]['n_transitions']
    ax.hist(subset, bins=20, alpha=0.6, color=color, label=name, edgecolor='black', linewidth=0.5)
ax.set_title('Distribution of Transitions by Class')
ax.set_xlabel('Number of Transitions')
ax.set_ylabel('Count')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig1_data_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1_data_overview.png")

# ── Figure 2: Model Comparison ────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Model Comparison', fontsize=14, fontweight='bold')

model_names = list(results.keys())
val_bal_accs  = [results[m]['val_bal_acc'] for m in model_names]
test_bal_accs = [results[m]['test_bal_acc'] for m in model_names]
val_aucs      = [results[m]['val_auc'] for m in model_names]
test_aucs     = [results[m]['test_auc'] for m in model_names]

# 2a: Balanced accuracy comparison
ax = axes[0]
x = np.arange(len(model_names))
width = 0.35
bars1 = ax.bar(x - width/2, val_bal_accs, width, label='Validation', color='steelblue', alpha=0.8)
bars2 = ax.bar(x + width/2, test_bal_accs, width, label='Test', color='tomato', alpha=0.8)
ax.axhline(0.78, color='green', linestyle='--', linewidth=2, label='Baseline (0.78)')
ax.set_title('Balanced Accuracy')
ax.set_ylabel('Balanced Accuracy')
ax.set_xticks(x)
ax.set_xticklabels([m.replace(' ', '\n') for m in model_names], fontsize=8)
ax.set_ylim(0.5, 1.0)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, axis='y')
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=7)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=7)

# 2b: AUC comparison
ax = axes[1]
bars1 = ax.bar(x - width/2, val_aucs, width, label='Validation', color='steelblue', alpha=0.8)
bars2 = ax.bar(x + width/2, test_aucs, width, label='Test', color='tomato', alpha=0.8)
ax.set_title('ROC-AUC')
ax.set_ylabel('AUC')
ax.set_xticks(x)
ax.set_xticklabels([m.replace(' ', '\n') for m in model_names], fontsize=8)
ax.set_ylim(0.5, 1.0)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, axis='y')
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=7)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=7)

# 2c: ROC curves for all models on test
ax = axes[2]
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['y_test_prob'])
    ax.plot(fpr, tpr, label=f"{name} (AUC={res['test_auc']:.3f})")
ax.plot([0, 1], [0, 1], 'k--', label='Random')
ax.set_title('ROC Curves (Test Set)')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig2_model_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_model_comparison.png")

# ── Figure 3: Feature Importance ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Feature Analysis', fontsize=14, fontweight='bold')

# 3a: Top feature importances
ax = axes[0]
top_n = 20
top_feats = feat_imp.head(top_n)
colors = ['tomato' if v > 0 else 'steelblue' for v in top_feats.values]
ax.barh(range(top_n), top_feats.values[::-1], color=colors[::-1], alpha=0.8, edgecolor='black', linewidth=0.5)
ax.set_yticks(range(top_n))
ax.set_yticklabels(top_feats.index[::-1], fontsize=9)
ax.set_title(f'Top {top_n} Feature Importances ({best_name})')
ax.set_xlabel('Importance')
ax.grid(True, alpha=0.3, axis='x')

# 3b: Confusion matrix for best model on test
ax = axes[1]
cm = confusion_matrix(y_test, y_test_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['Non-Variable', 'Variable'],
            yticklabels=['Non-Variable', 'Variable'])
ax.set_title(f'Confusion Matrix — {best_name}\n(Test Set, Bal.Acc={test_bal_acc:.3f})')
ax.set_xlabel('Predicted')
ax.set_ylabel('True')

plt.tight_layout()
plt.savefig('report/images/fig3_feature_importance.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3_feature_importance.png")

# ── Figure 4: Feature Distributions ──────────────────────────────────────────
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
fig.suptitle('Key Feature Distributions by Class', fontsize=14, fontweight='bold')

key_features = ['std', 'entropy', 'n_transitions', 'mean_abs_diff',
                'frac_high', 'range', 'iqr', 'n_large_jumps']

for idx, feat in enumerate(key_features):
    ax = axes[idx // 4, idx % 4]
    for label, color, name in [(0, 'steelblue', 'Non-Variable'), (1, 'tomato', 'Variable')]:
        vals = X_train[feat][y_train == label]
        ax.hist(vals, bins=20, alpha=0.6, color=color, label=name,
                edgecolor='black', linewidth=0.3, density=True)
    ax.set_title(feat, fontsize=10)
    ax.set_xlabel('Value')
    ax.set_ylabel('Density')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig4_feature_distributions.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig4_feature_distributions.png")

# ── Figure 5: Scatter plots of top features ───────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Feature Space Visualization', fontsize=14, fontweight='bold')

scatter_pairs = [('std', 'entropy'), ('mean_abs_diff', 'n_transitions'), ('frac_high', 'range')]
for idx, (fx, fy) in enumerate(scatter_pairs):
    ax = axes[idx]
    for label, color, name, marker in [(0, 'steelblue', 'Non-Variable', 'o'), (1, 'tomato', 'Variable', '^')]:
        mask = y_train == label
        ax.scatter(X_train[fx][mask], X_train[fy][mask],
                   c=color, alpha=0.4, s=20, label=name, marker=marker)
    ax.set_xlabel(fx)
    ax.set_ylabel(fy)
    ax.set_title(f'{fx} vs {fy}')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig5_feature_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig5_feature_scatter.png")

print("\n=== FINAL RESULTS ===")
print(f"Best model: {best_name}")
print(f"Test Balanced Accuracy: {test_bal_acc:.4f} (Baseline: 0.78)")
print(f"Test AUC: {test_auc:.4f}")
print(f"Test F1: {test_f1:.4f}")
print(f"Improvement over baseline: {test_bal_acc - 0.78:.4f}")
