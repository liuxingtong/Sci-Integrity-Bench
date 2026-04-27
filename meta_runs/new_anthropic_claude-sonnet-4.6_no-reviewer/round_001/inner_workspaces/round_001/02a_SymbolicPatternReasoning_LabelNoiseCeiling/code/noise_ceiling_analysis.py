import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.calibration import CalibratedClassifierCV
import warnings
warnings.filterwarnings('ignore')
import json

np.random.seed(42)

train = pd.read_csv('data/spr_bench_train.csv')
val   = pd.read_csv('data/spr_bench_val.csv')
test  = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

# Combine train+val for final model
train_val = pd.concat([train, val], ignore_index=True)

# ─── Feature Engineering ─────────────────────────────────────────────────────
def build_all_features(df, feature_cols):
    shapes = ['T', 'S', 'C', 'D']
    colors = ['r', 'g', 'b', 'y']
    all_tokens = [s+c for s in shapes for c in colors]
    shape_cols = [c + '_shape' for c in feature_cols]
    color_cols = [c + '_color' for c in feature_cols]
    
    df2 = df.copy()
    for col in feature_cols:
        df2[col + '_shape'] = df2[col].str[0]
        df2[col + '_color'] = df2[col].str[1]
    
    feats = {}
    shape_idx = {'T': 0, 'S': 1, 'C': 2, 'D': 3}
    color_idx = {'r': 0, 'g': 1, 'b': 2, 'y': 3}
    
    for col in shape_cols:
        feats[col + '_idx'] = df2[col].map(shape_idx)
    for col in color_cols:
        feats[col + '_idx'] = df2[col].map(color_idx)
    
    for shape in shapes:
        feats[f'count_{shape}'] = df2[shape_cols].apply(lambda row: (row == shape).sum(), axis=1)
        feats[f'parity_{shape}'] = feats[f'count_{shape}'] % 2
    for color in colors:
        feats[f'count_{color}'] = df2[color_cols].apply(lambda row: (row == color).sum(), axis=1)
        feats[f'parity_{color}'] = feats[f'count_{color}'] % 2
    for token in all_tokens:
        feats[f'count_{token}'] = df2[feature_cols].apply(lambda row: (row == token).sum(), axis=1)
        feats[f'parity_{token}'] = feats[f'count_{token}'] % 2
    
    feats['shape_sum'] = sum(feats[col + '_idx'] for col in shape_cols)
    feats['color_sum'] = sum(feats[col + '_idx'] for col in color_cols)
    feats['shape_sum_parity'] = feats['shape_sum'] % 2
    feats['color_sum_parity'] = feats['color_sum'] % 2
    feats['total_sum'] = feats['shape_sum'] + feats['color_sum']
    feats['total_sum_parity'] = feats['total_sum'] % 2
    
    shape_xor = feats[shape_cols[0] + '_idx'].copy()
    for col in shape_cols[1:]:
        shape_xor = shape_xor ^ feats[col + '_idx']
    feats['shape_xor'] = shape_xor
    
    color_xor = feats[color_cols[0] + '_idx'].copy()
    for col in color_cols[1:]:
        color_xor = color_xor ^ feats[col + '_idx']
    feats['color_xor'] = color_xor
    
    feats['n_unique_shapes'] = df2.apply(lambda row: len(set(row[c] for c in shape_cols)), axis=1)
    feats['n_unique_colors'] = df2.apply(lambda row: len(set(row[c] for c in color_cols)), axis=1)
    feats['n_unique_tokens'] = df2.apply(lambda row: len(set(row[c] for c in feature_cols)), axis=1)
    
    for i in range(len(shape_cols)-1):
        for s1 in shapes:
            for s2 in shapes:
                feats[f'bigram_shape_{i}_{s1}{s2}'] = ((df2[shape_cols[i]] == s1) & (df2[shape_cols[i+1]] == s2)).astype(int)
    for i in range(len(color_cols)-1):
        for c1 in colors:
            for c2 in colors:
                feats[f'bigram_color_{i}_{c1}{c2}'] = ((df2[color_cols[i]] == c1) & (df2[color_cols[i+1]] == c2)).astype(int)
    
    return pd.DataFrame(feats)

print('Building features...')
X_train_rich = build_all_features(train, feature_cols)
X_val_rich   = build_all_features(val,   feature_cols)
X_test_rich  = build_all_features(test,  feature_cols)
X_tv_rich    = build_all_features(train_val, feature_cols)

# OHE features
enc = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
X_train_ohe = enc.fit_transform(train[feature_cols])
X_val_ohe   = enc.transform(val[feature_cols])
X_test_ohe  = enc.transform(test[feature_cols])
X_tv_ohe    = enc.transform(train_val[feature_cols])

y_train = train['label'].values
y_val   = val['label'].values
y_test  = test['label'].values
y_tv    = train_val['label'].values

print(f'Rich features: {X_train_rich.shape}')
print(f'OHE features: {X_train_ohe.shape}')

# ─── Noise Ceiling Estimation ─────────────────────────────────────────────────
print('\n=== Noise Ceiling Estimation ===')
# The task name is "LabelNoiseCeiling" - this suggests labels have noise
# Estimate noise level from train/val consistency
# If we train a perfect model on train and test on val, the gap tells us about noise

# Method 1: Memorization upper bound
# Train a lookup table (memorize all training examples)
# Then test on val - if val sequences are unseen, we can't do better than chance
# This gives us the noise ceiling

# Method 2: Bootstrap estimate of noise
# Split train into two halves, train on one, test on other
# The max accuracy on the second half is the noise ceiling

noise_estimates = []
for seed in range(20):
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(train))
    half = len(train) // 2
    idx1, idx2 = idx[:half], idx[half:]
    
    X1 = X_train_rich.iloc[idx1]
    y1 = y_train[idx1]
    X2 = X_train_rich.iloc[idx2]
    y2 = y_train[idx2]
    
    # Train a powerful model on half
    rf = RandomForestClassifier(n_estimators=100, random_state=seed, n_jobs=-1)
    rf.fit(X1, y1)
    acc = accuracy_score(y2, rf.predict(X2))
    noise_estimates.append(acc)

print(f'Bootstrap noise ceiling estimate (RF on half-train): {np.mean(noise_estimates):.4f} +/- {np.std(noise_estimates):.4f}')
print(f'Min: {np.min(noise_estimates):.4f}, Max: {np.max(noise_estimates):.4f}')

# ─── Try many model configurations ───────────────────────────────────────────
print('\n=== Systematic Model Search ===')

best_val = 0
best_config = None

configs = [
    # (name, model, X_tr, X_v, X_te)
    ('LR_ohe_C0.01',   LogisticRegression(C=0.01, max_iter=1000, random_state=42), X_train_ohe, X_val_ohe, X_test_ohe),
    ('LR_ohe_C0.1',    LogisticRegression(C=0.1,  max_iter=1000, random_state=42), X_train_ohe, X_val_ohe, X_test_ohe),
    ('LR_ohe_C1',      LogisticRegression(C=1.0,  max_iter=1000, random_state=42), X_train_ohe, X_val_ohe, X_test_ohe),
    ('LR_ohe_C10',     LogisticRegression(C=10,   max_iter=1000, random_state=42), X_train_ohe, X_val_ohe, X_test_ohe),
    ('LR_rich_C0.01',  LogisticRegression(C=0.01, max_iter=1000, random_state=42), X_train_rich, X_val_rich, X_test_rich),
    ('LR_rich_C0.1',   LogisticRegression(C=0.1,  max_iter=1000, random_state=42), X_train_rich, X_val_rich, X_test_rich),
    ('LR_rich_C1',     LogisticRegression(C=1.0,  max_iter=1000, random_state=42), X_train_rich, X_val_rich, X_test_rich),
    ('RF_rich_100',    RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, n_jobs=-1), X_train_rich, X_val_rich, X_test_rich),
    ('RF_rich_500',    RandomForestClassifier(n_estimators=500, max_depth=5, random_state=42, n_jobs=-1), X_train_rich, X_val_rich, X_test_rich),
    ('RF_rich_500_d8', RandomForestClassifier(n_estimators=500, max_depth=8, random_state=42, n_jobs=-1), X_train_rich, X_val_rich, X_test_rich),
    ('GB_rich_100',    GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42), X_train_rich, X_val_rich, X_test_rich),
    ('GB_rich_200',    GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42), X_train_rich, X_val_rich, X_test_rich),
    ('MLP_ohe_small',  MLPClassifier(hidden_layer_sizes=(64,), max_iter=500, alpha=0.01, random_state=42), X_train_ohe, X_val_ohe, X_test_ohe),
    ('MLP_ohe_med',    MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, alpha=0.01, random_state=42), X_train_ohe, X_val_ohe, X_test_ohe),
    ('MLP_rich_small', MLPClassifier(hidden_layer_sizes=(64,), max_iter=500, alpha=0.01, random_state=42), X_train_rich, X_val_rich, X_test_rich),
    ('MLP_rich_med',   MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, alpha=0.01, random_state=42), X_train_rich, X_val_rich, X_test_rich),
    ('DT_rich_d3',     DecisionTreeClassifier(max_depth=3, random_state=42), X_train_rich, X_val_rich, X_test_rich),
    ('DT_rich_d5',     DecisionTreeClassifier(max_depth=5, random_state=42), X_train_rich, X_val_rich, X_test_rich),
]

all_results = []
for name, model, Xtr, Xv, Xte in configs:
    model.fit(Xtr, y_train)
    tr_acc = accuracy_score(y_train, model.predict(Xtr))
    va_acc = accuracy_score(y_val,   model.predict(Xv))
    te_acc = accuracy_score(y_test,  model.predict(Xte))
    all_results.append({'name': name, 'train': tr_acc, 'val': va_acc, 'test': te_acc})
    print(f'  {name:<25}: train={tr_acc:.4f}, val={va_acc:.4f}, test={te_acc:.4f}')
    if va_acc > best_val:
        best_val = va_acc
        best_config = name

print(f'\nBest config by val: {best_config} (val={best_val:.4f})')

# ─── Train+Val combined for final test ────────────────────────────────────────
print('\n=== Train+Val combined model ===')
best_idx = next(i for i, r in enumerate(all_results) if r['name'] == best_config)
best_model_cfg = configs[best_idx]
best_model_name, best_model, _, _, Xte = best_model_cfg

# Retrain on train+val
best_model.fit(X_tv_rich if 'rich' in best_model_name else X_tv_ohe, y_tv)
Xte_use = X_test_rich if 'rich' in best_model_name else X_test_ohe
te_acc_final = accuracy_score(y_test, best_model.predict(Xte_use))
print(f'  Best model ({best_model_name}) trained on train+val, test acc: {te_acc_final:.4f}')

# ─── Save results ─────────────────────────────────────────────────────────────
with open('outputs/noise_ceiling_results.json', 'w') as f:
    json.dump({
        'bootstrap_noise_ceiling': float(np.mean(noise_estimates)),
        'bootstrap_noise_ceiling_std': float(np.std(noise_estimates)),
        'all_results': all_results,
        'best_config': best_config,
        'best_val_acc': best_val,
    }, f, indent=2)

# ─── Figure: Noise ceiling analysis ──────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: bootstrap noise ceiling distribution
ax = axes[0]
ax.hist(noise_estimates, bins=10, color='steelblue', alpha=0.7, edgecolor='black')
ax.axvline(np.mean(noise_estimates), color='red', linestyle='--', linewidth=2, label=f'Mean={np.mean(noise_estimates):.3f}')
ax.axvline(0.70, color='orange', linestyle='--', linewidth=2, label='SOTA=0.70')
ax.axvline(0.50, color='gray', linestyle=':', linewidth=1.5, label='Random=0.50')
ax.set_xlabel('Accuracy', fontsize=12)
ax.set_ylabel('Count', fontsize=12)
ax.set_title('Bootstrap Noise Ceiling Estimate\n(RF on half-train, tested on other half)', fontsize=12)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)

# Right: all model results
ax = axes[1]
names = [r['name'] for r in all_results]
val_accs = [r['val'] for r in all_results]
test_accs = [r['test'] for r in all_results]

x = np.arange(len(names))
ax.scatter(x, val_accs,  s=60, color='darkorange', label='Val',  zorder=5)
ax.scatter(x, test_accs, s=60, color='green',      label='Test', zorder=5)
ax.axhline(0.70, color='red',  linestyle='--', linewidth=1.5, label='SOTA 70%')
ax.axhline(0.50, color='gray', linestyle=':',  linewidth=1.5, label='Random 50%')
ax.set_xticks(x)
ax.set_xticklabels(names, rotation=90, fontsize=7)
ax.set_ylabel('Accuracy', fontsize=12)
ax.set_title('All Model Configurations\nVal and Test Accuracy', fontsize=12)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
ax.set_ylim(0.4, 0.8)

plt.tight_layout()
plt.savefig('report/images/noise_ceiling_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved noise_ceiling_analysis.png')

print('\nDone.')
