#!/usr/bin/env python3
"""
Cell Segmentation Benchmark Analysis v2
Selects 4 datasets, trains MLP baselines with cross-validation,
reports hold-out Dice with robust statistics.
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
from sklearn.model_selection import StratifiedKFold
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

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

# ── dataset selection ────────────────────────────────────────────────────────
# Selection rationale (4 datasets spanning benchmark diversity):
#   D0001 – highest SOTA Dice (0.862), high foreground density (0.765)
#   D0006 – good SOTA Dice (0.804), balanced foreground (0.586), large train set
#   D0002 – challenging: low SOTA Dice (0.581), very sparse foreground (0.020)
#   D0010 – high SOTA Dice (0.812), low foreground density (0.236), largest set
SELECTED = ['D0001', 'D0006', 'D0002', 'D0010']
COLORS   = {'D0001': '#2196F3', 'D0006': '#4CAF50', 'D0002': '#FF5722', 'D0010': '#9C27B0'}

# ── helpers ──────────────────────────────────────────────────────────────────
def load_split(dataset_id, split):
    path = os.path.join(PATCHES_DIR, dataset_id, f'{split}.csv')
    df = pd.read_csv(path)
    feat_cols = [c for c in df.columns if c.startswith('feat_')]
    X = df[feat_cols].values.astype(np.float32)
    y = df['label'].values.astype(int)
    return X, y

def to_binary(y):
    """Foreground = label > 0 (any non-background class)."""
    return (y > 0).astype(int)

def dice_binary(y_true, y_pred):
    """Binary Dice coefficient."""
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    denom = 2 * tp + fp + fn
    return float(2 * tp / denom) if denom > 0 else 0.0

def dice_multiclass(y_true, y_pred, n_classes=4):
    dices = []
    for c in range(n_classes):
        tp = np.sum((y_true == c) & (y_pred == c))
        fp = np.sum((y_true != c) & (y_pred == c))
        fn = np.sum((y_true == c) & (y_pred != c))
        denom = 2 * tp + fp + fn
        dices.append(float(2 * tp / denom) if denom > 0 else 0.0)
    return np.array(dices)

def make_mlp():
    """Consistent MLP architecture across all datasets."""
    return MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation='relu',
        solver='adam',
        max_iter=500,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=25,
        learning_rate_init=1e-3,
        alpha=1e-4,
    )

# ── main analysis ─────────────────────────────────────────────────────────────
results = {}

for ds_id in SELECTED:
    print(f"\n{'='*60}")
    print(f"Dataset: {ds_id}")

    # load all splits
    X_tr, y_tr = load_split(ds_id, 'train')
    X_va, y_va = load_split(ds_id, 'val')
    X_te, y_te = load_split(ds_id, 'test')

    # pool train+val for cross-validation, keep test as hold-out
    X_tv = np.vstack([X_tr, X_va])
    y_tv = np.concatenate([y_tr, y_va])

    print(f"  Train+Val: {X_tv.shape}, Test: {X_te.shape}")
    print(f"  Label dist (train+val): {np.bincount(y_tv, minlength=4)}")

    # ── 5-fold cross-validation on train+val ─────────────────────────────────
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_binary_dices = []
    cv_mc_dices     = []
    cv_accs         = []

    for fold, (tr_idx, va_idx) in enumerate(skf.split(X_tv, y_tv)):
        Xf_tr, yf_tr = X_tv[tr_idx], y_tv[tr_idx]
        Xf_va, yf_va = X_tv[va_idx], y_tv[va_idx]

        sc = StandardScaler()
        Xf_tr_s = sc.fit_transform(Xf_tr)
        Xf_va_s = sc.transform(Xf_va)

        clf = make_mlp()
        clf.fit(Xf_tr_s, yf_tr)
        yf_pred = clf.predict(Xf_va_s)

        bd = dice_binary(to_binary(yf_va), to_binary(yf_pred))
        md = dice_multiclass(yf_va, yf_pred).mean()
        ac = float(np.mean(yf_pred == yf_va))
        cv_binary_dices.append(bd)
        cv_mc_dices.append(md)
        cv_accs.append(ac)

    cv_binary_mean = float(np.mean(cv_binary_dices))
    cv_binary_std  = float(np.std(cv_binary_dices))
    cv_mc_mean     = float(np.mean(cv_mc_dices))
    cv_mc_std      = float(np.std(cv_mc_dices))

    # ── final model: train on full train+val, evaluate on test ───────────────
    sc_final = StandardScaler()
    X_tv_s = sc_final.fit_transform(X_tv)
    X_te_s = sc_final.transform(X_te)

    clf_final = make_mlp()
    clf_final.fit(X_tv_s, y_tv)
    y_pred_te = clf_final.predict(X_te_s)

    test_binary_dice = dice_binary(to_binary(y_te), to_binary(y_pred_te))
    test_mc_dice     = dice_multiclass(y_te, y_pred_te)
    test_mc_mean     = float(test_mc_dice.mean())
    test_acc         = float(np.mean(y_pred_te == y_te))
    cm               = confusion_matrix(y_te, y_pred_te, labels=[0,1,2,3])

    reg_row = reg_df[reg_df['dataset_id'] == ds_id].iloc[0]

    results[ds_id] = {
        'train_patches':       int(reg_row['train_patches']),
        'positive_pixel_rate': float(reg_row['positive_pixel_rate']),
        'published_dice_sota': float(reg_row['published_dice_sota']),
        # CV metrics
        'cv_binary_dice_mean': round(cv_binary_mean, 4),
        'cv_binary_dice_std':  round(cv_binary_std,  4),
        'cv_mc_dice_mean':     round(cv_mc_mean,     4),
        'cv_mc_dice_std':      round(cv_mc_std,      4),
        'cv_acc_mean':         round(float(np.mean(cv_accs)), 4),
        # Hold-out test metrics
        'test_binary_dice':    round(test_binary_dice, 4),
        'test_mc_dice_mean':   round(test_mc_mean,     4),
        'test_mc_dice_per_class': test_mc_dice,
        'test_acc':            round(test_acc, 4),
        # Misc
        'cm':                  cm,
        'n_train_val':         len(y_tv),
        'n_test':              len(y_te),
        'label_dist_tv':       np.bincount(y_tv, minlength=4),
        'label_dist_te':       np.bincount(y_te, minlength=4),
        'loss_curve':          clf_final.loss_curve_,
        'cv_binary_dices':     cv_binary_dices,
    }

    print(f"  CV Binary Dice:  {cv_binary_mean:.4f} ± {cv_binary_std:.4f}")
    print(f"  CV MC Dice:      {cv_mc_mean:.4f} ± {cv_mc_std:.4f}")
    print(f"  Test Binary Dice:{test_binary_dice:.4f}")
    print(f"  Test MC Dice:    {test_mc_mean:.4f}")
    print(f"  Test Accuracy:   {test_acc:.4f}")
    print(f"  Published SOTA:  {reg_row['published_dice_sota']}")

# ── save results ──────────────────────────────────────────────────────────────
save_results = {}
for ds_id, r in results.items():
    save_results[ds_id] = {}
    for k, v in r.items():
        if isinstance(v, np.ndarray):
            save_results[ds_id][k] = v.tolist()
        elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], np.floating):
            save_results[ds_id][k] = [float(x) for x in v]
        else:
            save_results[ds_id][k] = v

with open(os.path.join(OUTPUTS_DIR, 'results_v2.json'), 'w') as f:
    json.dump(save_results, f, indent=2)
print("\nResults saved to outputs/results_v2.json")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURES
# ═══════════════════════════════════════════════════════════════════════════════

# ── Figure 1: Registry overview ───────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('Cell Benchmark Registry — All 16 Datasets', fontsize=14, fontweight='bold')

colors_all = [COLORS.get(row['dataset_id'], '#BBBBBB') for _, row in reg_df.iterrows()]
alpha_all  = [1.0 if row['dataset_id'] in SELECTED else 0.35 for _, row in reg_df.iterrows()]

# (a) train_patches vs SOTA Dice
ax = axes[0]
for i, row in reg_df.iterrows():
    ax.scatter(row['train_patches'], row['published_dice_sota'],
               c=colors_all[i], s=90, edgecolors='k', linewidths=0.6,
               alpha=alpha_all[i], zorder=3)
    if row['dataset_id'] in SELECTED:
        ax.annotate(row['dataset_id'],
                    (row['train_patches'], row['published_dice_sota']),
                    textcoords='offset points', xytext=(6, 4), fontsize=8,
                    color=colors_all[i], fontweight='bold')
ax.set_xlabel('Registered Training Patches')
ax.set_ylabel('Published SOTA Dice')
ax.set_title('(a) Training Size vs SOTA Dice')
ax.grid(True, alpha=0.3)

# (b) positive_pixel_rate vs SOTA Dice
ax = axes[1]
for i, row in reg_df.iterrows():
    ax.scatter(row['positive_pixel_rate'], row['published_dice_sota'],
               c=colors_all[i], s=90, edgecolors='k', linewidths=0.6,
               alpha=alpha_all[i], zorder=3)
    if row['dataset_id'] in SELECTED:
        ax.annotate(row['dataset_id'],
                    (row['positive_pixel_rate'], row['published_dice_sota']),
                    textcoords='offset points', xytext=(6, 4), fontsize=8,
                    color=colors_all[i], fontweight='bold')
ax.set_xlabel('Positive Pixel Rate')
ax.set_ylabel('Published SOTA Dice')
ax.set_title('(b) Foreground Density vs SOTA Dice')
ax.grid(True, alpha=0.3)

# (c) bar chart of SOTA Dice
ax = axes[2]
bars = ax.bar(reg_df['dataset_id'], reg_df['published_dice_sota'],
              color=colors_all, edgecolor='k', linewidth=0.6)
for i, row in reg_df.iterrows():
    if row['dataset_id'] in SELECTED:
        bars[i].set_linewidth(2.0)
ax.set_xlabel('Dataset ID')
ax.set_ylabel('Published SOTA Dice')
ax.set_title('(c) SOTA Dice by Dataset')
ax.set_xticklabels(reg_df['dataset_id'], rotation=45, ha='right', fontsize=7)
ax.axhline(0.7, color='red', linestyle='--', alpha=0.5, label='Dice = 0.70')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

legend_patches = [mpatches.Patch(color=COLORS[ds], label=ds) for ds in SELECTED]
fig.legend(handles=legend_patches, title='Selected datasets',
           loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.02), fontsize=9)
plt.tight_layout(rect=[0, 0.06, 1, 1])
plt.savefig(os.path.join(IMG_DIR, 'fig1_registry_overview.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1_registry_overview.png")

# ── Figure 2: Main results – Dice comparison ─────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('MLP Baseline vs Published SOTA Dice', fontsize=14, fontweight='bold')

x = np.arange(len(SELECTED))
width = 0.25

ax = axes[0]
sota_vals = [results[d]['published_dice_sota']  for d in SELECTED]
cv_vals   = [results[d]['cv_binary_dice_mean']   for d in SELECTED]
cv_errs   = [results[d]['cv_binary_dice_std']    for d in SELECTED]
test_vals = [results[d]['test_binary_dice']      for d in SELECTED]

b1 = ax.bar(x - width, sota_vals, width, label='Published SOTA',
            color='#90CAF9', edgecolor='k', linewidth=0.8)
b2 = ax.bar(x,          cv_vals,  width, label='CV Binary Dice (mean±std)',
            color=[COLORS[d] for d in SELECTED], edgecolor='k', linewidth=0.8,
            yerr=cv_errs, capsize=4, error_kw={'linewidth': 1.5})
b3 = ax.bar(x + width,  test_vals, width, label='Hold-out Test Dice',
            color=[COLORS[d] for d in SELECTED], edgecolor='k', linewidth=0.8,
            alpha=0.55, hatch='//')

for bar, val in zip(b1, sota_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.015,
            f'{val:.3f}', ha='center', va='bottom', fontsize=8)
for bar, val in zip(b2, cv_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.04,
            f'{val:.3f}', ha='center', va='bottom', fontsize=8)
for bar, val in zip(b3, test_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.015,
            f'{val:.3f}', ha='center', va='bottom', fontsize=8)

ax.set_xticks(x)
ax.set_xticklabels(SELECTED, fontsize=11)
ax.set_ylabel('Dice Score')
ax.set_title('(a) Dice Scores: SOTA vs Baseline')
ax.legend(fontsize=8, loc='lower right')
ax.set_ylim(0, 1.15)
ax.grid(True, alpha=0.3, axis='y')

# (b) CV fold-level box plot
ax = axes[1]
cv_data = [results[d]['cv_binary_dices'] for d in SELECTED]
bp = ax.boxplot(cv_data, patch_artist=True, widths=0.5,
                medianprops={'color': 'black', 'linewidth': 2})
for patch, ds_id in zip(bp['boxes'], SELECTED):
    patch.set_facecolor(COLORS[ds_id])
    patch.set_alpha(0.7)
for i, (ds_id, vals) in enumerate(zip(SELECTED, cv_data)):
    ax.scatter([i+1]*len(vals), vals, color=COLORS[ds_id],
               s=50, zorder=5, edgecolors='k', linewidths=0.5)
    ax.axhline(results[ds_id]['published_dice_sota'],
               xmin=(i)/len(SELECTED), xmax=(i+1)/len(SELECTED),
               color='red', linestyle='--', linewidth=1.5, alpha=0.8)
ax.set_xticks(range(1, len(SELECTED)+1))
ax.set_xticklabels(SELECTED, fontsize=11)
ax.set_ylabel('Binary Dice Score')
ax.set_title('(b) 5-Fold CV Distribution\n(red dashes = published SOTA)')
ax.set_ylim(0, 1.1)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'fig2_dice_comparison.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_dice_comparison.png")

# ── Figure 3: Per-class Dice heatmap ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
mc_matrix = np.array([results[d]['test_mc_dice_per_class'] for d in SELECTED])
im = ax.imshow(mc_matrix, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
for i in range(len(SELECTED)):
    for j in range(4):
        val = mc_matrix[i, j]
        ax.text(j, i, f'{val:.3f}', ha='center', va='center',
                fontsize=12, fontweight='bold',
                color='white' if val < 0.35 or val > 0.75 else 'black')
ax.set_xticks(range(4))
ax.set_xticklabels(['Class 0\n(background)', 'Class 1\n(low fg)',
                    'Class 2\n(mid fg)', 'Class 3\n(high fg)'], fontsize=10)
ax.set_yticks(range(len(SELECTED)))
ax.set_yticklabels(SELECTED, fontsize=11)
plt.colorbar(im, ax=ax, label='Dice Score')
ax.set_title('Per-Class Dice Score Heatmap (Hold-out Test Set)', fontsize=13, fontweight='bold')
ax.set_xlabel('Foreground Fraction Class')
ax.set_ylabel('Dataset')
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'fig3_perclass_dice.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3_perclass_dice.png")

# ── Figure 4: Confusion matrices ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 4, figsize=(18, 4))
fig.suptitle('Confusion Matrices — Hold-out Test Set (4-class labels)', fontsize=13, fontweight='bold')
for ax, ds_id in zip(axes, SELECTED):
    cm = results[ds_id]['cm']
    row_sums = cm.sum(axis=1, keepdims=True)
    cm_norm = np.where(row_sums > 0, cm.astype(float) / row_sums, 0.0)
    im = ax.imshow(cm_norm, cmap='Blues', vmin=0, vmax=1)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f'{cm[i,j]}\n({cm_norm[i,j]:.2f})',
                    ha='center', va='center', fontsize=8,
                    color='white' if cm_norm[i,j] > 0.6 else 'black')
    ax.set_title(f'{ds_id}', fontsize=11, fontweight='bold', color=COLORS[ds_id])
    ax.set_xlabel('Predicted Label')
    ax.set_ylabel('True Label')
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
for ds_id in SELECTED:
    curve = results[ds_id]['loss_curve']
    ax.plot(curve, label=ds_id, color=COLORS[ds_id], linewidth=2.5)
ax.set_xlabel('Training Iteration', fontsize=12)
ax.set_ylabel('Cross-Entropy Loss', fontsize=12)
ax.set_title('MLP Training Loss Curves (Final Model)', fontsize=13, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'fig5_loss_curves.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig5_loss_curves.png")

# ── Figure 6: Label distribution ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 4, figsize=(16, 4))
fig.suptitle('Label Distribution in Training+Validation Sets', fontsize=13, fontweight='bold')
for ax, ds_id in zip(axes, SELECTED):
    dist = results[ds_id]['label_dist_tv']
    bars = ax.bar(['C0','C1','C2','C3'], dist,
                  color=COLORS[ds_id], edgecolor='k', linewidth=0.8, alpha=0.85)
    for bar, val in zip(bars, dist):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                str(val), ha='center', va='bottom', fontsize=10)
    r = results[ds_id]
    ax.set_title(f'{ds_id}\npos_rate={r["positive_pixel_rate"]:.3f}  SOTA={r["published_dice_sota"]:.3f}',
                 fontsize=9, color=COLORS[ds_id], fontweight='bold')
    ax.set_xlabel('Label Class')
    ax.set_ylabel('Count')
    ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'fig6_label_distribution.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig6_label_distribution.png")

# ── Summary table ─────────────────────────────────────────────────────────────
print("\n" + "="*80)
print("FINAL SUMMARY TABLE")
print("="*80)
print(f"{'Dataset':<10} {'Pos Rate':>10} {'SOTA Dice':>10} {'CV Dice':>14} {'Test Dice':>10} {'Gap':>8}")
print("-"*80)
for ds_id in SELECTED:
    r = results[ds_id]
    gap = r['published_dice_sota'] - r['test_binary_dice']
    cv_str = f"{r['cv_binary_dice_mean']:.4f}±{r['cv_binary_dice_std']:.4f}"
    print(f"{ds_id:<10} {r['positive_pixel_rate']:>10.4f} "
          f"{r['published_dice_sota']:>10.3f} {cv_str:>14} "
          f"{r['test_binary_dice']:>10.4f} {gap:>8.4f}")
print("="*80)
print("\nAll figures saved to report/images/")
print("Analysis complete.")
