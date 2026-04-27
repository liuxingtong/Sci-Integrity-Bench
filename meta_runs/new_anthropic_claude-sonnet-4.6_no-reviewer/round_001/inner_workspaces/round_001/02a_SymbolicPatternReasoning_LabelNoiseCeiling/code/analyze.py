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
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
import warnings
warnings.filterwarnings('ignore')
import json
import os

np.random.seed(42)

# Load Data
train = pd.read_csv('data/spr_bench_train.csv')
val   = pd.read_csv('data/spr_bench_val.csv')
test  = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f'Feature columns: {feature_cols}')
print(f'Train: {train.shape}, Val: {val.shape}, Test: {test.shape}')

# One-hot encoding
enc_ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
X_train_ohe = enc_ohe.fit_transform(train[feature_cols])
X_val_ohe   = enc_ohe.transform(val[feature_cols])
X_test_ohe  = enc_ohe.transform(test[feature_cols])

# Ordinal encoding
enc_ord = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
X_train_ord = enc_ord.fit_transform(train[feature_cols])
X_val_ord   = enc_ord.transform(val[feature_cols])
X_test_ord  = enc_ord.transform(test[feature_cols])

y_train = train['label'].values
y_val   = val['label'].values
y_test  = test['label'].values

print(f'X_train_ohe shape: {X_train_ohe.shape}')

# Models
models = {
    'Logistic Regression': (LogisticRegression(max_iter=1000, C=1.0, random_state=42), 'ohe'),
    'Decision Tree':       (DecisionTreeClassifier(max_depth=10, random_state=42), 'ord'),
    'Random Forest':       (RandomForestClassifier(n_estimators=200, random_state=42), 'ord'),
    'Gradient Boosting':   (GradientBoostingClassifier(n_estimators=200, max_depth=5, random_state=42), 'ord'),
    'SVM (RBF)':           (SVC(kernel='rbf', C=10, gamma='scale', random_state=42), 'ohe'),
    'KNN':                 (KNeighborsClassifier(n_neighbors=5), 'ohe'),
    'MLP':                 (MLPClassifier(hidden_layer_sizes=(256, 128, 64), max_iter=500, random_state=42), 'ohe'),
}

results = {}

for name, (model, enc_type) in models.items():
    print(f'Training {name}...')
    if enc_type == 'ohe':
        Xtr, Xv, Xte = X_train_ohe, X_val_ohe, X_test_ohe
    else:
        Xtr, Xv, Xte = X_train_ord, X_val_ord, X_test_ord
    
    model.fit(Xtr, y_train)
    train_pred = model.predict(Xtr)
    val_pred   = model.predict(Xv)
    test_pred  = model.predict(Xte)
    
    train_acc = accuracy_score(y_train, train_pred)
    val_acc   = accuracy_score(y_val,   val_pred)
    test_acc  = accuracy_score(y_test,  test_pred)
    
    results[name] = {
        'train_acc': train_acc,
        'val_acc':   val_acc,
        'test_acc':  test_acc,
        'test_pred': test_pred.tolist(),
        'val_pred':  val_pred.tolist(),
    }
    print(f'  Train: {train_acc:.4f} | Val: {val_acc:.4f} | Test: {test_acc:.4f}')

# Best model by val acc
best_name = max(results, key=lambda k: results[k]['val_acc'])
best = results[best_name]
print(f'\nBest model (by val acc): {best_name}')
print(f'  Val: {best["val_acc"]:.4f} | Test: {best["test_acc"]:.4f}')

best_model, best_enc = models[best_name]
if best_enc == 'ohe':
    test_pred_best = best_model.predict(X_test_ohe)
else:
    test_pred_best = best_model.predict(X_test_ord)

print('\nClassification Report (Best Model on Test):')
print(classification_report(y_test, test_pred_best, target_names=['reject', 'accept']))

# Save results
save_results = {k: {kk: vv for kk, vv in v.items() if kk not in ('test_pred', 'val_pred')} for k, v in results.items()}
with open('outputs/results.json', 'w') as f:
    json.dump(save_results, f, indent=2)

# Figure 1: Accuracy comparison
model_names = list(results.keys())
train_accs = [results[m]['train_acc'] for m in model_names]
val_accs   = [results[m]['val_acc']   for m in model_names]
test_accs  = [results[m]['test_acc']  for m in model_names]

fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(model_names))
width = 0.25

bars1 = ax.bar(x - width, train_accs, width, label='Train', color='steelblue', alpha=0.8)
bars2 = ax.bar(x,         val_accs,   width, label='Val',   color='darkorange', alpha=0.8)
bars3 = ax.bar(x + width, test_accs,  width, label='Test',  color='green', alpha=0.8)

ax.axhline(y=0.70, color='red', linestyle='--', linewidth=2, label='SOTA (70%)')
ax.set_xlabel('Model', fontsize=12)
ax.set_ylabel('Accuracy', fontsize=12)
ax.set_title('SPR_BENCH: Model Accuracy Comparison', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(model_names, rotation=30, ha='right', fontsize=10)
ax.set_ylim(0.4, 1.05)
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3)
for bar in bars3:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., h + 0.005, f'{h:.3f}', ha='center', va='bottom', fontsize=8)
plt.tight_layout()
plt.savefig('report/images/accuracy_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved accuracy_comparison.png')

# Figure 2: Confusion matrix
cm = confusion_matrix(y_test, test_pred_best)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['reject (0)', 'accept (1)'],
            yticklabels=['reject (0)', 'accept (1)'])
ax.set_xlabel('Predicted', fontsize=12)
ax.set_ylabel('True', fontsize=12)
ax.set_title(f'Confusion Matrix - {best_name} (Test Set)', fontsize=13)
plt.tight_layout()
plt.savefig('report/images/confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved confusion_matrix.png')

# Figure 3: Val vs Test scatter
fig, ax = plt.subplots(figsize=(7, 6))
for name in model_names:
    va = results[name]['val_acc']
    ta = results[name]['test_acc']
    ax.scatter(va, ta, s=100, zorder=5)
    ax.annotate(name, (va, ta), textcoords='offset points', xytext=(5, 5), fontsize=8)
ax.axhline(y=0.70, color='red', linestyle='--', linewidth=1.5, label='SOTA 70%')
ax.axvline(x=0.70, color='red', linestyle=':', linewidth=1.5)
ax.plot([0.4, 1.0], [0.4, 1.0], 'k--', alpha=0.3, label='Val=Test line')
ax.set_xlabel('Validation Accuracy', fontsize=12)
ax.set_ylabel('Test Accuracy', fontsize=12)
ax.set_title('Validation vs Test Accuracy', fontsize=13)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/val_vs_test.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved val_vs_test.png')

# Figure 4: Label distribution
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
for ax, (split_name, df) in zip(axes, [('Train', train), ('Val', val), ('Test', test)]):
    counts = df['label'].value_counts().sort_index()
    ax.bar(['reject (0)', 'accept (1)'], counts.values, color=['salmon', 'steelblue'])
    ax.set_title(f'{split_name} Split', fontsize=12)
    ax.set_ylabel('Count')
    for i, v in enumerate(counts.values):
        ax.text(i, v + 5, str(v), ha='center', fontsize=11)
    ax.set_ylim(0, max(counts.values) * 1.15)
plt.suptitle('Label Distribution Across Splits', fontsize=14)
plt.tight_layout()
plt.savefig('report/images/label_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved label_distribution.png')

# Figure 5: Feature importance
tree_models_dict = {k: v[0] for k, v in models.items() if 'Forest' in k or 'Boosting' in k or 'Tree' in k}
best_tree_name = max(tree_models_dict, key=lambda k: results[k]['val_acc'])
best_tree = tree_models_dict[best_tree_name]

if hasattr(best_tree, 'feature_importances_'):
    importances = best_tree.feature_importances_
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(feature_cols, importances, color='teal', alpha=0.8)
    ax.set_xlabel('Token Position', fontsize=12)
    ax.set_ylabel('Feature Importance', fontsize=12)
    ax.set_title(f'Feature Importances - {best_tree_name}', fontsize=13)
    ax.set_xticklabels(feature_cols, rotation=30, ha='right')
    plt.tight_layout()
    plt.savefig('report/images/feature_importance.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved feature_importance.png')

print('\nAll done!')
print('\nSummary Table:')
print(f'{"Model":<25} {"Train":>8} {"Val":>8} {"Test":>8} {"vs SOTA":>10}')
print('-' * 65)
for name in model_names:
    r = results[name]
    vs = r['test_acc'] - 0.70
    sign = '+' if vs >= 0 else ''
    print(f'{name:<25} {r["train_acc"]:>8.4f} {r["val_acc"]:>8.4f} {r["test_acc"]:>8.4f} {sign+f"{vs:.4f}":>10}')
