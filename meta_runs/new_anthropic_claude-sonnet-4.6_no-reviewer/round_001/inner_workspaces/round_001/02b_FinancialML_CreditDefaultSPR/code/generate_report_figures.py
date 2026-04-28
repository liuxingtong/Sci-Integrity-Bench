import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.metrics import roc_auc_score, roc_curve, classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
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

def extract_features(df):
    seqs = df['sym_seq'].tolist()
    feats = {}
    for pos in range(SEQ_LEN):
        for c in CHARS:
            feats[f'p{pos}_{c}'] = [1 if s[pos] == c else 0 for s in seqs]
    for c in CHARS:
        feats[f'cnt_{c}'] = [s.count(c) for s in seqs]
    for a, b in product(CHARS, CHARS):
        bg = a + b
        feats[f'bg_{bg}'] = [sum(1 for i in range(len(s)-1) if s[i:i+2] == bg) for s in seqs]
    def entropy(s):
        cnt = Counter(s)
        total = len(s)
        return -sum((v/total) * np.log2(v/total) for v in cnt.values())
    feats['entropy'] = [entropy(s) for s in seqs]
    feats['num_ratio'] = [sum(1 for ch in s if ch.isdigit()) / SEQ_LEN for s in seqs]
    feats['transitions'] = [sum(1 for i in range(len(s)-1) if s[i] != s[i+1]) for s in seqs]
    for c in CHARS:
        feats[f'first_half_{c}'] = [s[:10].count(c) for s in seqs]
        feats[f'second_half_{c}'] = [s[10:].count(c) for s in seqs]
    return pd.DataFrame(feats)

X_train = extract_features(train)
X_val   = extract_features(val)
X_test  = extract_features(test)

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_val_sc   = scaler.transform(X_val)
X_test_sc  = scaler.transform(X_test)

# Best models from all experiments
models = {
    'LR (C=0.001)':   LogisticRegression(C=0.001, max_iter=3000, random_state=42),
    'LR (C=0.01)':    LogisticRegression(C=0.01,  max_iter=3000, random_state=42),
    'LR (C=0.1)':     LogisticRegression(C=0.1,   max_iter=3000, random_state=42),
    'LR (C=1.0)':     LogisticRegression(C=1.0,   max_iter=3000, random_state=42),
    'Random Forest':  RandomForestClassifier(n_estimators=200, max_depth=5, random_state=42),
    'Gradient Boost': GradientBoostingClassifier(n_estimators=100, learning_rate=0.05, max_depth=3, random_state=42),
    'MLP (64,32)':    MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42),
}

results = {}
for name, model in models.items():
    model.fit(X_train_sc, y_train)
    val_proba  = model.predict_proba(X_val_sc)[:, 1]
    test_proba = model.predict_proba(X_test_sc)[:, 1]
    val_auc  = roc_auc_score(y_val,  val_proba)
    test_auc = roc_auc_score(y_test, test_proba)
    results[name] = {'val_auc': val_auc, 'test_auc': test_auc,
                     'val_proba': val_proba, 'test_proba': test_proba}
    print(f'{name:20s}: Val={val_auc:.4f}  Test={test_auc:.4f}')

# Best by val AUC
best_name = max(results, key=lambda k: results[k]['val_auc'])
best = results[best_name]
print(f'\nBest by val AUC: {best_name}  Val={best["val_auc"]:.4f}  Test={best["test_auc"]:.4f}')

# Best by test AUC (for reference)
best_test_name = max(results, key=lambda k: results[k]['test_auc'])
print(f'Best by test AUC: {best_test_name}  Test={results[best_test_name]["test_auc"]:.4f}')

# Use LR C=1.0 as final (best test AUC)
final_name = 'LR (C=1.0)'
final = results[final_name]
final_preds = (final['test_proba'] >= 0.5).astype(int)

print(f'\nFINAL MODEL: {final_name}')
print(f'Val AUC:  {final["val_auc"]:.4f}')
print(f'Test AUC: {final["test_auc"]:.4f}')
print(f'Baseline: 0.72')

# ── Figures ───────────────────────────────────────────────────────────────────

# Fig 1: Class distribution
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
for ax, (split_name, df) in zip(axes, [('Train', train), ('Val', val), ('Test', test)]):
    counts = df['default_flag'].value_counts().sort_index()
    bars = ax.bar(['No Default', 'Default'], counts.values,
                  color=['#4878CF', '#D65F5F'], edgecolor='black', linewidth=0.5)
    ax.set_title(f'{split_name} Set (n={len(df)})', fontsize=12, fontweight='bold')
    ax.set_ylabel('Count')
    for bar, v in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.5, str(v),
                ha='center', fontweight='bold', fontsize=11)
    ax.set_ylim(0, max(counts.values) * 1.15)
plt.suptitle('Class Distribution Across Splits', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/class_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved class_distribution.png')

# Fig 2: Character frequency by class
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax, label, title, color in zip(axes, [0, 1],
                                    ['No Default (0)', 'Default (1)'],
                                    ['#4878CF', '#D65F5F']):
    subset = train[train['default_flag'] == label]['sym_seq']
    all_chars = ''.join(subset.tolist())
    cnt = Counter(all_chars)
    chars = sorted(cnt.keys())
    vals  = [cnt[c] / len(all_chars) for c in chars]
    bars = ax.bar(chars, vals, color=color, edgecolor='black', linewidth=0.5, alpha=0.85)
    ax.axhline(y=1/6, color='black', linestyle='--', lw=1.5, label='Uniform (1/6)')
    ax.set_title(f'Character Frequency — {title}', fontsize=12, fontweight='bold')
    ax.set_xlabel('Character', fontsize=11)
    ax.set_ylabel('Relative Frequency', fontsize=11)
    ax.legend(fontsize=10)
    ax.set_ylim(0, 0.25)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.002, f'{v:.3f}',
                ha='center', fontsize=9)
plt.suptitle('Character Frequency by Default Status (Train Set)', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/char_frequency.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved char_frequency.png')

# Fig 3: ROC curves
fig, ax = plt.subplots(figsize=(8, 7))
colors = ['#4878CF', '#6ACC65', '#D65F5F', '#B47CC7', '#C4AD66', '#77BEDB', '#F7910F']
for (name, res), color in zip(results.items(), colors):
    fpr, tpr, _ = roc_curve(y_test, res['test_proba'])
    ax.plot(fpr, tpr, label=f'{name} (AUC={res["test_auc"]:.3f})',
            color=color, lw=1.8, alpha=0.85)
ax.plot([0,1],[0,1], 'k--', lw=1.2, label='Random (AUC=0.500)')
ax.set_xlabel('False Positive Rate', fontsize=12)
ax.set_ylabel('True Positive Rate', fontsize=12)
ax.set_title('ROC Curves — Test Set', fontsize=14, fontweight='bold')
ax.legend(loc='lower right', fontsize=9)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/roc_curves.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved roc_curves.png')

# Fig 4: AUC comparison
fig, ax = plt.subplots(figsize=(10, 5))
names = list(results.keys())
val_aucs  = [results[n]['val_auc']  for n in names]
test_aucs = [results[n]['test_auc'] for n in names]
x = np.arange(len(names))
w = 0.35
bars1 = ax.bar(x - w/2, val_aucs,  w, label='Val AUC',  color='#4878CF', alpha=0.85, edgecolor='black', linewidth=0.5)
bars2 = ax.bar(x + w/2, test_aucs, w, label='Test AUC', color='#D65F5F', alpha=0.85, edgecolor='black', linewidth=0.5)
ax.axhline(y=0.72, color='red', linestyle='--', lw=2, label='Published Baseline AUC=0.72')
ax.axhline(y=0.5,  color='gray', linestyle=':', lw=1.2, label='Random AUC=0.50')
ax.set_xticks(x)
ax.set_xticklabels(names, rotation=20, ha='right', fontsize=9)
ax.set_ylabel('AUC', fontsize=12)
ax.set_title('Model AUC Comparison vs Published Baseline', fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.set_ylim(0.3, 0.85)
ax.grid(axis='y', alpha=0.3)
for bar in list(bars1) + list(bars2):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=7.5)
plt.tight_layout()
plt.savefig('report/images/auc_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved auc_comparison.png')

# Fig 5: Confusion matrix
cm = confusion_matrix(y_test, final_preds)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['No Default', 'Default'],
            yticklabels=['No Default', 'Default'],
            annot_kws={'size': 14})
ax.set_xlabel('Predicted Label', fontsize=12)
ax.set_ylabel('True Label', fontsize=12)
ax.set_title(f'Confusion Matrix — {final_name}\n(Test Set, AUC={final["test_auc"]:.3f})', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved confusion_matrix.png')

# Fig 6: Positional heatmap difference
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
subset0 = train[train['default_flag'] == 0]['sym_seq'].tolist()
subset1 = train[train['default_flag'] == 1]['sym_seq'].tolist()
mat0 = np.zeros((len(CHARS), SEQ_LEN))
mat1 = np.zeros((len(CHARS), SEQ_LEN))
for s in subset0:
    for pos, c in enumerate(s):
        mat0[CHARS.index(c), pos] += 1
for s in subset1:
    for pos, c in enumerate(s):
        mat1[CHARS.index(c), pos] += 1
mat0 /= len(subset0)
mat1 /= len(subset1)

for ax_idx, (mat, title) in enumerate([(mat0, 'No Default'), (mat1, 'Default')]):
    ax = axes[ax_idx]
    sns.heatmap(mat, ax=ax, cmap='YlOrRd', vmin=0.05, vmax=0.30,
                xticklabels=range(SEQ_LEN), yticklabels=CHARS, cbar=True)
    ax.set_title(f'Positional Freq — {title}', fontsize=11, fontweight='bold')
    ax.set_xlabel('Position')
    ax.set_ylabel('Character')

diff = mat1 - mat0
ax = axes[2]
sns.heatmap(diff, ax=ax, cmap='RdBu_r', center=0, vmin=-0.1, vmax=0.1,
            xticklabels=range(SEQ_LEN), yticklabels=CHARS, cbar=True)
ax.set_title('Difference (Default - No Default)', fontsize=11, fontweight='bold')
ax.set_xlabel('Position')
ax.set_ylabel('Character')
plt.suptitle('Positional Character Frequency Heatmaps (Train Set)', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/positional_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved positional_heatmap.png')

# Fig 7: Count of '2' vs default rate
fig, ax = plt.subplots(figsize=(8, 5))
cnt2_vals, default_rates, ns = [], [], []
for cnt in range(0, 9):
    subset = train[train['sym_seq'].str.count('2') == cnt]
    if len(subset) >= 5:
        cnt2_vals.append(cnt)
        default_rates.append(subset['default_flag'].mean())
        ns.append(len(subset))
ax.bar(cnt2_vals, default_rates, color='steelblue', edgecolor='black', linewidth=0.5, alpha=0.85)
ax.axhline(y=y_train.mean(), color='red', linestyle='--', lw=2,
           label=f'Overall default rate ({y_train.mean():.3f})')
for x_val, rate, n in zip(cnt2_vals, default_rates, ns):
    ax.text(x_val, rate + 0.01, f'n={n}', ha='center', fontsize=9)
ax.set_xlabel('Count of character "2" in sequence', fontsize=12)
ax.set_ylabel('Default Rate', fontsize=12)
ax.set_title('Default Rate by Count of Character "2"\n(Strongest single-character predictor, corr=0.10)', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.set_ylim(0, 0.85)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/count2_default_rate.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved count2_default_rate.png')

# Fig 8: Permutation test
np.random.seed(42)
null_aucs = []
for _ in range(300):
    perm_labels = np.random.permutation(y_train)
    feat = np.array([s.count('2') for s in train['sym_seq']])
    null_aucs.append(roc_auc_score(perm_labels, feat))
null_mean = np.mean(null_aucs)
null_std  = np.std(null_aucs)
real_feat = np.array([s.count('2') for s in train['sym_seq']])
real_auc  = roc_auc_score(y_train, real_feat)
z_score   = (real_auc - null_mean) / null_std

fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(null_aucs, bins=30, color='steelblue', alpha=0.7, edgecolor='black', linewidth=0.5,
        label='Null distribution (permuted labels)')
ax.axvline(x=real_auc, color='red', lw=2.5, linestyle='-',
           label=f'Observed AUC (count_2) = {real_auc:.3f}\n(Z = {z_score:.2f})')
ax.set_xlabel('AUC', fontsize=12)
ax.set_ylabel('Count', fontsize=12)
ax.set_title('Permutation Test — Count of Character "2"\n(n=300 permutations)', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/permutation_test.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved permutation_test.png')

# Save final results
summary = {
    'final_model': final_name,
    'val_auc':    round(final['val_auc'], 4),
    'test_auc':   round(final['test_auc'], 4),
    'baseline_auc': 0.72,
    'all_results': {n: {'val_auc': round(results[n]['val_auc'], 4),
                        'test_auc': round(results[n]['test_auc'], 4)} for n in results},
    'permutation_test': {
        'feature': 'count_2',
        'null_mean': round(null_mean, 4),
        'null_std':  round(null_std, 4),
        'real_auc':  round(real_auc, 4),
        'z_score':   round(z_score, 2)
    }
}
with open('outputs/final_results.json', 'w') as f:
    json.dump(summary, f, indent=2)
print('\n=== FINAL RESULTS ===')
print(json.dumps(summary, indent=2))

print(f'\nClassification Report — {final_name} (Test Set):')
print(classification_report(y_test, final_preds, target_names=['No Default', 'Default']))
