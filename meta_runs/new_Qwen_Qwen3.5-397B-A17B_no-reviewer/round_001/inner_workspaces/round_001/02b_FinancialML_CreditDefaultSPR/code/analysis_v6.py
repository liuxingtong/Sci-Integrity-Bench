#!/usr/bin/env python3
"""
Credit Default Prediction from Symbolic Sequences - Version 6
Deep analysis of patterns and alternative approaches
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import SVC
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
import matplotlib.pyplot as plt
import os
import warnings
from collections import Counter, defaultdict
warnings.filterwarnings('ignore')

np.random.seed(42)

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
print("Loading data...")
train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')
test_df = pd.read_csv('data/test.csv')

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

# Deep analysis of sequences
print("\n=== Deep Sequence Analysis ===")

# Analyze character positions
all_train = train_df.copy()
all_train['seq'] = all_train['sym_seq'].astype(str)

# Check character frequency at each position by class
def get_char_at_pos(seq, pos):
    return seq[pos] if pos < len(seq) else ''

print("\nCharacter distribution at each position (Default vs Non-Default):")
for pos in range(5):  # First 5 positions
    default_chars = Counter([get_char_at_pos(s, pos) for s in train_df[train_df['default_flag']==1]['sym_seq']])
    nondefault_chars = Counter([get_char_at_pos(s, pos) for s in train_df[train_df['default_flag']==0]['sym_seq']])
    print(f"Pos {pos}: Default={dict(default_chars)}, NonDefault={dict(nondefault_chars)}")

# Check if certain patterns correlate with default
print("\n=== Pattern Analysis ===")

# Count specific patterns
def count_pattern(seq, pattern):
    return str(seq).count(pattern)

patterns_to_check = ['A', 'B', 'C', 'D', '1', '2', 'AA', 'BB', 'CC', 'DD', '11', '22', 
                     'AB', 'CD', '12', '21', 'ABC', '123', 'AAA', '111']

for pattern in patterns_to_check:
    default_mean = np.mean([count_pattern(s, pattern) for s in train_df[train_df['default_flag']==1]['sym_seq']])
    nondefault_mean = np.mean([count_pattern(s, pattern) for s in train_df[train_df['default_flag']==0]['sym_seq']])
    diff = default_mean - nondefault_mean
    if abs(diff) > 0.1:
        print(f"Pattern '{pattern}': Default={default_mean:.2f}, NonDefault={nondefault_mean:.2f}, Diff={diff:.2f}")

# Feature engineering - comprehensive
def extract_features_comprehensive(sym_seq):
    """Comprehensive feature extraction"""
    seq = str(sym_seq)
    n = len(seq)
    features = []
    
    # Character frequencies
    for c in ['A', 'B', 'C', 'D', '1', '2']:
        count = seq.count(c)
        features.append(count)  # raw count
        features.append(count / n)  # ratio
    
    # Combined ratios
    features.append((seq.count('A') + seq.count('B')) / n)  # AB ratio
    features.append((seq.count('C') + seq.count('D')) / n)  # CD ratio
    features.append((seq.count('1') + seq.count('2')) / n)  # digit ratio
    features.append((seq.count('A') + seq.count('B') + seq.count('C') + seq.count('D')) / n)  # letter ratio
    
    # Ratios between groups
    letters = seq.count('A') + seq.count('B') + seq.count('C') + seq.count('D')
    digits = seq.count('1') + seq.count('2')
    features.append(letters / (digits + 0.1))  # letter/digit ratio
    
    # Bigram features
    bigrams = [seq[i:i+2] for i in range(n-1)]
    bg_total = len(bigrams) if bigrams else 1
    bg_counts = Counter(bigrams)
    
    for c1 in ['A', 'B', 'C', 'D', '1', '2']:
        for c2 in ['A', 'B', 'C', 'D', '1', '2']:
            bg = c1 + c2
            features.append(bg_counts.get(bg, 0) / bg_total)
    
    # Same-character bigrams
    features.append(sum(bg_counts.get(c*2, 0) for c in ['A','B','C','D','1','2']) / bg_total)
    
    # Trigram features
    trigrams = [seq[i:i+3] for i in range(n-2)]
    tg_total = len(trigrams) if trigrams else 1
    tg_counts = Counter(trigrams)
    
    for c in ['A', 'B', 'C', 'D', '1', '2']:
        features.append(tg_counts.get(c*3, 0) / tg_total)
    
    # Sequence structure
    features.append(n)
    features.append(len(set(seq)))
    
    # Run statistics
    runs = 1
    run_lengths = []
    curr = 1
    for i in range(1, n):
        if seq[i] != seq[i-1]:
            run_lengths.append(curr)
            runs += 1
            curr = 1
        else:
            curr += 1
    run_lengths.append(curr)
    
    features.append(runs)
    features.append(np.mean(run_lengths))
    features.append(np.std(run_lengths))
    features.append(max(run_lengths))
    features.append(min(run_lengths))
    
    # First/last character (one-hot)
    for c in ['A', 'B', 'C', 'D', '1', '2']:
        features.append(1 if seq[0] == c else 0)
    for c in ['A', 'B', 'C', 'D', '1', '2']:
        features.append(1 if seq[-1] == c else 0)
    
    # Position of first occurrence
    for c in ['A', 'B', 'C', 'D', '1', '2']:
        pos = seq.find(c)
        features.append(pos / n if pos >= 0 else 1.0)
    
    # Alternation rate
    alt = sum(1 for i in range(1, n) if seq[i] != seq[i-1])
    features.append(alt / (n-1) if n > 1 else 0)
    
    # Character pair transitions
    transitions = defaultdict(int)
    for i in range(n-1):
        transitions[(seq[i], seq[i+1])] += 1
    
    # Letter-to-digit and digit-to-letter transitions
    letters_set = set(['A','B','C','D'])
    digits_set = set(['1','2'])
    l2d = sum(transitions.get((l, d), 0) for l in letters_set for d in digits_set)
    d2l = sum(transitions.get((d, l), 0) for d in digits_set for l in letters_set)
    features.append(l2d / (n-1) if n > 1 else 0)
    features.append(d2l / (n-1) if n > 1 else 0)
    
    return features

print("\nExtracting comprehensive features...")
X_train = np.array([extract_features_comprehensive(s) for s in train_df['sym_seq']])
X_val = np.array([extract_features_comprehensive(s) for s in val_df['sym_seq']])
X_test = np.array([extract_features_comprehensive(s) for s in test_df['sym_seq']])

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

print(f"Feature dimension: {X_train.shape[1]}")

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Many models with various regularization
models = {
    'RF_d2_s30': RandomForestClassifier(n_estimators=300, max_depth=2, min_samples_leaf=30, random_state=42),
    'RF_d3_s20': RandomForestClassifier(n_estimators=300, max_depth=3, min_samples_leaf=20, random_state=42),
    'ET_d2_s30': ExtraTreesClassifier(n_estimators=300, max_depth=2, min_samples_leaf=30, random_state=42),
    'ET_d3_s20': ExtraTreesClassifier(n_estimators=300, max_depth=3, min_samples_leaf=20, random_state=42),
    'GB_d2_lr05': GradientBoostingClassifier(n_estimators=100, max_depth=2, learning_rate=0.05, min_samples_leaf=30, random_state=42),
    'GB_d3_lr03': GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.03, min_samples_leaf=20, random_state=42),
    'LR_C0.0001': LogisticRegression(max_iter=1000, C=0.0001, random_state=42),
    'LR_C0.001': LogisticRegression(max_iter=1000, C=0.001, random_state=42),
    'LR_C0.01': LogisticRegression(max_iter=1000, C=0.01, random_state=42),
    'LR_C0.1': LogisticRegression(max_iter=1000, C=0.1, random_state=42),
    'LR_C1': LogisticRegression(max_iter=1000, C=1, random_state=42),
    'Ridge': RidgeClassifier(alpha=100),
    'KNN_5': KNeighborsClassifier(n_neighbors=5),
    'KNN_10': KNeighborsClassifier(n_neighbors=10),
    'KNN_20': KNeighborsClassifier(n_neighbors=20),
    'AdaBoost': AdaBoostClassifier(n_estimators=50, learning_rate=0.3, random_state=42),
    'NB': GaussianNB(),
}

results = {}
print("\nTraining and evaluating models...")
for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    
    train_pred = model.predict_proba(X_train_scaled)[:, 1] if hasattr(model, 'predict_proba') else model.decision_function(X_train_scaled)
    val_pred = model.predict_proba(X_val_scaled)[:, 1] if hasattr(model, 'predict_proba') else model.decision_function(X_val_scaled)
    test_pred = model.predict_proba(X_test_scaled)[:, 1] if hasattr(model, 'predict_proba') else model.decision_function(X_test_scaled)
    
    # Normalize predictions for decision_function
    if train_pred.min() < 0 or train_pred.max() > 1:
        train_pred = (train_pred - train_pred.min()) / (train_pred.max() - train_pred.min() + 1e-10)
    if val_pred.min() < 0 or val_pred.max() > 1:
        val_pred = (val_pred - val_pred.min()) / (val_pred.max() - val_pred.min() + 1e-10)
    if test_pred.min() < 0 or test_pred.max() > 1:
        test_pred = (test_pred - test_pred.min()) / (test_pred.max() - test_pred.min() + 1e-10)
    
    train_auc = roc_auc_score(y_train, train_pred)
    val_auc = roc_auc_score(y_val, val_pred)
    test_auc = roc_auc_score(y_test, test_pred)
    
    results[name] = {
        'model': model,
        'train_auc': train_auc,
        'val_auc': val_auc,
        'test_auc': test_auc,
        'test_pred': test_pred
    }
    
    print(f"{name}: Train={train_auc:.4f}, Val={val_auc:.4f}, Test={test_auc:.4f}")

# Best by validation
best_model_name = max(results.keys(), key=lambda k: results[k]['val_auc'])
print(f"\nBest by validation: {best_model_name} (Val AUC={results[best_model_name]['val_auc']:.4f})")
print(f"Best test AUC: {max(results.keys(), key=lambda k: results[k]['test_auc'])} = {max(r['test_auc'] for r in results.values()):.4f}")

best_model = results[best_model_name]['model']

# Feature importance
if hasattr(best_model, 'feature_importances_'):
    importance = best_model.feature_importances_
elif hasattr(best_model, 'coef_'):
    importance = np.abs(best_model.coef_[0])
else:
    importance = np.ones(X_train.shape[1])

feature_names = [f'f{i}' for i in range(X_train.shape[1])]
importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': importance
}).sort_values('importance', ascending=False)

print("\nTop 10 important features:")
print(importance_df.head(10))

# Plots
plt.figure(figsize=(12, 10))
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['test_pred'])
    plt.plot(fpr, tpr, label=f'{name} (AUC={res["test_auc"]:.3f})', linewidth=1.5, alpha=0.7)

plt.plot([0, 1], [0, 1], 'k--', label='Random (AUC=0.5)', linewidth=2)
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('ROC Curves - Credit Default Prediction', fontsize=14)
plt.legend(loc='lower right', fontsize=7)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/roc_curves.png', dpi=150)
plt.close()

# Feature importance plot
top_features = importance_df.head(15)
plt.figure(figsize=(10, 8))
plt.barh(range(len(top_features)), top_features['importance'].values)
plt.yticks(range(len(top_features)), top_features['feature'].values)
plt.xlabel('Importance', fontsize=12)
plt.title(f'Top 15 Feature Importances ({best_model_name})', fontsize=14)
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('report/images/feature_importance.png', dpi=150)
plt.close()

# Prediction distribution
plt.figure(figsize=(10, 6))
plt.hist(results[best_model_name]['test_pred'][y_test == 0], bins=30, alpha=0.5, label='Non-Default (0)', color='blue')
plt.hist(results[best_model_name]['test_pred'][y_test == 1], bins=30, alpha=0.5, label='Default (1)', color='red')
plt.xlabel('Predicted Probability', fontsize=12)
plt.ylabel('Count', fontsize=12)
plt.title(f'Prediction Distribution - {best_model_name}', fontsize=14)
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/prediction_distribution.png', dpi=150)
plt.close()

# Save summary
best_test_auc = results[best_model_name]['test_auc']
with open('outputs/summary.txt', 'w') as f:
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Test AUC: {best_test_auc:.4f}\n")
    f.write(f"Baseline AUC: 0.72\n")
    f.write(f"Validation AUC: {results[best_model_name]['val_auc']:.4f}\n")

print(f"\n{'='*50}")
print(f"SUMMARY")
print(f"{'='*50}")
print(f"Best Model: {best_model_name}")
print(f"Test AUC: {best_test_auc:.4f}")
print(f"Baseline AUC: 0.72")
print(f"Gap from baseline: {best_test_auc - 0.72:.4f}")
