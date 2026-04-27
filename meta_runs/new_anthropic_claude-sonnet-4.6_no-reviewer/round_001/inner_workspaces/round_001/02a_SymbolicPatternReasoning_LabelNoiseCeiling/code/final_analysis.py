import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_selection import mutual_info_classif
import warnings
warnings.filterwarnings('ignore')
import json

np.random.seed(42)

train = pd.read_csv('data/spr_bench_train.csv')
val   = pd.read_csv('data/spr_bench_val.csv')
test  = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']

# ─── Feature Engineering ─────────────────────────────────────────────────────
enc_ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
X_train_ohe = enc_ohe.fit_transform(train[feature_cols])
X_val_ohe   = enc_ohe.transform(val[feature_cols])
X_test_ohe  = enc_ohe.transform(test[feature_cols])

enc_ord = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
X_train_ord = enc_ord.fit_transform(train[feature_cols])
X_val_ord   = enc_ord.transform(val[feature_cols])
X_test_ord  = enc_ord.transform(test[feature_cols])

y_train = train['label'].values
y_val   = val['label'].values
y_test  = test['label'].values

# ─── Main Models ─────────────────────────────────────────────────────────────
models = {
    'Logistic Regression': (LogisticRegression(max_iter=1000, C=1.0, random_state=42), 'ohe'),
    'Decision Tree':       (DecisionTreeClassifier(max_depth=10, random_state=42), 'ord'),
    'Random Forest':       (RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1), 'ord'),
    'Gradient Boosting':   (GradientBoostingClassifier(n_estimators=200, max_depth=5, random_state=42), 'ord'),
    'SVM (RBF)':           (SVC(kernel='rbf', C=10, gamma='scale', random_state=42), 'ohe'),
    'KNN':                 (KNeighborsClassifier(n_neighbors=5), 'ohe'),
    'MLP':                 (MLPClassifier(hidden_layer_sizes=(256, 128, 64), max_iter=500, random_state=42), 'ohe'),
}

results = {}
for name, (model, enc_type) in models.items():
    Xtr = X_train_ohe if enc_type == 'ohe' else X_train_ord
    Xv  = X_val_ohe   if enc_type == 'ohe' else X_val_ord
    Xte = X_test_ohe  if enc_type == 'ohe' else X_test_ord
    model.fit(Xtr, y_train)
    results[name] = {
        'train_acc': accuracy_score(y_train, model.predict(Xtr)),
        'val_acc':   accuracy_score(y_val,   model.predict(Xv)),
        'test_acc':  accuracy_score(y_test,  model.predict(Xte)),
    }
    print(f'{name}: train={results[name]["train_acc"]:.4f}, val={results[name]["val_acc"]:.4f}, test={results[name]["test_acc"]:.4f}')

# Best model
best_name = max(results, key=lambda k: results[k]['val_acc'])
best_model, best_enc = models[best_name]
Xte_best = X_test_ohe if best_enc == 'ohe' else X_test_ord
test_pred_best = best_model.predict(Xte_best)

print(f'\nBest model: {best_name}')
print(classification_report(y_test, test_pred_best, target_names=['reject', 'accept']))

# ─── Noise Ceiling Bootstrap ──────────────────────────────────────────────────
print('\nBootstrap noise ceiling...')
noise_estimates = []
for seed in range(50):
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(train))
    half = len(train) // 2
    idx1, idx2 = idx[:half], idx[half:]
    rf = RandomForestClassifier(n_estimators=100, random_state=seed, n_jobs=-1)
    rf.fit(X_train_ord[idx1], y_train[idx1])
    acc = accuracy_score(y_train[idx2], rf.predict(X_train_ord[idx2]))
    noise_estimates.append(acc)
noise_mean = np.mean(noise_estimates)
noise_std  = np.std(noise_estimates)
print(f'Noise ceiling: {noise_mean:.4f} +/- {noise_std:.4f}')

# ─── Overfitting analysis ─────────────────────────────────────────────────────
print('\nOverfitting analysis (train size vs val acc)...')
train_sizes = [100, 200, 500, 1000, 1500, 2000]
lr_train_accs = []
lr_val_accs   = []
rf_train_accs = []
rf_val_accs   = []

for n in train_sizes:
    idx = np.random.choice(len(train), n, replace=False)
    Xtr_sub = X_train_ohe[idx]
    ytr_sub = y_train[idx]
    
    lr = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
    lr.fit(Xtr_sub, ytr_sub)
    lr_train_accs.append(accuracy_score(ytr_sub, lr.predict(Xtr_sub)))
    lr_val_accs.append(accuracy_score(y_val, lr.predict(X_val_ohe)))
    
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train_ord[idx], ytr_sub)
    rf_train_accs.append(accuracy_score(ytr_sub, rf.predict(X_train_ord[idx])))
    rf_val_accs.append(accuracy_score(y_val, rf.predict(X_val_ord)))

# ─── Save results ─────────────────────────────────────────────────────────────
final_results = {
    'models': results,
    'best_model': best_name,
    'noise_ceiling_mean': noise_mean,
    'noise_ceiling_std': noise_std,
    'sota': 0.70,
    'random_baseline': 0.50,
}
with open('outputs/final_results.json', 'w') as f:
    json.dump(final_results, f, indent=2)

# ─── Figure 1: Main accuracy comparison ──────────────────────────────────────
model_names = list(results.keys())
train_accs = [results[m]['train_acc'] for m in model_names]
val_accs   = [results[m]['val_acc']   for m in model_names]
test_accs  = [results[m]['test_acc']  for m in model_names]

fig, ax = plt.subplots(figsize=(13, 6))
x = np.arange(len(model_names))
width = 0.25
ax.bar(x - width, train_accs, width, label='Train', color='steelblue', alpha=0.85)
ax.bar(x,         val_accs,   width, label='Val',   color='darkorange', alpha=0.85)
ax.bar(x + width, test_accs,  width, label='Test',  color='seagreen', alpha=0.85)
ax.axhline(y=0.70, color='red',    linestyle='--', linewidth=2.0, label='SOTA (70%)')
ax.axhline(y=0.50, color='gray',   linestyle=':',  linewidth=1.5, label='Random (50%)')
ax.axhline(y=noise_mean, color='purple', linestyle='-.', linewidth=1.5, label=f'Noise Ceiling ({noise_mean:.2f})')
ax.set_xlabel('Model', fontsize=12)
ax.set_ylabel('Accuracy', fontsize=12)
ax.set_title('SPR_BENCH: Model Accuracy vs SOTA and Noise Ceiling', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(model_names, rotation=30, ha='right', fontsize=10)
ax.set_ylim(0.3, 1.1)
ax.legend(fontsize=10, loc='upper right')
ax.grid(axis='y', alpha=0.3)
for i, bar in enumerate(ax.patches[14:21]):  # test bars
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., h + 0.005, f'{h:.3f}', ha='center', va='bottom', fontsize=8)
plt.tight_layout()
plt.savefig('report/images/accuracy_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved accuracy_comparison.png')

# ─── Figure 2: Confusion matrix ───────────────────────────────────────────────
cm = confusion_matrix(y_test, test_pred_best)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['reject (0)', 'accept (1)'],
            yticklabels=['reject (0)', 'accept (1)'])
ax.set_xlabel('Predicted', fontsize=12)
ax.set_ylabel('True', fontsize=12)
ax.set_title(f'Confusion Matrix\n{best_name} (Test Set)', fontsize=13)
plt.tight_layout()
plt.savefig('report/images/confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved confusion_matrix.png')

# ─── Figure 3: Learning curves ────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

ax = axes[0]
ax.plot(train_sizes, lr_train_accs, 'o-', color='steelblue', label='Train')
ax.plot(train_sizes, lr_val_accs,   's--', color='darkorange', label='Val')
ax.axhline(0.70, color='red',    linestyle='--', linewidth=1.5, label='SOTA 70%')
ax.axhline(0.50, color='gray',   linestyle=':',  linewidth=1.5, label='Random 50%')
ax.axhline(noise_mean, color='purple', linestyle='-.', linewidth=1.5, label=f'Noise Ceiling {noise_mean:.2f}')
ax.set_xlabel('Training Set Size', fontsize=12)
ax.set_ylabel('Accuracy', fontsize=12)
ax.set_title('Learning Curve — Logistic Regression', fontsize=12)
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
ax.set_ylim(0.4, 1.05)

ax = axes[1]
ax.plot(train_sizes, rf_train_accs, 'o-', color='steelblue', label='Train')
ax.plot(train_sizes, rf_val_accs,   's--', color='darkorange', label='Val')
ax.axhline(0.70, color='red',    linestyle='--', linewidth=1.5, label='SOTA 70%')
ax.axhline(0.50, color='gray',   linestyle=':',  linewidth=1.5, label='Random 50%')
ax.axhline(noise_mean, color='purple', linestyle='-.', linewidth=1.5, label=f'Noise Ceiling {noise_mean:.2f}')
ax.set_xlabel('Training Set Size', fontsize=12)
ax.set_ylabel('Accuracy', fontsize=12)
ax.set_title('Learning Curve — Random Forest', fontsize=12)
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
ax.set_ylim(0.4, 1.05)

plt.suptitle('Learning Curves: Overfitting vs Noise Ceiling', fontsize=14)
plt.tight_layout()
plt.savefig('report/images/learning_curves.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved learning_curves.png')

# ─── Figure 4: Noise ceiling bootstrap distribution ───────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(noise_estimates, bins=15, color='steelblue', alpha=0.7, edgecolor='black')
ax.axvline(noise_mean, color='red', linestyle='--', linewidth=2, label=f'Mean={noise_mean:.3f}')
ax.axvline(noise_mean + noise_std, color='red', linestyle=':', linewidth=1.5, label=f'+/-1 std ({noise_std:.3f})')
ax.axvline(noise_mean - noise_std, color='red', linestyle=':', linewidth=1.5)
ax.axvline(0.70, color='orange', linestyle='--', linewidth=2, label='SOTA=0.70')
ax.axvline(0.50, color='gray',   linestyle=':',  linewidth=1.5, label='Random=0.50')
ax.set_xlabel('Accuracy', fontsize=12)
ax.set_ylabel('Count', fontsize=12)
ax.set_title('Bootstrap Noise Ceiling Estimate\n(RF trained on half-train, tested on other half, 50 seeds)', fontsize=12)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/noise_ceiling_bootstrap.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved noise_ceiling_bootstrap.png')

# ─── Figure 5: Label distribution ────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
for ax, (split_name, df) in zip(axes, [('Train', train), ('Val', val), ('Test', test)]):
    counts = df['label'].value_counts().sort_index()
    bars = ax.bar(['reject (0)', 'accept (1)'], counts.values, color=['salmon', 'steelblue'])
    ax.set_title(f'{split_name} Split (n={len(df)})', fontsize=12)
    ax.set_ylabel('Count')
    for i, v in enumerate(counts.values):
        ax.text(i, v + 5, str(v), ha='center', fontsize=11)
    ax.set_ylim(0, max(counts.values) * 1.15)
plt.suptitle('Label Distribution Across Splits', fontsize=14)
plt.tight_layout()
plt.savefig('report/images/label_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved label_distribution.png')

# ─── Figure 6: Val vs Test scatter ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 6))
colors_plot = plt.cm.tab10(np.linspace(0, 1, len(model_names)))
for i, name in enumerate(model_names):
    va = results[name]['val_acc']
    ta = results[name]['test_acc']
    ax.scatter(va, ta, s=120, color=colors_plot[i], zorder=5, label=name)
    ax.annotate(name, (va, ta), textcoords='offset points', xytext=(5, 5), fontsize=8)
ax.axhline(y=0.70, color='red',  linestyle='--', linewidth=1.5, label='SOTA 70%')
ax.axvline(x=0.70, color='red',  linestyle=':', linewidth=1.5)
ax.axhline(y=noise_mean, color='purple', linestyle='-.', linewidth=1.5, label=f'Noise Ceiling {noise_mean:.2f}')
ax.plot([0.45, 0.60], [0.45, 0.60], 'k--', alpha=0.3, label='Val=Test line')
ax.set_xlabel('Validation Accuracy', fontsize=12)
ax.set_ylabel('Test Accuracy', fontsize=12)
ax.set_title('Validation vs Test Accuracy\nAll Models', fontsize=13)
ax.legend(fontsize=8, loc='lower right')
ax.grid(alpha=0.3)
ax.set_xlim(0.45, 0.60)
ax.set_ylim(0.45, 0.60)
plt.tight_layout()
plt.savefig('report/images/val_vs_test.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved val_vs_test.png')

# ─── Print final summary ──────────────────────────────────────────────────────
print('\n' + '='*70)
print('FINAL SUMMARY')
print('='*70)
print(f'{"Model":<25} {"Train":>8} {"Val":>8} {"Test":>8} {"vs SOTA":>10}')
print('-'*65)
for name in model_names:
    r = results[name]
    vs = r['test_acc'] - 0.70
    sign = '+' if vs >= 0 else ''
    print(f'{name:<25} {r["train_acc"]:>8.4f} {r["val_acc"]:>8.4f} {r["test_acc"]:>8.4f} {sign+f"{vs:.4f}":>10}')
print(f'\nNoise Ceiling: {noise_mean:.4f} +/- {noise_std:.4f}')
print(f'SOTA: 0.7000')
print(f'Random Baseline: 0.5000')
print(f'Best Test Acc: {max(r["test_acc"] for r in results.values()):.4f}')
print(f'Best Val Acc:  {max(r["val_acc"] for r in results.values()):.4f}')
