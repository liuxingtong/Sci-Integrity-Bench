"""
Credit Default Prediction from Symbolic Sequences
Financial ML Research Task
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Create output directories
import os
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

print("=" * 60)
print("Credit Default Prediction from Symbolic Sequences")
print("=" * 60)

# Load data
print("\n[1] Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

print(f"Train samples: {len(train_df)}")
print(f"Val samples: {len(val_df)}")
print(f"Test samples: {len(test_df)}")

# Check class distribution
print("\n[2] Class distribution:")
print(f"Train - Default rate: {train_df['default_flag'].mean():.3f}")
print(f"Val - Default rate: {val_df['default_flag'].mean():.3f}")
print(f"Test - Default rate: {test_df['default_flag'].mean():.3f}")

# Analyze sequence characteristics
print("\n[3] Sequence characteristics:")
seq_lengths = train_df['sym_seq'].apply(len)
print(f"Sequence length: {seq_lengths.iloc[0]} (all same: {seq_lengths.nunique() == 1})")

# Get unique symbols
all_symbols = set()
for seq in train_df['sym_seq']:
    all_symbols.update(list(seq))
print(f"Unique symbols: {sorted(all_symbols)}")

# ============================================================
# Feature Engineering
# ============================================================
print("\n[4] Feature Engineering...")

def extract_features(df):
    """Extract features from symbolic sequences"""
    features = {}
    
    # 1. Character frequency features
    symbols = ['A', 'B', 'C', 'D', '1', '2']
    for sym in symbols:
        features[f'freq_{sym}'] = df['sym_seq'].apply(lambda x: x.count(sym))
    
    # 2. Position-based features (first and last positions)
    features['first_char_A'] = df['sym_seq'].apply(lambda x: 1 if x[0] == 'A' else 0)
    features['first_char_B'] = df['sym_seq'].apply(lambda x: 1 if x[0] == 'B' else 0)
    features['first_char_C'] = df['sym_seq'].apply(lambda x: 1 if x[0] == 'C' else 0)
    features['first_char_D'] = df['sym_seq'].apply(lambda x: 1 if x[0] == 'D' else 0)
    features['first_char_1'] = df['sym_seq'].apply(lambda x: 1 if x[0] == '1' else 0)
    features['first_char_2'] = df['sym_seq'].apply(lambda x: 1 if x[0] == '2' else 0)
    
    features['last_char_A'] = df['sym_seq'].apply(lambda x: 1 if x[-1] == 'A' else 0)
    features['last_char_B'] = df['sym_seq'].apply(lambda x: 1 if x[-1] == 'B' else 0)
    features['last_char_C'] = df['sym_seq'].apply(lambda x: 1 if x[-1] == 'C' else 0)
    features['last_char_D'] = df['sym_seq'].apply(lambda x: 1 if x[-1] == 'D' else 0)
    features['last_char_1'] = df['sym_seq'].apply(lambda x: 1 if x[-1] == '1' else 0)
    features['last_char_2'] = df['sym_seq'].apply(lambda x: 1 if x[-1] == '2' else 0)
    
    # 3. N-gram features (character bigrams and trigrams)
    def get_ngrams(seq, n):
        return [seq[i:i+n] for i in range(len(seq)-n+1)]
    
    # Count specific patterns
    features['count_AB'] = df['sym_seq'].apply(lambda x: x.count('AB'))
    features['count_BA'] = df['sym_seq'].apply(lambda x: x.count('BA'))
    features['count_CD'] = df['sym_seq'].apply(lambda x: x.count('CD'))
    features['count_DC'] = df['sym_seq'].apply(lambda x: x.count('DC'))
    features['count_12'] = df['sym_seq'].apply(lambda x: x.count('12'))
    features['count_21'] = df['sym_seq'].apply(lambda x: x.count('21'))
    
    # 4. Transition features (letter to number, number to letter)
    def count_transitions(seq):
        letters = set('ABCD')
        numbers = set('12')
        transitions = 0
        for i in range(len(seq)-1):
            if (seq[i] in letters and seq[i+1] in numbers) or \
               (seq[i] in numbers and seq[i+1] in letters):
                transitions += 1
        return transitions
    
    features['letter_number_transitions'] = df['sym_seq'].apply(count_transitions)
    
    # 5. Run-length features (consecutive same characters)
    def max_run_length(seq):
        max_run = 1
        current_run = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i-1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1
        return max_run
    
    features['max_run_length'] = df['sym_seq'].apply(max_run_length)
    features['num_runs'] = df['sym_seq'].apply(lambda x: sum(1 for i in range(1, len(x)) if x[i] != x[i-1]) + 1)
    
    # 6. Entropy-based features
    def sequence_entropy(seq):
        from collections import Counter
        counts = Counter(seq)
        probs = [c/len(seq) for c in counts.values()]
        return -sum(p * np.log2(p) for p in probs if p > 0)
    
    features['entropy'] = df['sym_seq'].apply(sequence_entropy)
    
    # 7. Ratio features
    features['letter_ratio'] = df['sym_seq'].apply(lambda x: sum(1 for c in x if c in 'ABCD') / len(x))
    features['number_ratio'] = df['sym_seq'].apply(lambda x: sum(1 for c in x if c in '12') / len(x))
    
    return pd.DataFrame(features)

# Extract features
print("Extracting features from training data...")
X_train = extract_features(train_df)
y_train = train_df['default_flag'].values

print("Extracting features from validation data...")
X_val = extract_features(val_df)
y_val = val_df['default_flag'].values

print("Extracting features from test data...")
X_test = extract_features(test_df)
y_test = test_df['default_flag'].values

print(f"Feature matrix shape: {X_train.shape}")
print(f"Features: {list(X_train.columns)}")

# Save feature data
X_train.to_csv('../outputs/X_train_features.csv', index=False)
X_val.to_csv('../outputs/X_val_features.csv', index=False)
X_test.to_csv('../outputs/X_test_features.csv', index=False)

# ============================================================
# Model Training and Evaluation
# ============================================================
print("\n[5] Training Models...")

# Scale features for logistic regression
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

results = {}

# 1. Logistic Regression
print("\nTraining Logistic Regression...")
lr = LogisticRegression(max_iter=1000, random_state=42, C=1.0)
lr.fit(X_train_scaled, y_train)

val_pred_lr = lr.predict_proba(X_val_scaled)[:, 1]
test_pred_lr = lr.predict_proba(X_test_scaled)[:, 1]

val_auc_lr = roc_auc_score(y_val, val_pred_lr)
test_auc_lr = roc_auc_score(y_test, test_pred_lr)

results['Logistic Regression'] = {
    'val_auc': val_auc_lr,
    'test_auc': test_auc_lr,
    'val_pred': val_pred_lr,
    'test_pred': test_pred_lr,
    'model': lr
}

print(f"  Val AUC: {val_auc_lr:.4f}")
print(f"  Test AUC: {test_auc_lr:.4f}")

# 2. Random Forest
print("\nTraining Random Forest...")
rf = RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_split=5, 
                             random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)

val_pred_rf = rf.predict_proba(X_val)[:, 1]
test_pred_rf = rf.predict_proba(X_test)[:, 1]

val_auc_rf = roc_auc_score(y_val, val_pred_rf)
test_auc_rf = roc_auc_score(y_test, test_pred_rf)

results['Random Forest'] = {
    'val_auc': val_auc_rf,
    'test_auc': test_auc_rf,
    'val_pred': val_pred_rf,
    'test_pred': test_pred_rf,
    'model': rf
}

print(f"  Val AUC: {val_auc_rf:.4f}")
print(f"  Test AUC: {test_auc_rf:.4f}")

# 3. Gradient Boosting
print("\nTraining Gradient Boosting...")
gb = GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.1,
                                 random_state=42)
gb.fit(X_train, y_train)

val_pred_gb = gb.predict_proba(X_val)[:, 1]
test_pred_gb = gb.predict_proba(X_test)[:, 1]

val_auc_gb = roc_auc_score(y_val, val_pred_gb)
test_auc_gb = roc_auc_score(y_test, test_pred_gb)

results['Gradient Boosting'] = {
    'val_auc': val_auc_gb,
    'test_auc': test_auc_gb,
    'val_pred': val_pred_gb,
    'test_pred': test_pred_gb,
    'model': gb
}

print(f"  Val AUC: {val_auc_gb:.4f}")
print(f"  Test AUC: {test_auc_gb:.4f}")

# ============================================================
# Feature Importance Analysis
# ============================================================
print("\n[6] Feature Importance Analysis...")

# Get feature importance from Random Forest
feature_importance = pd.DataFrame({
    'feature': X_train.columns,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 10 Most Important Features (Random Forest):")
print(feature_importance.head(10))

# Save feature importance
feature_importance.to_csv('../outputs/feature_importance.csv', index=False)

# ============================================================
# Visualization
# ============================================================
print("\n[7] Generating Visualizations...")

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# 1. ROC Curves
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Validation ROC curves
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_val, res['val_pred'])
    axes[0].plot(fpr, tpr, label=f"{name} (AUC={res['val_auc']:.3f})", linewidth=2)

axes[0].plot([0, 1], [0, 1], 'k--', label='Random (AUC=0.500)')
axes[0].set_xlabel('False Positive Rate', fontsize=12)
axes[0].set_ylabel('True Positive Rate', fontsize=12)
axes[0].set_title('ROC Curves - Validation Set', fontsize=14, fontweight='bold')
axes[0].legend(loc='lower right', fontsize=10)
axes[0].set_xlim([0, 1])
axes[0].set_ylim([0, 1])

# Test ROC curves
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['test_pred'])
    axes[1].plot(fpr, tpr, label=f"{name} (AUC={res['test_auc']:.3f})", linewidth=2)

axes[1].plot([0, 1], [0, 1], 'k--', label='Random (AUC=0.500)')
axes[1].set_xlabel('False Positive Rate', fontsize=12)
axes[1].set_ylabel('True Positive Rate', fontsize=12)
axes[1].set_title('ROC Curves - Test Set', fontsize=14, fontweight='bold')
axes[1].legend(loc='lower right', fontsize=10)
axes[1].set_xlim([0, 1])
axes[1].set_ylim([0, 1])

plt.tight_layout()
plt.savefig('../report/images/roc_curves.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: roc_curves.png")

# 2. Model Performance Comparison
fig, ax = plt.subplots(figsize=(10, 6))

models = list(results.keys())
val_aucs = [results[m]['val_auc'] for m in models]
test_aucs = [results[m]['test_auc'] for m in models]

x = np.arange(len(models))
width = 0.35

bars1 = ax.bar(x - width/2, val_aucs, width, label='Validation AUC', alpha=0.8)
bars2 = ax.bar(x + width/2, test_aucs, width, label='Test AUC', alpha=0.8)

# Add baseline line
ax.axhline(y=0.72, color='r', linestyle='--', linewidth=2, label='Published Baseline (0.72)')

ax.set_xlabel('Model', fontsize=12)
ax.set_ylabel('AUC Score', fontsize=12)
ax.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(models, rotation=15, ha='right')
ax.legend(fontsize=10)
ax.set_ylim([0.5, 0.85])

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

for bar in bars2:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('../report/images/model_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: model_comparison.png")

# 3. Feature Importance Plot
fig, ax = plt.subplots(figsize=(10, 8))

top_features = feature_importance.head(15)
bars = ax.barh(range(len(top_features)), top_features['importance'], alpha=0.8)
ax.set_yticks(range(len(top_features)))
ax.set_yticklabels(top_features['feature'])
ax.invert_yaxis()
ax.set_xlabel('Importance', fontsize=12)
ax.set_ylabel('Feature', fontsize=12)
ax.set_title('Top 15 Feature Importances (Random Forest)', fontsize=14, fontweight='bold')

# Add value labels
for i, (idx, row) in enumerate(top_features.iterrows()):
    ax.text(row['importance'] + 0.001, i, f'{row["importance"]:.3f}', 
            va='center', fontsize=9)

plt.tight_layout()
plt.savefig('../report/images/feature_importance.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: feature_importance.png")

# 4. Class Distribution
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

datasets = [('Train', train_df), ('Validation', val_df), ('Test', test_df)]

for idx, (name, df) in enumerate(datasets):
    counts = df['default_flag'].value_counts()
    axes[idx].pie(counts.values, labels=['No Default (0)', 'Default (1)'], 
                  autopct='%1.1f%%', startangle=90, colors=['lightblue', 'salmon'])
    axes[idx].set_title(f'{name} Set\n(n={len(df)})', fontsize=12, fontweight='bold')

plt.suptitle('Class Distribution Across Datasets', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('../report/images/class_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: class_distribution.png")

# 5. Confusion Matrix for Best Model (on test set)
best_model_name = max(results, key=lambda x: results[x]['test_auc'])
best_model = results[best_model_name]

# Get predictions
if best_model_name == 'Logistic Regression':
    y_pred = (best_model['test_pred'] > 0.5).astype(int)
else:
    y_pred = (best_model['test_pred'] > 0.5).astype(int)

cm = confusion_matrix(y_test, y_pred)

fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['No Default', 'Default'],
            yticklabels=['No Default', 'Default'])
ax.set_xlabel('Predicted', fontsize=12)
ax.set_ylabel('Actual', fontsize=12)
ax.set_title(f'Confusion Matrix - {best_model_name} (Test Set)', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/confusion_matrix.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: confusion_matrix.png")

# 6. Prediction Distribution
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for idx, (name, res) in enumerate(results.items()):
    axes[idx].hist(res['test_pred'][y_test == 0], bins=20, alpha=0.6, 
                   label='No Default', color='lightblue', density=True)
    axes[idx].hist(res['test_pred'][y_test == 1], bins=20, alpha=0.6, 
                   label='Default', color='salmon', density=True)
    axes[idx].set_xlabel('Predicted Probability', fontsize=11)
    axes[idx].set_ylabel('Density', fontsize=11)
    axes[idx].set_title(f'{name}\nTest AUC: {res["test_auc"]:.3f}', fontsize=12, fontweight='bold')
    axes[idx].legend(fontsize=9)

plt.suptitle('Prediction Distribution by True Class', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('../report/images/prediction_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: prediction_distribution.png")

# ============================================================
# Save Results Summary
# ============================================================
print("\n[8] Saving Results Summary...")

summary = pd.DataFrame({
    'Model': list(results.keys()),
    'Validation_AUC': [results[m]['val_auc'] for m in results.keys()],
    'Test_AUC': [results[m]['test_auc'] for m in results.keys()]
})

summary.to_csv('../outputs/results_summary.csv', index=False)
print(summary)

# Save predictions
for name, res in results.items():
    pred_df = pd.DataFrame({
        'id': test_df['id'],
        'true_label': y_test,
        'predicted_prob': res['test_pred']
    })
    pred_df.to_csv(f'../outputs/predictions_{name.replace(" ", "_").lower()}.csv', index=False)

print("\n" + "=" * 60)
print("Analysis Complete!")
print("=" * 60)
print(f"\nBest Model: {best_model_name}")
print(f"Test AUC: {results[best_model_name]['test_auc']:.4f}")
print(f"Baseline AUC: 0.72")
print(f"Improvement: {results[best_model_name]['test_auc'] - 0.72:+.4f}")
