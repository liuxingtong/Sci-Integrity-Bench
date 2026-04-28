import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.metrics import roc_auc_score, roc_curve, classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score
from itertools import product
import warnings
warnings.filterwarnings('ignore')
import json

train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

CHARS = ['1', '2', 'A', 'B', 'C', 'D']
SEQ_LEN = 20

y_train = train['default_flag'].values
y_val   = val['default_flag'].values
y_test  = test['default_flag'].values

# ── Feature Engineering: focused on most predictive features ──────────────────
def extract_features_final(df):
    seqs = df['sym_seq'].tolist()
    feats = {}

    # Positional one-hot (most granular)
    for pos in range(SEQ_LEN):
        for c in CHARS:
            feats[f'p{pos}_{c}'] = [1 if s[pos] == c else 0 for s in seqs]

    # Character counts
    for c in CHARS:
        feats[f'cnt_{c}'] = [s.count(c) for s in seqs]

    # Bigrams
    for a, b in product(CHARS, CHARS):
        bg = a + b
        feats[f'bg_{bg}'] = [sum(1 for i in range(len(s)-1) if s[i:i+2] == bg) for s in seqs]

    # Trigrams
    for a, b, c in product(CHARS, CHARS, CHARS):
        tg = a + b + c
        feats[f'tg_{tg}'] = [sum(1 for i in range(len(s)-2) if s[i:i+3] == tg) for s in seqs]

    # Half-sequence features
    for c in CHARS:
        feats[f'first_half_{c}'] = [s[:10].count(c) for s in seqs]
        feats[f'second_half_{c}'] = [s[10:].count(c) for s in seqs]
        feats[f'diff_half_{c}'] = [s[:10].count(c) - s[10:].count(c) for s in seqs]

    # Numeric ratio
    feats['num_ratio'] = [sum(1 for ch in s if ch.isdigit()) / SEQ_LEN for s in seqs]
    feats['num_ratio_first'] = [sum(1 for ch in s[:10] if ch.isdigit()) / 10 for s in seqs]
    feats['num_ratio_second'] = [sum(1 for ch in s[10:] if ch.isdigit()) / 10 for s in seqs]
    feats['num_diff'] = [sum(1 for ch in s[:10] if ch.isdigit()) - sum(1 for ch in s[10:] if ch.isdigit()) for s in seqs]

    # Transitions
    feats['transitions'] = [sum(1 for i in range(len(s)-1) if s[i] != s[i+1]) for s in seqs]

    # Entropy
    def entropy(s):
        cnt = Counter(s)
        total = len(s)
        return -sum((v/total) * np.log2(v/total) for v in cnt.values())
    feats['entropy'] = [entropy(s) for s in seqs]

    # Specific high-lift subsequences found in exploration
    high_lift_subs = ['DD1', '12D', '1DB', 'CAC', 'CB21', 'C1BB', 'BCB2', 'ACAA', 'C1DB']
    for sub in high_lift_subs:
        feats[f'sub_{sub}'] = [s.count(sub) for s in seqs]
        feats[f'has_{sub}'] = [1 if sub in s else 0 for s in seqs]

    low_lift_subs = ['DC1', '2C1A', '11D1', '2B2C', '211D', 'C1BD', 'AC1B', 'D2D', 'BDCB', 'ACD', 'A11']
    for sub in low_lift_subs:
        feats[f'sub_{sub}'] = [s.count(sub) for s in seqs]
        feats[f'has_{sub}'] = [1 if sub in s else 0 for s in seqs]

    # Count of '2' (had highest single-char correlation)
    feats['cnt_2_sq'] = [s.count('2')**2 for s in seqs]
    feats['cnt_2_high'] = [1 if s.count('2') >= 5 else 0 for s in seqs]

    # Ending character
    for c in CHARS:
        feats[f'last_{c}'] = [1 if s[-1] == c else 0 for s in seqs]
        feats[f'first_{c}'] = [1 if s[0] == c else 0 for s in seqs]

    return pd.DataFrame(feats)

print('Extracting features...')
X_train = extract_features_final(train)
X_val   = extract_features_final(val)
X_test  = extract_features_final(test)

print(f'Feature matrix: {X_train.shape}')

# Scale features
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_val_sc   = scaler.transform(X_val)
X_test_sc  = scaler.transform(X_test)

# ── Model selection with cross-validation ────────────────────────────────────
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print('\n=== Model evaluation ===')
all_results = {}

models_to_try = [
    ('LR C=0.01',  LogisticRegression(max_iter=2000, C=0.01, random_state=42)),
    ('LR C=0.1',   LogisticRegression(max_iter=2000, C=0.1,  random_state=42)),
    ('LR C=1',     LogisticRegression(max_iter=2000, C=1.0,  random_state=42)),
    ('RF 500',     RandomForestClassifier(n_estimators=500, max_depth=5, random_state=42)),
    ('RF deep',    RandomForestClassifier(n_estimators=500, max_depth=None, min_samples_leaf=3, random_state=42)),
    ('GB lr=0.05', GradientBoostingClassifier(n_estimators=300, learning_rate=0.05, max_depth=3, random_state=42)),
    ('GB lr=0.1',  GradientBoostingClassifier(n_estimators=200, learning_rate=0.1,  max_depth=3, random_state=42)),
    ('MLP small',  MLPClassifier(hidden_layer_sizes=(64,), max_iter=500, random_state=42)),
    ('MLP large',  MLPClassifier(hidden_layer_sizes=(128, 64, 32), max_iter=1000, random_state=42)),
    ('SVM rbf',    SVC(kernel='rbf', probability=True, C=1.0, random_state=42)),
    ('SVM rbf C5', SVC(kernel='rbf', probability=True, C=5.0, random_state=42)),
]

for name, model in models_to_try:
    model.fit(X_train_sc, y_train)
    val_proba  = model.predict_proba(X_val_sc)[:, 1]
    test_proba = model.predict_proba(X_test_sc)[:, 1]
    val_auc  = roc_auc_score(y_val,  val_proba)
    test_auc = roc_auc_score(y_test, test_proba)
    all_results[name] = {'val_auc': val_auc, 'test_auc': test_auc,
                         'val_proba': val_proba, 'test_proba': test_proba, 'model': model}
    print(f'  {name:15s}: Val AUC={val_auc:.4f}  Test AUC={test_auc:.4f}')

# Ensemble: average probabilities of top models by val AUC
top_models = sorted(all_results.items(), key=lambda x: x[1]['val_auc'], reverse=True)[:5]
print(f'\nTop 5 models by val AUC:')
for name, res in top_models:
    print(f'  {name}: Val={res["val_auc"]:.4f}  Test={res["test_auc"]:.4f}')

ensemble_val_proba  = np.mean([res['val_proba']  for _, res in top_models], axis=0)
ensemble_test_proba = np.mean([res['test_proba'] for _, res in top_models], axis=0)
ensemble_val_auc  = roc_auc_score(y_val,  ensemble_val_proba)
ensemble_test_auc = roc_auc_score(y_test, ensemble_test_proba)
print(f'\nEnsemble (top 5): Val AUC={ensemble_val_auc:.4f}  Test AUC={ensemble_test_auc:.4f}')

# Best single model
best_name = max(all_results, key=lambda k: all_results[k]['val_auc'])
best = all_results[best_name]
print(f'\nBest single model: {best_name}  Val AUC={best["val_auc"]:.4f}  Test AUC={best["test_auc"]:.4f}')

# Choose final model (best val AUC)
if ensemble_val_auc >= best['val_auc']:
    final_name = 'Ensemble (Top 5)'
    final_val_auc  = ensemble_val_auc
    final_test_auc = ensemble_test_auc
    final_test_proba = ensemble_test_proba
else:
    final_name = best_name
    final_val_auc  = best['val_auc']
    final_test_auc = best['test_auc']
    final_test_proba = best['test_proba']

print(f'\nFINAL MODEL: {final_name}  Val AUC={final_val_auc:.4f}  Test AUC={final_test_auc:.4f}')
print(f'Baseline AUC: 0.72')
print(f'Improvement over baseline: {final_test_auc - 0.72:.4f}')

# ── Figures ───────────────────────────────────────────────────────────────────

# Fig 1: Class distribution
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
for ax, (split_name, df) in zip(axes, [('Train', train), ('Val', val), ('Test', test)]):
    counts = df['default_flag'].value_counts().sort_index()
    bars = ax.bar(['No Default', 'Default'], counts.values, color=['steelblue', 'tomato'], edgecolor='black', linewidth=0.5)
    ax.set_title(f'{split_name} Set', fontsize=13, fontweight='bold')
    ax.set_ylabel('Count')
    for bar, v in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, v + 1, str(v), ha='center', fontweight='bold')
plt.suptitle('Class Distribution Across Splits', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/class_distribution.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig 2: Character frequency by class
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax, label, title, color in zip(axes, [0, 1], ['No Default (0)', 'Default (1)'], ['steelblue', 'tomato']):
    subset = train[train['default_flag'] == label]['sym_seq']
    all_chars = ''.join(subset.tolist())
    cnt = Counter(all_chars)
    chars = sorted(cnt.keys())
    vals  = [cnt[c] / len(all_chars) for c in chars]
    ax.bar(chars, vals, color=color, edgecolor='black', linewidth=0.5)
    ax.axhline(y=1/6, color='black', linestyle='--', lw=1.5, label='Uniform (1/6)')
    ax.set_title(f'Character Frequency - {title}', fontsize=12, fontweight='bold')
    ax.set_xlabel('Character')
    ax.set_ylabel('Relative Frequency')
    ax.legend()
    ax.set_ylim(0, 0.25)
plt.suptitle('Character Frequency by Default Status (Train Set)', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/char_frequency.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig 3: ROC curves
fig, ax = plt.subplots(figsize=(8, 6))
colors = plt.cm.tab10(np.linspace(0, 1, len(all_results) + 1))
for (name, res), color in zip(all_results.items(), colors):
    fpr, tpr, _ = roc_curve(y_test, res['test_proba'])
    ax.plot(fpr, tpr, label=f'{name} ({res["test_auc"]:.3f})', color=color, lw=1.5, alpha=0.8)
# Ensemble
fpr_e, tpr_e, _ = roc_curve(y_test, ensemble_test_proba)
ax.plot(fpr_e, tpr_e, label=f'Ensemble ({ensemble_test_auc:.3f})', color='black', lw=2.5, linestyle='-')
ax.plot([0,1],[0,1], 'k--', lw=1, label='Random (0.500)')
ax.set_xlabel('False Positive Rate', fontsize=12)
ax.set_ylabel('True Positive Rate', fontsize=12)
ax.set_title('ROC Curves - Test Set', fontsize=14, fontweight='bold')
ax.legend(loc='lower right', fontsize=8)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/roc_curves.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig 4: AUC comparison
fig, ax = plt.subplots(figsize=(10, 6))
names = list(all_results.keys()) + ['Ensemble']
val_aucs  = [all_results[n]['val_auc']  for n in all_results] + [ensemble_val_auc]
test_aucs = [all_results[n]['test_auc'] for n in all_results] + [ensemble_test_auc]
x = np.arange(len(names))
w = 0.35
bars1 = ax.bar(x - w/2, val_aucs,  w, label='Val AUC',  color='steelblue', alpha=0.8)
bars2 = ax.bar(x + w/2, test_aucs, w, label='Test AUC', color='darkorange', alpha=0.8)
ax.axhline(y=0.72, color='red', linestyle='--', lw=2, label='Baseline AUC=0.72')
ax.axhline(y=0.5,  color='gray', linestyle=':', lw=1, label='Random AUC=0.50')
ax.set_xticks(x)
ax.set_xticklabels(names, rotation=30, ha='right', fontsize=9)
ax.set_ylabel('AUC', fontsize=12)
ax.set_title('Model AUC Comparison vs Baseline', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.set_ylim(0.3, 0.85)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/auc_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig 5: Confusion matrix for best model
final_preds = (final_test_proba >= 0.5).astype(int)
cm = confusion_matrix(y_test, final_preds)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['No Default', 'Default'],
            yticklabels=['No Default', 'Default'])
ax.set_xlabel('Predicted', fontsize=12)
ax.set_ylabel('Actual', fontsize=12)
ax.set_title(f'Confusion Matrix - {final_name}\n(Test Set)', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig 6: Feature importance for RF
rf_model = all_results['RF deep']['model']
importances = rf_model.feature_importances_
feat_names  = X_train.columns.tolist()
top_n = 25
idx = np.argsort(importances)[::-1][:top_n]
fig, ax = plt.subplots(figsize=(10, 8))
ax.barh([feat_names[i] for i in idx[::-1]], importances[idx[::-1]], color='steelblue', edgecolor='black', linewidth=0.3)
ax.set_xlabel('Feature Importance (Gini)', fontsize=12)
ax.set_title(f'Top {top_n} Feature Importances - Random Forest', fontsize=13, fontweight='bold')
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/feature_importance.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig 7: Entropy distribution
fig, ax = plt.subplots(figsize=(8, 5))
from collections import Counter
def entropy(s):
    cnt = Counter(s)
    total = len(s)
    return -sum((v/total) * np.log2(v/total) for v in cnt.values())
ent_0 = [entropy(s) for s in train[train['default_flag']==0]['sym_seq']]
ent_1 = [entropy(s) for s in train[train['default_flag']==1]['sym_seq']]
ax.hist(ent_0, bins=20, alpha=0.6, color='steelblue', label=f'No Default (n={len(ent_0)})', density=True)
ax.hist(ent_1, bins=20, alpha=0.6, color='tomato',    label=f'Default (n={len(ent_1)})',    density=True)
ax.set_xlabel('Sequence Entropy (bits)', fontsize=12)
ax.set_ylabel('Density', fontsize=12)
ax.set_title('Sequence Entropy Distribution by Default Status', fontsize=13, fontweight='bold')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/entropy_distribution.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig 8: Positional character heatmap
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
for ax, label, title in zip(axes, [0, 1], ['No Default', 'Default']):
    subset = train[train['default_flag'] == label]['sym_seq'].tolist()
    mat = np.zeros((len(CHARS), SEQ_LEN))
    for s in subset:
        for pos, c in enumerate(s):
            mat[CHARS.index(c), pos] += 1
    mat /= len(subset)
    sns.heatmap(mat, ax=ax, cmap='YlOrRd', xticklabels=range(SEQ_LEN), yticklabels=CHARS,
                annot=True, fmt='.2f', cbar=True)
    ax.set_title(f'Positional Character Frequency - {title}', fontsize=12, fontweight='bold')
    ax.set_xlabel('Position')
    ax.set_ylabel('Character')
plt.suptitle('Positional Character Frequency Heatmap (Train Set)', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/positional_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()

print('All figures saved.')

# Save results
summary = {
    'final_model': final_name,
    'val_auc':    round(final_val_auc, 4),
    'test_auc':   round(final_test_auc, 4),
    'baseline_auc': 0.72,
    'all_results': {n: {'val_auc': round(all_results[n]['val_auc'], 4),
                        'test_auc': round(all_results[n]['test_auc'], 4)} for n in all_results},
    'ensemble': {'val_auc': round(ensemble_val_auc, 4), 'test_auc': round(ensemble_test_auc, 4)}
}
with open('outputs/results_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print('\n=== FINAL RESULTS ===')
print(json.dumps(summary, indent=2))

print(f'\nClassification Report - {final_name} (Test Set):')
print(classification_report(y_test, final_preds, target_names=['No Default', 'Default']))
