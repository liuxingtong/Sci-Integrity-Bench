import pandas as pd
import numpy as np
import json
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

SEED = 42
np.random.seed(SEED)

with open('data/benchmark_registry.json') as f:
    registry = json.load(f)

SELECTED = ['OQMEA', 'ILULR', 'RHHQD', 'FDLOT']

def encode_features(train_df, val_df, test_df):
    token_cols = [c for c in train_df.columns if c.startswith('token_')]
    enc = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    enc.fit(train_df[token_cols])
    X_train = enc.transform(train_df[token_cols])
    X_val   = enc.transform(val_df[token_cols])
    X_test  = enc.transform(test_df[token_cols])
    y_train = train_df['label'].values
    y_val   = val_df['label'].values
    y_test  = test_df['label'].values
    return X_train, y_train, X_val, y_val, X_test, y_test, token_cols

def get_candidate_models():
    return {
        'DecisionTree_d3':   DecisionTreeClassifier(max_depth=3, random_state=SEED),
        'DecisionTree_d5':   DecisionTreeClassifier(max_depth=5, random_state=SEED),
        'DecisionTree_d10':  DecisionTreeClassifier(max_depth=10, random_state=SEED),
        'DecisionTree_None': DecisionTreeClassifier(max_depth=None, random_state=SEED),
        'RF_50':             RandomForestClassifier(n_estimators=50,  random_state=SEED),
        'RF_100':            RandomForestClassifier(n_estimators=100, random_state=SEED),
        'RF_200':            RandomForestClassifier(n_estimators=200, random_state=SEED),
        'RF_100_d5':         RandomForestClassifier(n_estimators=100, max_depth=5, random_state=SEED),
        'GBT_100':           GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=SEED),
        'GBT_200':           GradientBoostingClassifier(n_estimators=200, max_depth=3, random_state=SEED),
        'GBT_100_d5':        GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=SEED),
        'LogReg':            LogisticRegression(max_iter=1000, random_state=SEED),
        'SVM_rbf':           SVC(kernel='rbf', C=1.0, random_state=SEED),
        'SVM_rbf_C10':       SVC(kernel='rbf', C=10.0, random_state=SEED),
    }

results = {}
all_model_scores = {}

for code in SELECTED:
    print('\n=== {} (SOTA: {}%) ==='.format(code, registry[code]['sota_accuracy']))
    train_df = pd.read_csv('data/{}_train.csv'.format(code))
    val_df   = pd.read_csv('data/{}_val.csv'.format(code))
    test_df  = pd.read_csv('data/{}_test.csv'.format(code))

    X_train, y_train, X_val, y_val, X_test, y_test, token_cols = encode_features(
        train_df, val_df, test_df)

    print('  Sequence length: {} tokens'.format(len(token_cols)))
    print('  Label balance (train): {:.3f}'.format(y_train.mean()))

    candidates = get_candidate_models()
    val_scores = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        val_acc = accuracy_score(y_val, model.predict(X_val))
        val_scores[name] = (model, val_acc)
        print('    {:25s}  val_acc={:.4f}'.format(name, val_acc))

    best_name = max(val_scores, key=lambda k: val_scores[k][1])
    best_model, best_val_acc = val_scores[best_name]

    test_acc = accuracy_score(y_test, best_model.predict(X_test)) * 100
    sota = registry[code]['sota_accuracy']
    delta = test_acc - sota

    print('  Best model: {}  val_acc={:.4f}'.format(best_name, best_val_acc))
    print('  Test accuracy: {:.2f}%  SOTA: {}%  Delta: {:+.2f}%'.format(test_acc, sota, delta))

    results[code] = {
        'sota': sota,
        'test_acc': test_acc,
        'delta': delta,
        'best_model': best_name,
        'best_val_acc': best_val_acc * 100,
        'seq_len': len(token_cols),
        'val_scores': {k: v[1]*100 for k, v in val_scores.items()}
    }
    all_model_scores[code] = {k: v[1]*100 for k, v in val_scores.items()}

with open('outputs/results.json', 'w') as f:
    json.dump(results, f, indent=2)
print('\nResults saved to outputs/results.json')

# Figure 1: Test Accuracy vs SOTA
fig, ax = plt.subplots(figsize=(9, 5))
codes = SELECTED
x = np.arange(len(codes))
width = 0.35
sota_vals = [results[c]['sota'] for c in codes]
test_vals = [results[c]['test_acc'] for c in codes]
bars1 = ax.bar(x - width/2, sota_vals, width, label='Published SOTA', color='#4C72B0', alpha=0.85)
bars2 = ax.bar(x + width/2, test_vals, width, label='Our Model (Test)', color='#DD8452', alpha=0.85)
ax.set_xlabel('Benchmark Code', fontsize=13)
ax.set_ylabel('Accuracy (%)', fontsize=13)
ax.set_title('Test Accuracy vs Published SOTA\nAcross 4 Selected SPR Benchmarks', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(codes, fontsize=12)
ax.set_ylim(50, 110)
ax.legend(fontsize=11)
for i, code in enumerate(codes):
    delta = results[code]['delta']
    color = 'green' if delta >= 0 else 'red'
    ax.annotate('{:+.1f}%'.format(delta), xy=(x[i] + width/2, test_vals[i] + 0.8),
                ha='center', va='bottom', fontsize=10, color=color, fontweight='bold')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/fig1_test_vs_sota.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig1_test_vs_sota.png')

# Figure 2: Validation accuracy of all candidate models per benchmark
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()
for idx, code in enumerate(codes):
    ax = axes[idx]
    model_names = list(all_model_scores[code].keys())
    scores = [all_model_scores[code][m] for m in model_names]
    best_name = results[code]['best_model']
    colors = ['#DD8452' if m == best_name else '#4C72B0' for m in model_names]
    ax.barh(model_names, scores, color=colors, alpha=0.85)
    ax.set_xlim(40, 105)
    ax.axvline(x=results[code]['sota'], color='red', linestyle='--', linewidth=1.5)
    ax.set_title('{} — Candidate Model Validation Accuracy'.format(code), fontsize=11)
    ax.set_xlabel('Validation Accuracy (%)', fontsize=10)
    orange_patch = mpatches.Patch(color='#DD8452', label='Best: {}'.format(best_name))
    blue_patch   = mpatches.Patch(color='#4C72B0', label='Other models')
    sota_line    = plt.Line2D([0],[0], color='red', linestyle='--', linewidth=1.5,
                               label='SOTA ({:.1f}%)'.format(results[code]['sota']))
    ax.legend(handles=[orange_patch, blue_patch, sota_line], fontsize=8, loc='lower right')
    ax.grid(axis='x', alpha=0.3)
plt.suptitle('Validation Accuracy of All Candidate Models (orange = selected best)', fontsize=13)
plt.tight_layout()
plt.savefig('report/images/fig2_model_selection.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig2_model_selection.png')

# Figure 3: Delta vs sequence length
fig, ax = plt.subplots(figsize=(7, 5))
seq_lens = [results[c]['seq_len'] for c in codes]
deltas   = [results[c]['delta'] for c in codes]
sotas    = [results[c]['sota'] for c in codes]
sc = ax.scatter(seq_lens, deltas, c=sotas, cmap='RdYlGn', s=200, zorder=5,
                edgecolors='black', linewidths=0.8, vmin=55, vmax=100)
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label('SOTA Accuracy (%)', fontsize=11)
for i, code in enumerate(codes):
    ax.annotate(code, (seq_lens[i], deltas[i]),
                textcoords='offset points', xytext=(8, 4), fontsize=11, fontweight='bold')
ax.axhline(0, color='gray', linestyle='--', alpha=0.6)
ax.set_xlabel('Sequence Length (# tokens)', fontsize=12)
ax.set_ylabel('Test Accuracy - SOTA (%)', fontsize=12)
ax.set_title('Performance Gap vs Sequence Length', fontsize=13)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/fig3_delta_vs_seqlen.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig3_delta_vs_seqlen.png')

# Figure 4: Label distribution
fig, axes = plt.subplots(1, 4, figsize=(14, 4))
for idx, code in enumerate(codes):
    ax = axes[idx]
    train_df = pd.read_csv('data/{}_train.csv'.format(code))
    val_df   = pd.read_csv('data/{}_val.csv'.format(code))
    test_df  = pd.read_csv('data/{}_test.csv'.format(code))
    all_df   = pd.concat([train_df, val_df, test_df])
    counts   = all_df['label'].value_counts().sort_index()
    ax.bar(['Class 0', 'Class 1'], counts.values, color=['#4C72B0', '#DD8452'], alpha=0.85)
    ax.set_title('{} (SOTA {:.1f}%)'.format(code, registry[code]['sota_accuracy']), fontsize=11)
    ax.set_ylabel('Count' if idx == 0 else '')
    ax.set_ylim(0, 500)
    ax.grid(axis='y', alpha=0.3)
    for j, v in enumerate(counts.values):
        ax.text(j, v + 5, str(v), ha='center', fontsize=10)
plt.suptitle('Label Distribution Across All Splits (Train+Val+Test)', fontsize=13)
plt.tight_layout()
plt.savefig('report/images/fig4_label_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig4_label_distribution.png')

print('\n=== SUMMARY TABLE ===')
print('{:8s} {:8s} {:8s} {:8s} {:8s} {:30s}'.format('Code','SeqLen','SOTA%','Test%','Delta','BestModel'))
print('-'*75)
for code in codes:
    r = results[code]
    print('{:8s} {:8d} {:8.1f} {:8.2f} {:+8.2f} {:30s}'.format(
        code, r['seq_len'], r['sota'], r['test_acc'], r['delta'], r['best_model']))
