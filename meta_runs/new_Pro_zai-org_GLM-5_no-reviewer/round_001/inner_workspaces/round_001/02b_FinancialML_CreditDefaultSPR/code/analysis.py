import pandas as pd
import numpy as np
from collections import Counter
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, AdaBoostClassifier, ExtraTreesClassifier
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# Load data
print("Loading data...")
train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')
test_df = pd.read_csv('data/test.csv')

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
print(f"Train default rate: {train_df['default_flag'].mean():.3f}")

# Simple feature engineering - just position one-hot
def extract_features(seq):
    features = {}
    chars = ['A', 'B', 'C', 'D', '1', '2']
    
    # One-hot per position
    for i, c in enumerate(seq):
        for ch in chars:
            features[f'p{i}_{ch}'] = 1 if c == ch else 0
    
    # Character frequencies
    for c in chars:
        features[f'freq_{c}'] = seq.count(c) / len(seq)
    
    return features

def create_features(df):
    return pd.DataFrame([extract_features(seq) for seq in df['sym_seq']])

print("\nExtracting features...")
X_train = create_features(train_df)
X_val = create_features(val_df)
X_test = create_features(test_df)

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

print(f"Features: {X_train.shape[1]}")

# Standardize
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_val_s = scaler.transform(X_val)
X_test_s = scaler.transform(X_test)

# Combine train+val
X_trainval = np.vstack([X_train_s, X_val_s])
X_trainval_raw = np.vstack([X_train, X_val])
y_trainval = np.concatenate([y_train, y_val])

print("\n" + "="*50)
print("Model Training")
print("="*50)

results = {}

# 1. Logistic Regression
print("\n1. Logistic Regression...")
best_lr = None
best_score = 0
for C in [0.0001, 0.001, 0.01, 0.1, 1.0, 10.0]:
    lr = LogisticRegression(C=C, max_iter=5000, random_state=42)
    lr.fit(X_train_s, y_train)
    val_auc = roc_auc_score(y_val, lr.predict_proba(X_val_s)[:, 1])
    test_auc = roc_auc_score(y_test, lr.predict_proba(X_test_s)[:, 1])
    train_auc = roc_auc_score(y_train, lr.predict_proba(X_train_s)[:, 1])
    print(f"  C={C}: train={train_auc:.4f}, val={val_auc:.4f}, test={test_auc:.4f}")
    if val_auc > best_score:
        best_score = val_auc
        best_lr = {'C': C, 'train_auc': train_auc, 'val_auc': val_auc, 'test_auc': test_auc, 'model': lr}

lr_final = LogisticRegression(C=best_lr['C'], max_iter=5000, random_state=42)
lr_final.fit(X_trainval, y_trainval)
best_lr['test_auc_final'] = roc_auc_score(y_test, lr_final.predict_proba(X_test_s)[:, 1])
best_lr['test_pred'] = lr_final.predict_proba(X_test_s)[:, 1]
print(f"  Final (train+val): test={best_lr['test_auc_final']:.4f}")
results['Logistic Regression'] = best_lr

# 2. Gradient Boosting
print("\n2. Gradient Boosting...")
best_gb = None
best_score = 0
for depth in [1, 2, 3]:
    for lr_rate in [0.01, 0.05, 0.1]:
        for n_est in [50, 100, 200]:
            gb = GradientBoostingClassifier(n_estimators=n_est, max_depth=depth,
                                            learning_rate=lr_rate, min_samples_leaf=20,
                                            subsample=0.8, random_state=42)
            gb.fit(X_train, y_train)
            val_auc = roc_auc_score(y_val, gb.predict_proba(X_val)[:, 1])
            test_auc = roc_auc_score(y_test, gb.predict_proba(X_test)[:, 1])
            train_auc = roc_auc_score(y_train, gb.predict_proba(X_train)[:, 1])
            if val_auc > best_score:
                best_score = val_auc
                best_gb = {'depth': depth, 'lr': lr_rate, 'n_est': n_est,
                          'train_auc': train_auc, 'val_auc': val_auc, 'test_auc': test_auc, 'model': gb}

print(f"  Best: depth={best_gb['depth']}, lr={best_gb['lr']}, n_est={best_gb['n_est']}")
print(f"  train={best_gb['train_auc']:.4f}, val={best_gb['val_auc']:.4f}, test={best_gb['test_auc']:.4f}")

gb_final = GradientBoostingClassifier(n_estimators=best_gb['n_est'], max_depth=best_gb['depth'],
                                       learning_rate=best_gb['lr'], min_samples_leaf=20,
                                       subsample=0.8, random_state=42)
gb_final.fit(X_trainval_raw, y_trainval)
best_gb['test_auc_final'] = roc_auc_score(y_test, gb_final.predict_proba(X_test)[:, 1])
best_gb['test_pred'] = gb_final.predict_proba(X_test)[:, 1]
print(f"  Final (train+val): test={best_gb['test_auc_final']:.4f}")
results['Gradient Boosting'] = best_gb

# 3. Random Forest
print("\n3. Random Forest...")
best_rf = None
best_score = 0
for depth in [2, 3, 4, 5]:
    for min_leaf in [10, 20, 30]:
        rf = RandomForestClassifier(n_estimators=300, max_depth=depth,
                                    min_samples_leaf=min_leaf, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        val_auc = roc_auc_score(y_val, rf.predict_proba(X_val)[:, 1])
        test_auc = roc_auc_score(y_test, rf.predict_proba(X_test)[:, 1])
        train_auc = roc_auc_score(y_train, rf.predict_proba(X_train)[:, 1])
        if val_auc > best_score:
            best_score = val_auc
            best_rf = {'depth': depth, 'min_leaf': min_leaf,
                      'train_auc': train_auc, 'val_auc': val_auc, 'test_auc': test_auc, 'model': rf}

print(f"  Best: depth={best_rf['depth']}, min_leaf={best_rf['min_leaf']}")
print(f"  train={best_rf['train_auc']:.4f}, val={best_rf['val_auc']:.4f}, test={best_rf['test_auc']:.4f}")

rf_final = RandomForestClassifier(n_estimators=300, max_depth=best_rf['depth'],
                                  min_samples_leaf=best_rf['min_leaf'], random_state=42, n_jobs=-1)
rf_final.fit(X_trainval_raw, y_trainval)
best_rf['test_auc_final'] = roc_auc_score(y_test, rf_final.predict_proba(X_test)[:, 1])
best_rf['test_pred'] = rf_final.predict_proba(X_test)[:, 1]
print(f"  Final (train+val): test={best_rf['test_auc_final']:.4f}")
results['Random Forest'] = best_rf

# 4. AdaBoost
print("\n4. AdaBoost...")
best_ab = None
best_score = 0
for lr_rate in [0.01, 0.1, 0.5, 1.0]:
    for n_est in [50, 100, 200]:
        ab = AdaBoostClassifier(n_estimators=n_est, learning_rate=lr_rate, random_state=42)
        ab.fit(X_train, y_train)
        val_auc = roc_auc_score(y_val, ab.predict_proba(X_val)[:, 1])
        test_auc = roc_auc_score(y_test, ab.predict_proba(X_test)[:, 1])
        train_auc = roc_auc_score(y_train, ab.predict_proba(X_train)[:, 1])
        if val_auc > best_score:
            best_score = val_auc
            best_ab = {'lr': lr_rate, 'n_est': n_est,
                      'train_auc': train_auc, 'val_auc': val_auc, 'test_auc': test_auc, 'model': ab}

print(f"  Best: lr={best_ab['lr']}, n_est={best_ab['n_est']}")
print(f"  train={best_ab['train_auc']:.4f}, val={best_ab['val_auc']:.4f}, test={best_ab['test_auc']:.4f}")

ab_final = AdaBoostClassifier(n_estimators=best_ab['n_est'], learning_rate=best_ab['lr'], random_state=42)
ab_final.fit(X_trainval_raw, y_trainval)
best_ab['test_auc_final'] = roc_auc_score(y_test, ab_final.predict_proba(X_test)[:, 1])
best_ab['test_pred'] = ab_final.predict_proba(X_test)[:, 1]
print(f"  Final (train+val): test={best_ab['test_auc_final']:.4f}")
results['AdaBoost'] = best_ab

# 5. Extra Trees
print("\n5. Extra Trees...")
best_et = None
best_score = 0
for depth in [2, 3, 4]:
    for min_leaf in [10, 20, 30]:
        et = ExtraTreesClassifier(n_estimators=300, max_depth=depth,
                                  min_samples_leaf=min_leaf, random_state=42, n_jobs=-1)
        et.fit(X_train, y_train)
        val_auc = roc_auc_score(y_val, et.predict_proba(X_val)[:, 1])
        test_auc = roc_auc_score(y_test, et.predict_proba(X_test)[:, 1])
        train_auc = roc_auc_score(y_train, et.predict_proba(X_train)[:, 1])
        if val_auc > best_score:
            best_score = val_auc
            best_et = {'depth': depth, 'min_leaf': min_leaf,
                      'train_auc': train_auc, 'val_auc': val_auc, 'test_auc': test_auc, 'model': et}

print(f"  Best: depth={best_et['depth']}, min_leaf={best_et['min_leaf']}")
print(f"  train={best_et['train_auc']:.4f}, val={best_et['val_auc']:.4f}, test={best_et['test_auc']:.4f}")

et_final = ExtraTreesClassifier(n_estimators=300, max_depth=best_et['depth'],
                                min_samples_leaf=best_et['min_leaf'], random_state=42, n_jobs=-1)
et_final.fit(X_trainval_raw, y_trainval)
best_et['test_auc_final'] = roc_auc_score(y_test, et_final.predict_proba(X_test)[:, 1])
best_et['test_pred'] = et_final.predict_proba(X_test)[:, 1]
print(f"  Final (train+val): test={best_et['test_auc_final']:.4f}")
results['Extra Trees'] = best_et

# Best model
best_name = max(results.keys(), key=lambda x: results[x]['val_auc'])
best = results[best_name]

print(f"\n{'='*50}")
print(f"Best Model: {best_name}")
print(f"Val AUC: {best['val_auc']:.4f}")
print(f"Test AUC: {best['test_auc']:.4f}")
print(f"Test AUC (train+val): {best['test_auc_final']:.4f}")
print(f"Baseline: 0.72")
print(f"{'='*50}")

# Save results
pd.DataFrame({
    'model': list(results.keys()),
    'train_auc': [results[m]['train_auc'] for m in results],
    'val_auc': [results[m]['val_auc'] for m in results],
    'test_auc': [results[m]['test_auc'] for m in results],
    'test_auc_final': [results[m]['test_auc_final'] for m in results]
}).to_csv('outputs/model_results.csv', index=False)

# Feature importance
if best_name in ['Random Forest', 'Gradient Boosting', 'Extra Trees', 'AdaBoost']:
    fi = pd.DataFrame({'feature': X_train.columns, 'importance': best['model'].feature_importances_})
    fi = fi.sort_values('importance', ascending=False)
    fi.to_csv('outputs/feature_importance.csv', index=False)
    print("\nTop 20 Features:")
    print(fi.head(20).to_string())

# Create visualizations
print("\nCreating visualizations...")

# 1. ROC Curves
plt.figure(figsize=(10, 8))
colors = ['blue', 'green', 'red', 'purple', 'orange']
for i, (name, res) in enumerate(results.items()):
    fpr, tpr, _ = roc_curve(y_test, res['test_pred'])
    plt.plot(fpr, tpr, color=colors[i % len(colors)], lw=2, 
             label=f"{name} (AUC = {res['test_auc_final']:.3f})")

plt.plot([0, 1], [0, 1], 'k--', lw=2, label='Random (AUC = 0.500)')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('ROC Curves for Credit Default Prediction', fontsize=14)
plt.legend(loc="lower right", fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/roc_curves.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: roc_curves.png")

# 2. Model Comparison Bar Chart
models = list(results.keys())
train_aucs = [results[m]['train_auc'] for m in models]
val_aucs = [results[m]['val_auc'] for m in models]
test_aucs = [results[m]['test_auc_final'] for m in models]

x = np.arange(len(models))
width = 0.25

fig, ax = plt.subplots(figsize=(12, 6))
rects1 = ax.bar(x - width, train_aucs, width, label='Train AUC', color='steelblue')
rects2 = ax.bar(x, val_aucs, width, label='Val AUC', color='darkorange')
rects3 = ax.bar(x + width, test_aucs, width, label='Test AUC', color='forestgreen')

ax.axhline(y=0.72, color='red', linestyle='--', linewidth=2, label='Baseline (0.72)')
ax.set_ylabel('AUC Score', fontsize=12)
ax.set_xlabel('Model', fontsize=12)
ax.set_title('Model Performance Comparison', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=10, rotation=15)
ax.legend(loc='upper right', fontsize=10)
ax.set_ylim([0, 1.1])
ax.grid(True, alpha=0.3, axis='y')

for rects in [rects1, rects2, rects3]:
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('report/images/model_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: model_comparison.png")

# 3. Feature Importance
if best_name in ['Random Forest', 'Gradient Boosting', 'Extra Trees', 'AdaBoost']:
    plt.figure(figsize=(10, 8))
    top_features = fi.head(15)
    plt.barh(range(len(top_features)), top_features['importance'].values, color='steelblue')
    plt.yticks(range(len(top_features)), top_features['feature'].values)
    plt.xlabel('Feature Importance', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.title(f'Top 15 Feature Importance ({best_name})', fontsize=14)
    plt.gca().invert_yaxis()
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig('report/images/feature_importance.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: feature_importance.png")

# 4. Class Distribution
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
for i, (df, name) in enumerate([(train_df, 'Train'), (val_df, 'Validation'), (test_df, 'Test')]):
    counts = df['default_flag'].value_counts()
    axes[i].bar(['Non-Default (0)', 'Default (1)'], [counts.get(0, 0), counts.get(1, 0)], 
                color=['forestgreen', 'crimson'])
    axes[i].set_title(f'{name} Set\n(n={len(df)})', fontsize=12)
    axes[i].set_ylabel('Count', fontsize=10)
    for j, v in enumerate([counts.get(0, 0), counts.get(1, 0)]):
        axes[i].text(j, v + 5, str(v), ha='center', fontsize=10)

plt.suptitle('Class Distribution Across Datasets', fontsize=14)
plt.tight_layout()
plt.savefig('report/images/class_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: class_distribution.png")

# 5. Character Frequency Analysis
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

default_seqs = train_df[train_df['default_flag'] == 1]['sym_seq'].values
non_default_seqs = train_df[train_df['default_flag'] == 0]['sym_seq'].values
chars = ['A', 'B', 'C', 'D', '1', '2']

default_freqs = []
non_default_freqs = []
for c in chars:
    default_freqs.append(np.mean([seq.count(c) / len(seq) for seq in default_seqs]))
    non_default_freqs.append(np.mean([seq.count(c) / len(seq) for seq in non_default_seqs]))

x = np.arange(len(chars))
width = 0.35

axes[0].bar(x - width/2, default_freqs, width, label='Default', color='crimson')
axes[0].bar(x + width/2, non_default_freqs, width, label='Non-Default', color='forestgreen')
axes[0].set_xlabel('Character', fontsize=12)
axes[0].set_ylabel('Frequency', fontsize=12)
axes[0].set_title('Character Frequencies by Class', fontsize=12)
axes[0].set_xticks(x)
axes[0].set_xticklabels(chars)
axes[0].legend()
axes[0].grid(True, alpha=0.3, axis='y')

diff = np.array(default_freqs) - np.array(non_default_freqs)
colors = ['crimson' if d > 0 else 'forestgreen' for d in diff]
axes[1].bar(chars, diff, color=colors)
axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
axes[1].set_xlabel('Character', fontsize=12)
axes[1].set_ylabel('Frequency Difference (Default - Non-Default)', fontsize=12)
axes[1].set_title('Character Frequency Differences', fontsize=12)
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/character_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: character_analysis.png")

print("\nDone!")
