import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, roc_curve, classification_report, confusion_matrix
from collections import Counter
import warnings
warnings.filterwarnings('ignore')
import json
import os

# Load data
train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

print(f'Train: {train.shape}, Val: {val.shape}, Test: {test.shape}')
print(f'Default rates - Train: {train["default_flag"].mean():.3f}, Val: {val["default_flag"].mean():.3f}, Test: {test["default_flag"].mean():.3f}')

CHARS = ['1', '2', 'A', 'B', 'C', 'D']
SEQ_LEN = 20

def extract_features(df):
    seqs = df['sym_seq'].tolist()
    feats = {}

    # Character frequency counts
    for c in CHARS:
        feats[f'cnt_{c}'] = [s.count(c) for s in seqs]

    # Character frequency ratios
    for c in CHARS:
        feats[f'freq_{c}'] = [s.count(c) / SEQ_LEN for s in seqs]

    # Positional one-hot encoding
    for pos in range(SEQ_LEN):
        for c in CHARS:
            feats[f'pos{pos}_{c}'] = [1 if s[pos] == c else 0 for s in seqs]

    # Bigram counts
    bigrams = [f'{a}{b}' for a in CHARS for b in CHARS]
    for bg in bigrams:
        feats[f'bg_{bg}'] = [sum(1 for i in range(len(s)-1) if s[i:i+2] == bg) for s in seqs]

    # Trigram counts
    trigrams = [f'{a}{b}{c}' for a in CHARS for b in CHARS for c in CHARS]
    for tg in trigrams:
        feats[f'tg_{tg}'] = [sum(1 for i in range(len(s)-2) if s[i:i+3] == tg) for s in seqs]

    # Max run length
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

    # Number of unique characters
    feats['n_unique'] = [len(set(s)) for s in seqs]

    # Entropy
    def entropy(s):
        cnt = Counter(s)
        total = len(s)
        return -sum((v/total) * np.log2(v/total) for v in cnt.values())
    feats['entropy'] = [entropy(s) for s in seqs]

    # First and last character one-hot
    for c in CHARS:
        feats[f'first_{c}'] = [1 if s[0] == c else 0 for s in seqs]
        feats[f'last_{c}']  = [1 if s[-1] == c else 0 for s in seqs]

    # Numeric vs alpha ratio
    feats['num_ratio']   = [sum(1 for ch in s if ch.isdigit()) / SEQ_LEN for s in seqs]
    feats['alpha_ratio'] = [sum(1 for ch in s if ch.isalpha()) / SEQ_LEN for s in seqs]

    # Transitions
    feats['transitions'] = [sum(1 for i in range(len(s)-1) if s[i] != s[i+1]) for s in seqs]

    return pd.DataFrame(feats)

X_train = extract_features(train)
X_val   = extract_features(val)
X_test  = extract_features(test)

y_train = train['default_flag'].values
y_val   = val['default_flag'].values
y_test  = test['default_flag'].values

print(f'Feature matrix shape: {X_train.shape}')

# Train models
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, C=1.0, random_state=42),
    'Random Forest':       RandomForestClassifier(n_estimators=300, max_depth=None, random_state=42),
    'Gradient Boosting':   GradientBoostingClassifier(n_estimators=300, learning_rate=0.05, max_depth=4, random_state=42),
}

results = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    val_proba  = model.predict_proba(X_val)[:, 1]
    test_proba = model.predict_proba(X_test)[:, 1]
    val_auc  = roc_auc_score(y_val,  val_proba)
    test_auc = roc_auc_score(y_test, test_proba)
    results[name] = {
        'model': model,
        'val_auc':  val_auc,
        'test_auc': test_auc,
        'val_proba':  val_proba,
        'test_proba': test_proba,
    }
    print(f'{name:30s}  Val AUC={val_auc:.4f}  Test AUC={test_auc:.4f}')

best_name = max(results, key=lambda k: results[k]['val_auc'])
best = results[best_name]
print(f'\nBest model: {best_name}  Val AUC={best["val_auc"]:.4f}  Test AUC={best["test_auc"]:.4f}')

# Fig 1: Class distribution
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
for ax, (split_name, df) in zip(axes, [('Train', train), ('Val', val), ('Test', test)]):
    counts = df['default_flag'].value_counts().sort_index()
    ax.bar(['No Default', 'Default'], counts.values, color=['steelblue', 'tomato'])
    ax.set_title(f'{split_name} Set')
    ax.set_ylabel('Count')
    for i, v in enumerate(counts.values):
        ax.text(i, v + 1, str(v), ha='center', fontweight='bold')
plt.suptitle('Class Distribution Across Splits', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/class_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved class_distribution.png')

# Fig 2: Character frequency by class
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax, label, title in zip(axes, [0, 1], ['No Default (0)', 'Default (1)']):
    subset = train[train['default_flag'] == label]['sym_seq']
    all_chars = ''.join(subset.tolist())
    cnt = Counter(all_chars)
    chars = sorted(cnt.keys())
    vals  = [cnt[c] / len(all_chars) for c in chars]
    ax.bar(chars, vals, color='steelblue' if label == 0 else 'tomato')
    ax.set_title(f'Character Frequency - {title}')
    ax.set_xlabel('Character')
    ax.set_ylabel('Relative Frequency')
plt.suptitle('Character Frequency by Default Status (Train Set)', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/char_frequency.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved char_frequency.png')

# Fig 3: ROC curves
fig, ax = plt.subplots(figsize=(8, 6))
colors = ['steelblue', 'darkorange', 'green']
for (name, res), color in zip(results.items(), colors):
    fpr, tpr, _ = roc_curve(y_test, res['test_proba'])
    ax.plot(fpr, tpr, label=f'{name} (AUC={res["test_auc"]:.4f})', color=color, lw=2)
ax.plot([0,1],[0,1], 'k--', lw=1, label='Random (AUC=0.50)')
ax.set_xlabel('False Positive Rate', fontsize=12)
ax.set_ylabel('True Positive Rate', fontsize=12)
ax.set_title('ROC Curves - Test Set', fontsize=14, fontweight='bold')
ax.legend(loc='lower right', fontsize=10)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/roc_curves.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved roc_curves.png')

# Fig 4: Feature importance
best_model = best['model']
if hasattr(best_model, 'feature_importances_'):
    importances = best_model.feature_importances_
    feat_names  = X_train.columns.tolist()
    top_n = 20
    idx = np.argsort(importances)[::-1][:top_n]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh([feat_names[i] for i in idx[::-1]], importances[idx[::-1]], color='steelblue')
    ax.set_xlabel('Feature Importance', fontsize=12)
    ax.set_title(f'Top {top_n} Feature Importances - {best_name}', fontsize=13, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/feature_importance.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved feature_importance.png')

# Fig 5: AUC comparison
fig, ax = plt.subplots(figsize=(8, 5))
names = list(results.keys())
val_aucs  = [results[n]['val_auc']  for n in names]
test_aucs = [results[n]['test_auc'] for n in names]
x = np.arange(len(names))
w = 0.35
bars1 = ax.bar(x - w/2, val_aucs,  w, label='Val AUC',  color='steelblue')
bars2 = ax.bar(x + w/2, test_aucs, w, label='Test AUC', color='darkorange')
ax.axhline(y=0.72, color='red', linestyle='--', lw=1.5, label='Baseline AUC=0.72')
ax.set_xticks(x)
ax.set_xticklabels(names, rotation=15, ha='right')
ax.set_ylabel('AUC', fontsize=12)
ax.set_title('Model AUC Comparison', fontsize=14, fontweight='bold')
ax.legend()
ax.set_ylim(0.5, 1.0)
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005, f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=9)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005, f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=9)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/auc_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved auc_comparison.png')

# Fig 6: Confusion matrix
best_preds = (best['test_proba'] >= 0.5).astype(int)
cm = confusion_matrix(y_test, best_preds)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['No Default', 'Default'],
            yticklabels=['No Default', 'Default'])
ax.set_xlabel('Predicted', fontsize=12)
ax.set_ylabel('Actual', fontsize=12)
ax.set_title(f'Confusion Matrix - {best_name} (Test Set)', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved confusion_matrix.png')

# Fig 7: Entropy distribution
fig, ax = plt.subplots(figsize=(8, 5))
ent_0 = X_train.loc[y_train == 0, 'entropy']
ent_1 = X_train.loc[y_train == 1, 'entropy']
ax.hist(ent_0, bins=20, alpha=0.6, color='steelblue', label='No Default', density=True)
ax.hist(ent_1, bins=20, alpha=0.6, color='tomato',    label='Default',    density=True)
ax.set_xlabel('Sequence Entropy', fontsize=12)
ax.set_ylabel('Density', fontsize=12)
ax.set_title('Sequence Entropy Distribution by Default Status', fontsize=13, fontweight='bold')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/entropy_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved entropy_distribution.png')

# Save results
summary = {
    'best_model': best_name,
    'val_auc':    round(best['val_auc'], 4),
    'test_auc':   round(best['test_auc'], 4),
    'baseline_auc': 0.72,
    'all_results': {n: {'val_auc': round(results[n]['val_auc'], 4),
                        'test_auc': round(results[n]['test_auc'], 4)} for n in results}
}
with open('outputs/results_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)
print('\nSaved results_summary.json')
print('\n=== FINAL SUMMARY ===')
print(json.dumps(summary, indent=2))

print(f'\nClassification Report - {best_name} (Test Set):')
print(classification_report(y_test, best_preds, target_names=['No Default', 'Default']))
