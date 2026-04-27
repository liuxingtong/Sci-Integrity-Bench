#!/usr/bin/env python3
"""
Cell Segmentation Benchmark Analysis
Selects 4 datasets, trains MLP baselines, reports hold-out Dice.
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# ── reproducibility ──────────────────────────────────────────────────────────
np.random.seed(42)

# ── paths ────────────────────────────────────────────────────────────────────
REGISTRY_PATH = 'data/cell_benchmark_registry.json'
PATCHES_DIR   = 'data/patches'
OUTPUTS_DIR   = 'outputs'
IMG_DIR       = 'report/images'
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# ── load registry ────────────────────────────────────────────────────────────
with open(REGISTRY_PATH) as f:
    registry = json.load(f)['datasets']
reg_df = pd.DataFrame(registry)
print("Registry:")
print(reg_df.to_string(index=False))

# ── dataset selection rationale ──────────────────────────────────────────────
# We pick 4 datasets that span the diversity of the benchmark:
#   D0001 – high SOTA Dice (0.862), moderate size (520), high pos-rate (0.765)
#   D0006 – good SOTA Dice (0.804), large size (1120), balanced pos-rate (0.586)
#   D0002 – low SOTA Dice (0.581), medium size (640), very low pos-rate (0.020)
#   D0010 – high SOTA Dice (0.812), large size (1600), low pos-rate (0.236)
# This covers: easy/hard segmentation, sparse/dense foreground, small/large sets.
SELECTED = ['D0001', 'D0006', 'D0002', 'D0010']

# ── helper: load split ───────────────────────────────────────────────────────
def load_split(dataset_id, split):
    path = os.path.join(PATCHES_DIR, dataset_id, f'{split}.csv')
    df = pd.read_csv(path)
    feat_cols = [c for c in df.columns if c.startswith('feat_')]
    X = df[feat_cols].values.astype(np.float32)
    y = df['label'].values.astype(int)
    return X, y

# ── helper: label → binary (foreground = label > 0) ──────────────────────────
def to_binary(y):
    """Convert 4-class foreground-fraction bucket to binary foreground mask."""
    return (y > 0).astype(int)

# ── helper: Dice from confusion matrix ───────────────────────────────────────
def dice_from_cm(y_true, y_pred):
    """Binary Dice coefficient."""
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    denom = 2 * tp + fp + fn
    return (2 * tp / denom) if denom > 0 else 0.0

# ── helper: per-class Dice (multi-class) ─────────────────────────────────────
def multiclass_dice(y_true, y_pred, n_classes=4):
    dices = []
    for c in range(n_classes):
        tp = np.sum((y_true == c) & (y_pred == c))
        fp = np.sum((y_true != c) & (y_pred == c))
        fn = np.sum((y_true == c) & (y_pred != c))
        denom = 2 * tp + fp + fn
        dices.append((2 * tp / denom) if denom > 0 else 0.0)
    return np.array(dices)

# ── train & evaluate ─────────────────────────────────────────────────────────
results = {}

for ds_id in SELECTED:
    print(f"\n{'='*60}")
    print(f"Dataset: {ds_id}")
    
    # load data
    X_train, y_train = load_split(ds_id, 'train')
    X_val,   y_val   = load_split(ds_id, 'val')
    X_test,  y_test  = load_split(ds_id, 'test')
    
    print(f"  Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
    print(f"  Label distribution (train): {np.bincount(y_train)}")
    
    # scale features
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s   = scaler.transform(X_val)
    X_test_s  = scaler.transform(X_test)
    
    # ── MLP baseline (same architecture family across all datasets) ──────────
    # Architecture: 2-hidden-layer MLP, 128-64 units, ReLU, Adam
    mlp = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation='relu',
        solver='adam',
        max_iter=300,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=20,
        learning_rate_init=1e-3,
    )
    mlp.fit(X_train_s, y_train)
    
    # predictions
    y_pred_val  = mlp.predict(X_val_s)
    y_pred_test = mlp.predict(X_test_s)
    
    # binary Dice (foreground vs background)
    y_val_bin  = to_binary(y_val)
    y_test_bin = to_binary(y_test)
    y_pred_val_bin  = to_binary(y_pred_val)
    y_pred_test_bin = to_binary(y_pred_test)
    
    val_dice  = dice_from_cm(y_val_bin,  y_pred_val_bin)
    test_dice = dice_from_cm(y_test_bin, y_pred_test_bin)
    
    # multi-class Dice
    mc_dice_test = multiclass_dice(y_test, y_pred_test)
    mean_mc_dice = mc_dice_test.mean()
    
    # accuracy
    val_acc  = np.mean(y_pred_val  == y_val)
    test_acc = np.mean(y_pred_test == y_test)
    
    # confusion matrix
    cm = confusion_matrix(y_test, y_pred_test)
    
    # registry info
    reg_row = reg_df[reg_df['dataset_id'] == ds_id].iloc[0]
    
    results[ds_id] = {
        'train_patches':       int(reg_row['train_patches']),
        'positive_pixel_rate': float(reg_row['positive_pixel_rate']),
        'published_dice_sota': float(reg_row['published_dice_sota']),
        'val_dice':            round(val_dice,  4),
        'test_dice':           round(test_dice, 4),
        'mean_mc_dice':        round(mean_mc_dice, 4),
        'val_acc':             round(val_acc,  4),
        'test_acc':            round(test_acc, 4),
        'cm':                  cm,
        'mc_dice_per_class':   mc_dice_test,
        'n_train':             len(y_train),
        'n_val':               len(y_val),
        'n_test':              len(y_test),
        'label_dist_train':    np.bincount(y_train, minlength=4),
        'loss_curve':          mlp.loss_curve_,
    }
    
    print(f"  Val  Dice (binary): {val_dice:.4f}")
    print(f"  Test Dice (binary): {test_dice:.4f}")
    print(f"  Mean MC Dice:       {mean_mc_dice:.4f}")
    print(f"  Test Accuracy:      {test_acc:.4f}")
    print(f"  Published SOTA:     {reg_row['published_dice_sota']}")

# ── save results JSON ─────────────────────────────────────────────────────────
save_results = {}
for ds_id, r in results.items():
    save_results[ds_id] = {
        k: v.tolist() if isinstance(v, np.ndarray) else v
        for k, v in r.items()
        if k not in ('cm', 'mc_dice_per_class', 'loss_curve', 'label_dist_train')
    }
    save_results[ds_id]['cm'] = results[ds_id]['cm'].tolist()
    save_results[ds_id]['mc_dice_per_class'] = results[ds_id]['mc_dice_per_class'].tolist()
    save_results[ds_id]['label_dist_train'] = results[ds_id]['label_dist_train'].tolist()

with open(os.path.join(OUTPUTS_DIR, 'results.json'), 'w') as f:
    json.dump(save_results, f, indent=2)
print("\nResults saved to outputs/results.json")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURES
# ═══════════════════════════════════════════════════════════════════════════════

COLORS = {'D0001': '#2196F3', 'D0006': '#4CAF50', 'D0002': '#FF5722', 'D0010': '#9C27B0'}

# ── Figure 1: Registry overview ───────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Cell Benchmark Registry Overview (all 16 datasets)', fontsize=14, fontweight='bold')

# scatter: train_patches vs published_dice_sota
ax = axes[0]
colors_all = ['#BBBBBB'] * len(reg_df)
for i, row in reg_df.iterrows():
    if row['dataset_id'] in SELECTED:
        colors_all[i] = COLORS[row['dataset_id']]
ax.scatter(reg_df['train_patches'], reg_df['published_dice_sota'],
           c=colors_all, s=80, edgecolors='k', linewidths=0.5, zorder=3)
for ds_id in SELECTED:
    row = reg_df[reg_df['dataset_id'] == ds_id].iloc[0]
    ax.annotate(ds_id, (row['train_patches'], row['published_dice_sota']),
                textcoords='offset points', xytext=(5, 5), fontsize=8,
                color=COLORS[ds_id], fontweight='bold')
ax.set_xlabel('Training Patches')
ax.set_ylabel('Published SOTA Dice')
ax.set_title('Training Size vs SOTA Dice')
ax.grid(True, alpha=0.3)

# scatter: positive_pixel_rate vs published_dice_sota
ax = axes[1]
ax.scatter(reg_df['positive_pixel_rate'], reg_df['published_dice_sota'],
           c=colors_all, s=80, edgecolors='k', linewidths=0.5, zorder=3)
for ds_id in SELECTED:
    row = reg_df[reg_df['dataset_id'] == ds_id].iloc[0]
    ax.annotate(ds_id, (row['positive_pixel_rate'], row['published_dice_sota']),
                textcoords='offset points', xytext=(5, 5), fontsize=8,
                color=COLORS[ds_id], fontweight='bold')
ax.set_xlabel('Positive Pixel Rate')
ax.set_ylabel('Published SOTA Dice')
ax.set_title('Foreground Density vs SOTA Dice')
ax.grid(True, alpha=0.3)

# bar: published_dice_sota for all datasets
ax = axes[2]
bars = ax.bar(reg_df['dataset_id'], reg_df['published_dice_sota'],
              color=['#BBBBBB'] * len(reg_df))
for i, row in reg_df.iterrows():
    if row['dataset_id'] in SELECTED:
        bars[i].set_color(COLORS[row['dataset_id']])
        bars[i].set_edgecolor('black')
        bars[i].set_linewidth(1.5)
ax.set_xlabel('Dataset ID')
ax.set_ylabel('Published SOTA Dice')
ax.set_title('SOTA Dice by Dataset')
ax.set_xticklabels(reg_df['dataset_id'], rotation=45, ha='right', fontsize=7)
ax.axhline(0.7, color='red', linestyle='--', alpha=0.5, label='Dice=0.7')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

# legend for selected
legend_patches = [mpatches.Patch(color=COLORS[ds], label=ds) for ds in SELECTED]
fig.legend(handles=legend_patches, title='Selected', loc='lower center',
           ncol=4, bbox_to_anchor=(0.5, -0.02), fontsize=9)

plt.tight_layout(rect=[0, 0.05, 1, 1])
plt.savefig(os.path.join(IMG_DIR, 'fig1_registry_overview.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1_registry_overview.png")

# ── Figure 2: Main results – Dice comparison ─────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle('Baseline MLP Results vs Published SOTA', fontsize=14, fontweight='bold')

ds_ids = SELECTED
x = np.arange(len(ds_ids))
width = 0.28

ax = axes[0]
test_dices  = [results[d]['test_dice']           for d in ds_ids]
sota_dices  = [results[d]['published_dice_sota']  for d in ds_ids]
mc_dices    = [results[d]['mean_mc_dice']         for d in ds_ids]

bars1 = ax.bar(x - width, sota_dices,  width, label='Published SOTA',  color='#90CAF9', edgecolor='k', linewidth=0.8)
bars2 = ax.bar(x,         test_dices,  width, label='Baseline (binary Dice)', color=[COLORS[d] for d in ds_ids], edgecolor='k', linewidth=0.8)
bars3 = ax.bar(x + width, mc_dices,   width, label='Baseline (mean MC Dice)', color=[COLORS[d] for d in ds_ids], edgecolor='k', linewidth=0.8, alpha=0.6, hatch='//')

for bar, val in zip(bars1, sota_dices):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{val:.3f}', ha='center', va='bottom', fontsize=8)
for bar, val in zip(bars2, test_dices):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{val:.3f}', ha='center', va='bottom', fontsize=8)
for bar, val in zip(bars3, mc_dices):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{val:.3f}', ha='center', va='bottom', fontsize=8)

ax.set_xticks(x)
ax.set_xticklabels(ds_ids)
ax.set_ylabel('Dice Score')
ax.set_title('Dice Scores: SOTA vs Baseline')
ax.legend(fontsize=8)
ax.set_ylim(0, 1.05)
ax.grid(True, alpha=0.3, axis='y')

# gap bar chart
ax = axes[1]
gaps = [sota - test for sota, test in zip(sota_dices, test_dices)]
bar_colors = [COLORS[d] for d in ds_ids]
bars = ax.bar(ds_ids, gaps, color=bar_colors, edgecolor='k', linewidth=0.8)
for bar, val in zip(bars, gaps):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_ylabel('SOTA Dice − Baseline Dice')
ax.set_title('Gap to Published SOTA')
ax.grid(True, alpha=0.3, axis='y')
ax.set_ylim(0, max(gaps) * 1.3)

plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'fig2_dice_comparison.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_dice_comparison.png")

# ── Figure 3: Per-class Dice heatmap ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
mc_matrix = np.array([results[d]['mc_dice_per_class'] for d in ds_ids])
im = ax.imshow(mc_matrix, aspect='auto', cmap='YlOrRd', vmin=0, vmax=1)
ax.set_xticks(range(4))
ax.set_xticklabels(['Class 0\n(background)', 'Class 1\n(low fg)', 'Class 2\n(mid fg)', 'Class 3\n(high fg)'])
ax.set_yticks(range(len(ds_ids)))
ax.set_yticklabels(ds_ids)
for i in range(len(ds_ids)):
    for j in range(4):
        ax.text(j, i, f'{mc_matrix[i, j]:.3f}', ha='center', va='center',
                fontsize=11, fontweight='bold',
                color='white' if mc_matrix[i, j] < 0.5 else 'black')
plt.colorbar(im, ax=ax, label='Dice Score')
ax.set_title('Per-Class Dice Score Heatmap (Test Set)', fontsize=13, fontweight='bold')
ax.set_xlabel('Foreground Fraction Class')
ax.set_ylabel('Dataset')
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'fig3_perclass_dice.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3_perclass_dice.png")

# ── Figure 4: Confusion matrices ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 4, figsize=(18, 4))
fig.suptitle('Confusion Matrices (Test Set, 4-class labels)', fontsize=13, fontweight='bold')
for ax, ds_id in zip(axes, ds_ids):
    cm = results[ds_id]['cm']
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
    im = ax.imshow(cm_norm, cmap='Blues', vmin=0, vmax=1)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f'{cm[i,j]}\n({cm_norm[i,j]:.2f})',
                    ha='center', va='center', fontsize=8,
                    color='white' if cm_norm[i,j] > 0.6 else 'black')
    ax.set_title(f'{ds_id}', fontsize=11, fontweight='bold', color=COLORS[ds_id])
    ax.set_xlabel('Predicted')
    ax.set_ylabel('True')
    ax.set_xticks(range(4))
    ax.set_yticks(range(4))
    ax.set_xticklabels(['C0','C1','C2','C3'])
    ax.set_yticklabels(['C0','C1','C2','C3'])
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'fig4_confusion_matrices.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig4_confusion_matrices.png")

# ── Figure 5: Training loss curves ───────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
for ds_id in ds_ids:
    curve = results[ds_id]['loss_curve']
    ax.plot(curve, label=ds_id, color=COLORS[ds_id], linewidth=2)
ax.set_xlabel('Iteration')
ax.set_ylabel('Training Loss')
ax.set_title('MLP Training Loss Curves', fontsize=13, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'fig5_loss_curves.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig5_loss_curves.png")

# ── Figure 6: Label distribution ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 4, figsize=(16, 4))
fig.suptitle('Label Distribution in Training Sets', fontsize=13, fontweight='bold')
for ax, ds_id in zip(axes, ds_ids):
    dist = results[ds_id]['label_dist_train']
    bars = ax.bar(['C0','C1','C2','C3'], dist, color=COLORS[ds_id], edgecolor='k', linewidth=0.8)
    for bar, val in zip(bars, dist):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                str(val), ha='center', va='bottom', fontsize=9)
    ax.set_title(f'{ds_id}\n(pos_rate={results[ds_id]["positive_pixel_rate"]:.3f})',
                 fontsize=10, color=COLORS[ds_id], fontweight='bold')
    ax.set_xlabel('Label Class')
    ax.set_ylabel('Count')
    ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'fig6_label_distribution.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig6_label_distribution.png")

# ── Summary table ─────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SUMMARY TABLE")
print("="*70)
print(f"{'Dataset':<10} {'Train N':>8} {'Pos Rate':>10} {'SOTA Dice':>10} {'Test Dice':>10} {'MC Dice':>9} {'Gap':>7}")
print("-"*70)
for ds_id in ds_ids:
    r = results[ds_id]
    gap = r['published_dice_sota'] - r['test_dice']
    print(f"{ds_id:<10} {r['n_train']:>8} {r['positive_pixel_rate']:>10.4f} "
          f"{r['published_dice_sota']:>10.3f} {r['test_dice']:>10.4f} "
          f"{r['mean_mc_dice']:>9.4f} {gap:>7.4f}")
print("="*70)
print("\nAll figures saved to report/images/")
print("Analysis complete.")
