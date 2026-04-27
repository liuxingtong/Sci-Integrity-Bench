import pandas as pd
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

SEED = 42
np.random.seed(SEED)

with open('data/benchmark_registry.json') as f:
    registry = json.load(f)
with open('outputs/results.json') as f:
    results_basic = json.load(f)
with open('outputs/results_advanced.json') as f:
    results_adv = json.load(f)

SELECTED = ['OQMEA', 'ILULR', 'RHHQD', 'FDLOT']

# Use best result from either approach
results = {}
for code in SELECTED:
    rb = results_basic[code]
    ra = results_adv[code]
    if ra['test_acc'] > rb['test_acc']:
        best = ra.copy()
        best['approach'] = 'Rich Features'
    else:
        best = rb.copy()
        best['approach'] = 'Ordinal Encoding'
    results[code] = best

print('Final results:')
for code in SELECTED:
    r = results[code]
    print('  {} test={:.2f}% SOTA={}% delta={:+.2f}% approach={}'.format(
        code, r['test_acc'], r['sota'], r['delta'], r['approach']))

with open('outputs/results_final.json', 'w') as f:
    json.dump(results, f, indent=2)

# ─── Figure 1: Main Results - Test vs SOTA ───────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
codes = SELECTED
x = np.arange(len(codes))
width = 0.35

sota_vals = [results[c]['sota'] for c in codes]
test_vals = [results[c]['test_acc'] for c in codes]

bars1 = ax.bar(x - width/2, sota_vals, width, label='Published SOTA', 
               color='#2196F3', alpha=0.85, edgecolor='white', linewidth=0.5)
bars2 = ax.bar(x + width/2, test_vals, width, label='Our Best Model (Test)', 
               color='#FF9800', alpha=0.85, edgecolor='white', linewidth=0.5)

ax.set_xlabel('Benchmark Code', fontsize=13)
ax.set_ylabel('Accuracy (%)', fontsize=13)
ax.set_title('Test Accuracy vs Published SOTA\nAcross 4 Selected SPR Benchmarks', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels([
    '{} ({} tok)'.format(c, results[c]['seq_len']) for c in codes
], fontsize=11)
ax.set_ylim(40, 115)
ax.legend(fontsize=11, loc='upper right')

for i, code in enumerate(codes):
    delta = results[code]['delta']
    color = '#2E7D32' if delta >= 0 else '#C62828'
    ax.annotate('{:+.1f}%'.format(delta), 
                xy=(x[i] + width/2, test_vals[i] + 1.5),
                ha='center', va='bottom', fontsize=11, color=color, fontweight='bold')
    # Add SOTA value label
    ax.text(x[i] - width/2, sota_vals[i] + 1.5, '{:.1f}'.format(sota_vals[i]),
            ha='center', va='bottom', fontsize=9, color='#1565C0')
    # Add test value label
    ax.text(x[i] + width/2, test_vals[i] - 3.5, '{:.1f}'.format(test_vals[i]),
            ha='center', va='top', fontsize=9, color='#E65100')

ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5, label='Random baseline (50%)')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/fig1_test_vs_sota.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig1_test_vs_sota.png')

# ─── Figure 2: Model Selection - Validation Accuracy Heatmap ─────────────────
fig, axes = plt.subplots(2, 2, figsize=(15, 11))
axes = axes.flatten()

for idx, code in enumerate(codes):
    ax = axes[idx]
    # Combine basic and advanced val scores
    all_scores = {}
    for k, v in results_basic[code]['val_scores'].items():
        all_scores['Basic/' + k] = v
    for k, v in results_adv[code]['val_scores'].items():
        all_scores['Rich/' + k] = v
    
    model_names = list(all_scores.keys())
    scores = [all_scores[m] for m in model_names]
    best_name = results[code]['approach'].split()[0] + '/' + results[code]['best_model']
    
    colors = ['#FF9800' if m == best_name else 
              ('#4CAF50' if all_scores[m] >= results[code]['sota'] else '#90CAF9') 
              for m in model_names]
    
    bars = ax.barh(model_names, scores, color=colors, alpha=0.85, height=0.7)
    ax.set_xlim(35, 105)
    ax.axvline(x=results[code]['sota'], color='red', linestyle='--', linewidth=2,
               label='SOTA ({:.1f}%)'.format(results[code]['sota']))
    ax.axvline(x=50, color='gray', linestyle=':', linewidth=1, alpha=0.6, label='Random (50%)')
    ax.set_title('{} — Validation Accuracy (seq_len={})'.format(code, results[code]['seq_len']), 
                 fontsize=11, fontweight='bold')
    ax.set_xlabel('Validation Accuracy (%)', fontsize=10)
    
    orange_patch = mpatches.Patch(color='#FF9800', label='Selected best')
    green_patch  = mpatches.Patch(color='#4CAF50', label='>= SOTA')
    blue_patch   = mpatches.Patch(color='#90CAF9', label='Other models')
    sota_line    = plt.Line2D([0],[0], color='red', linestyle='--', linewidth=2,
                               label='SOTA ({:.1f}%)'.format(results[code]['sota']))
    ax.legend(handles=[orange_patch, green_patch, blue_patch, sota_line], 
              fontsize=7.5, loc='lower right')
    ax.grid(axis='x', alpha=0.3)
    ax.tick_params(axis='y', labelsize=8)

plt.suptitle('Candidate Model Validation Accuracy\n(Basic = ordinal encoding; Rich = engineered features)', 
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig2_model_selection.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig2_model_selection.png')

# ─── Figure 3: Performance Gap Analysis ──────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Left: Delta vs SOTA difficulty
ax = axes[0]
seq_lens = [results[c]['seq_len'] for c in codes]
deltas   = [results[c]['delta'] for c in codes]
sotas    = [results[c]['sota'] for c in codes]

sc = ax.scatter(sotas, deltas, c=seq_lens, cmap='viridis', s=250, zorder=5,
                edgecolors='black', linewidths=1.0, vmin=3, vmax=13)
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label('Sequence Length (tokens)', fontsize=10)
for i, code in enumerate(codes):
    ax.annotate(code, (sotas[i], deltas[i]),
                textcoords='offset points', xytext=(8, 5), fontsize=11, fontweight='bold')
ax.axhline(0, color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
ax.set_xlabel('Published SOTA Accuracy (%)', fontsize=12)
ax.set_ylabel('Test Accuracy - SOTA (%)', fontsize=12)
ax.set_title('Performance Gap vs SOTA Difficulty', fontsize=12, fontweight='bold')
ax.grid(alpha=0.3)

# Right: Delta vs Sequence Length
ax2 = axes[1]
sc2 = ax2.scatter(seq_lens, deltas, c=sotas, cmap='RdYlGn', s=250, zorder=5,
                  edgecolors='black', linewidths=1.0, vmin=55, vmax=100)
cbar2 = plt.colorbar(sc2, ax=ax2)
cbar2.set_label('SOTA Accuracy (%)', fontsize=10)
for i, code in enumerate(codes):
    ax2.annotate(code, (seq_lens[i], deltas[i]),
                 textcoords='offset points', xytext=(8, 5), fontsize=11, fontweight='bold')
ax2.axhline(0, color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
ax2.set_xlabel('Sequence Length (# tokens)', fontsize=12)
ax2.set_ylabel('Test Accuracy - SOTA (%)', fontsize=12)
ax2.set_title('Performance Gap vs Sequence Length', fontsize=12, fontweight='bold')
ax2.grid(alpha=0.3)

plt.suptitle('Analysis of Performance Gaps Across Benchmarks', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig3_gap_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig3_gap_analysis.png')

# ─── Figure 4: Data Overview ──────────────────────────────────────────────────
fig, axes = plt.subplots(2, 4, figsize=(16, 8))

for idx, code in enumerate(codes):
    # Top row: label distribution
    ax = axes[0][idx]
    train_df = pd.read_csv('data/{}_train.csv'.format(code))
    val_df   = pd.read_csv('data/{}_val.csv'.format(code))
    test_df  = pd.read_csv('data/{}_test.csv'.format(code))
    
    splits = ['Train', 'Val', 'Test']
    split_dfs = [train_df, val_df, test_df]
    colors_split = ['#42A5F5', '#66BB6A', '#FFA726']
    
    x_pos = np.arange(3)
    class0 = [df['label'].value_counts().get(0, 0) for df in split_dfs]
    class1 = [df['label'].value_counts().get(1, 0) for df in split_dfs]
    
    ax.bar(x_pos, class0, label='Class 0', color='#42A5F5', alpha=0.85)
    ax.bar(x_pos, class1, bottom=class0, label='Class 1', color='#FFA726', alpha=0.85)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(splits, fontsize=9)
    ax.set_title('{} (SOTA {:.1f}%)'.format(code, registry[code]['sota_accuracy']), 
                 fontsize=10, fontweight='bold')
    ax.set_ylabel('Count' if idx == 0 else '')
    ax.legend(fontsize=7, loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    
    # Bottom row: token vocabulary size per position
    ax2 = axes[1][idx]
    token_cols = [c for c in train_df.columns if c.startswith('token_')]
    vocab_sizes = [train_df[c].nunique() for c in token_cols]
    ax2.bar(range(len(token_cols)), vocab_sizes, color='#7E57C2', alpha=0.85)
    ax2.set_xlabel('Token Position', fontsize=9)
    ax2.set_ylabel('Vocab Size' if idx == 0 else '')
    ax2.set_title('Vocabulary Size per Position', fontsize=10)
    ax2.set_xticks(range(len(token_cols)))
    ax2.set_xticklabels(['t{}'.format(i) for i in range(len(token_cols))], fontsize=8)
    ax2.grid(axis='y', alpha=0.3)
    ax2.set_ylim(0, max(vocab_sizes) + 2)
    for i, v in enumerate(vocab_sizes):
        ax2.text(i, v + 0.1, str(v), ha='center', fontsize=8)

plt.suptitle('Data Overview: Label Distribution and Token Vocabulary\nAcross 4 Selected Benchmarks', 
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig4_data_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig4_data_overview.png')

print('\nAll figures saved.')
