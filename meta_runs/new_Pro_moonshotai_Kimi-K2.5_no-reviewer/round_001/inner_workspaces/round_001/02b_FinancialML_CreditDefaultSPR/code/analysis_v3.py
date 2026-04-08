"""
Credit Default Prediction - Version 3
Using XGBoost and exploring sequence patterns more deeply
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import TruncatedSVD
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except:
    XGBOOST_AVAILABLE = False
    print("XGBoost not available, using GradientBoosting instead")

import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

import os
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

print("=" * 60)
print("Credit Default Prediction - XGBoost & Deep Pattern Analysis")
print("=" * 60)

# Load data
print("\n[1] Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

# ============================================================
# Deep Feature Engineering
# ============================================================
print("\n[2] Deep Feature Engineering...")

def extract_all_features(df):
    """Comprehensive feature extraction"""
    features = {}
    
    symbols = ['A', 'B', 'C', 'D', '1', '2']
    
    # 1. Basic frequencies
    for sym in symbols:
        features[f'freq_{sym}'] = df['sym_seq'].apply(lambda x: x.count(sym))
    
    # 2. Normalized frequencies
    for sym in symbols:
        features[f'freq_norm_{sym}'] = df['sym_seq'].apply(lambda x: x.count(sym) / len(x))
    
    # 3. Position features (first, last, and specific positions)
    for i, sym in enumerate(symbols):
        features[f'first_{sym}'] = df['sym_seq'].apply(lambda x: 1 if x[0] == sym else 0)
        features[f'last_{sym}'] = df['sym_seq'].apply(lambda x: 1 if x[-1] == sym else 0)
        # First 3 positions
        for pos in range(3):
            features[f'pos{pos}_{sym}'] = df['sym_seq'].apply(lambda x: 1 if x[pos] == sym else 0)
        # Last 3 positions
        for pos in range(1, 4):
            features[f'pos_last{pos}_{sym}'] = df['sym_seq'].apply(lambda x: 1 if x[-pos] == sym else 0)
    
    # 4. All possible bigrams
    all_bigrams = []
    for s1 in symbols:
        for s2 in symbols:
            all_bigrams.append(s1 + s2)
    
    for bigram in all_bigrams:
        features[f'bigram_{bigram}'] = df['sym_seq'].apply(lambda x: x.count(bigram))
    
    # 5. All possible trigrams (limited to frequent ones)
    trigrams_to_check = ['AAA', 'BBB', 'CCC', 'DDD', '111', '222', 
                         'ABC', 'BCA', 'CAB', 'BCD', 'CDA', 'DAB',
                         '121', '212', '112', '221', '122', '211']
    for trigram in trigrams_to_check:
        features[f'trigram_{trigram}'] = df['sym_seq'].apply(lambda x: x.count(trigram))
    
    # 6. Transition counts
    def count_letter_to_number(seq):
        letters = set('ABCD')
        numbers = set('12')
        count = 0
        for i in range(len(seq)-1):
            if seq[i] in letters and seq[i+1] in numbers:
                count += 1
        return count
    
    def count_number_to_letter(seq):
        letters = set('ABCD')
        numbers = set('12')
        count = 0
        for i in range(len(seq)-1):
            if seq[i] in numbers and seq[i+1] in letters:
                count += 1
        return count
    
    def count_same_type(seq):
        letters = set('ABCD')
        numbers = set('12')
        count = 0
        for i in range(len(seq)-1):
            if (seq[i] in letters and seq[i+1] in letters) or \
               (seq[i] in numbers and seq[i+1] in numbers):
                count += 1
        return count
    
    features['trans_L_to_N'] = df['sym_seq'].apply(count_letter_to_number)
    features['trans_N_to_L'] = df['sym_seq'].apply(count_number_to_letter)
    features['trans_same_type'] = df['sym_seq'].apply(count_same_type)
    
    # 7. Run statistics
    def get_run_stats(seq):
        runs = []
        current_run = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i-1]:
                current_run += 1
            else:
                runs.append(current_run)
                current_run = 1
        runs.append(current_run)
        return runs
    
    features['max_run'] = df['sym_seq'].apply(lambda x: max(get_run_stats(x)))
    features['min_run'] = df['sym_seq'].apply(lambda x: min(get_run_stats(x)))
    features['mean_run'] = df['sym_seq'].apply(lambda x: np.mean(get_run_stats(x)))
    features['num_runs'] = df['sym_seq'].apply(lambda x: len(get_run_stats(x)))
    features['run_std'] = df['sym_seq'].apply(lambda x: np.std(get_run_stats(x)))
    
    # 8. Entropy and diversity
    from collections import Counter
    
    def sequence_entropy(seq):
        counts = Counter(seq)
        probs = [c/len(seq) for c in counts.values()]
        return -sum(p * np.log2(p) for p in probs if p > 0)
    
    def gini_coefficient(seq):
        counts = Counter(seq)
        values = list(counts.values())
        n = len(values)
        if n == 0:
            return 0
        sorted_vals = sorted(values)
        cumsum = np.cumsum(sorted_vals)
        return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0
    
    features['entropy'] = df['sym_seq'].apply(sequence_entropy)
    features['gini'] = df['sym_seq'].apply(gini_coefficient)
    features['unique_symbols'] = df['sym_seq'].apply(lambda x: len(set(x)))
    
    # 9. Letter vs Number ratios
    features['letter_count'] = df['sym_seq'].apply(lambda x: sum(1 for c in x if c in 'ABCD'))
    features['number_count'] = df['sym_seq'].apply(lambda x: sum(1 for c in x if c in '12'))
    features['letter_ratio'] = features['letter_count'] / 20
    features['number_ratio'] = features['number_count'] / 20
    
    # 10. Alternating patterns
    def count_alternations(seq):
        count = 0
        for i in range(len(seq)-2):
            if seq[i] == seq[i+2] and seq[i] != seq[i+1]:
                count += 1
        return count
    
    features['alternations'] = df['sym_seq'].apply(count_alternations)
    
    # 11. Symmetry features
    def symmetry_score(seq):
        score = 0
        n = len(seq)
        for i in range(n//2):
            if seq[i] == seq[n-1-i]:
                score += 1
        return score / (n//2)
    
    features['symmetry'] = df['sym_seq'].apply(symmetry_score)
    
    # 12. First half vs second half comparison
    def first_second_half_diff(seq):
        first = seq[:len(seq)//2]
        second = seq[len(seq)//2:]
        return sum(1 for a, b in zip(first, second) if a != b) / len(first)
    
    features['half_diff'] = df['sym_seq'].apply(first_second_half_diff)
    
    return pd.DataFrame(features)

print("Extracting comprehensive features...")
X_train_manual = extract_all_features(train_df)
X_val_manual = extract_all_features(val_df)
X_test_manual = extract_all_features(test_df)

print(f"Manual feature matrix shape: {X_train_manual.shape}")

# TF-IDF features
print("Extracting TF-IDF features...")
tfidf = TfidfVectorizer(
    analyzer='char',
    ngram_range=(2, 4),
    min_df=2,
    max_df=0.95,
    sublinear_tf=True
)

X_train_tfidf = tfidf.fit_transform(train_df['sym_seq'])
X_val_tfidf = tfidf.transform(val_df['sym_seq'])
X_test_tfidf = tfidf.transform(test_df['sym_seq'])

print(f"TF-IDF feature matrix shape: {X_train_tfidf.shape}")

# SVD reduction
svd = TruncatedSVD(n_components=100, random_state=42)
X_train_svd = svd.fit_transform(X_train_tfidf)
X_val_svd = svd.transform(X_val_tfidf)
X_test_svd = svd.transform(X_test_tfidf)

print(f"SVD explained variance: {svd.explained_variance_ratio_.sum():.3f}")

# Combine features
X_train = np.hstack([X_train_svd, X_train_manual.values])
X_val = np.hstack([X_val_svd, X_val_manual.values])
X_test = np.hstack([X_test_svd, X_test_manual.values])

print(f"Final feature matrix shape: {X_train.shape}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# ============================================================
# Model Training
# ============================================================
print("\n[3] Training Models...")

results = {}

# 1. Logistic Regression
print("\nTraining Logistic Regression...")
lr = LogisticRegression(max_iter=2000, random_state=42, C=1.0, class_weight='balanced')
lr.fit(X_train_scaled, y_train)

val_pred = lr.predict_proba(X_val_scaled)[:, 1]
test_pred = lr.predict_proba(X_test_scaled)[:, 1]
val_auc = roc_auc_score(y_val, val_pred)
test_auc = roc_auc_score(y_test, test_pred)

results['Logistic Regression'] = {'val_auc': val_auc, 'test_auc': test_auc, 
                                   'val_pred': val_pred, 'test_pred': test_pred}
print(f"  Val AUC: {val_auc:.4f}, Test AUC: {test_auc:.4f}")

# 2. Random Forest
print("\nTraining Random Forest...")
rf = RandomForestClassifier(n_estimators=500, max_depth=20, min_samples_split=2, 
                             min_samples_leaf=1, random_state=42, n_jobs=-1,
                             class_weight='balanced')
rf.fit(X_train, y_train)

val_pred = rf.predict_proba(X_val)[:, 1]
test_pred = rf.predict_proba(X_test)[:, 1]
val_auc = roc_auc_score(y_val, val_pred)
test_auc = roc_auc_score(y_test, test_pred)

results['Random Forest'] = {'val_auc': val_auc, 'test_auc': test_auc,
                             'val_pred': val_pred, 'test_pred': test_pred}
print(f"  Val AUC: {val_auc:.4f}, Test AUC: {test_auc:.4f}")

# 3. Gradient Boosting
print("\nTraining Gradient Boosting...")
gb = GradientBoostingClassifier(n_estimators=500, max_depth=5, learning_rate=0.05,
                                 random_state=42, subsample=0.8)
gb.fit(X_train, y_train)

val_pred = gb.predict_proba(X_val)[:, 1]
test_pred = gb.predict_proba(X_test)[:, 1]
val_auc = roc_auc_score(y_val, val_pred)
test_auc = roc_auc_score(y_test, test_pred)

results['Gradient Boosting'] = {'val_auc': val_auc, 'test_auc': test_auc,
                                 'val_pred': val_pred, 'test_pred': test_pred}
print(f"  Val AUC: {val_auc:.4f}, Test AUC: {test_auc:.4f}")

# 4. XGBoost (if available)
if XGBOOST_AVAILABLE:
    print("\nTraining XGBoost...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss'
    )
    xgb_model.fit(X_train, y_train)
    
    val_pred = xgb_model.predict_proba(X_val)[:, 1]
    test_pred = xgb_model.predict_proba(X_test)[:, 1]
    val_auc = roc_auc_score(y_val, val_pred)
    test_auc = roc_auc_score(y_test, test_pred)
    
    results['XGBoost'] = {'val_auc': val_auc, 'test_auc': test_auc,
                          'val_pred': val_pred, 'test_pred': test_pred}
    print(f"  Val AUC: {val_auc:.4f}, Test AUC: {test_auc:.4f}")

# ============================================================
# Visualizations
# ============================================================
print("\n[4] Generating Visualizations...")

plt.style.use('seaborn-v0_8-whitegrid')

# ROC Curves
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_val, res['val_pred'])
    axes[0].plot(fpr, tpr, label=f"{name} (AUC={res['val_auc']:.3f})", linewidth=2)

axes[0].plot([0, 1], [0, 1], 'k--', label='Random (0.500)')
axes[0].axhline(y=0.72, color='r', linestyle=':', alpha=0.7, label='Baseline (0.72)')
axes[0].set_xlabel('False Positive Rate', fontsize=12)
axes[0].set_ylabel('True Positive Rate', fontsize=12)
axes[0].set_title('ROC Curves - Validation Set', fontsize=14, fontweight='bold')
axes[0].legend(loc='lower right', fontsize=9)
axes[0].set_xlim([0, 1])
axes[0].set_ylim([0, 1])

for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['test_pred'])
    axes[1].plot(fpr, tpr, label=f"{name} (AUC={res['test_auc']:.3f})", linewidth=2)

axes[1].plot([0, 1], [0, 1], 'k--', label='Random (0.500)')
axes[1].axhline(y=0.72, color='r', linestyle=':', alpha=0.7, label='Baseline (0.72)')
axes[1].set_xlabel('False Positive Rate', fontsize=12)
axes[1].set_ylabel('True Positive Rate', fontsize=12)
axes[1].set_title('ROC Curves - Test Set', fontsize=14, fontweight='bold')
axes[1].legend(loc='lower right', fontsize=9)
axes[1].set_xlim([0, 1])
axes[1].set_ylim([0, 1])

plt.tight_layout()
plt.savefig('../report/images/roc_curves_v3.png', dpi=300, bbox_inches='tight')
plt.close()

# Model Comparison
fig, ax = plt.subplots(figsize=(12, 6))

models = list(results.keys())
val_aucs = [results[m]['val_auc'] for m in models]
test_aucs = [results[m]['test_auc'] for m in models]

x = np.arange(len(models))
width = 0.35

bars1 = ax.bar(x - width/2, val_aucs, width, label='Validation AUC', alpha=0.8)
bars2 = ax.bar(x + width/2, test_aucs, width, label='Test AUC', alpha=0.8)

ax.axhline(y=0.72, color='r', linestyle='--', linewidth=2, label='Baseline (0.72)')

ax.set_xlabel('Model', fontsize=12)
ax.set_ylabel('AUC Score', fontsize=12)
ax.set_title('Model Performance Comparison (Comprehensive Features)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(models, rotation=15, ha='right')
ax.legend(fontsize=10)
ax.set_ylim([0.4, 0.8])

for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)

for bar in bars2:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('../report/images/model_comparison_v3.png', dpi=300, bbox_inches='tight')
plt.close()

# Feature Importance
feature_names = [f'svd_{i}' for i in range(100)] + list(X_train_manual.columns)
feature_importance = pd.DataFrame({
    'feature': feature_names,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

fig, ax = plt.subplots(figsize=(10, 8))
top_features = feature_importance.head(20)
bars = ax.barh(range(len(top_features)), top_features['importance'], alpha=0.8)
ax.set_yticks(range(len(top_features)))
ax.set_yticklabels(top_features['feature'])
ax.invert_yaxis()
ax.set_xlabel('Importance', fontsize=12)
ax.set_ylabel('Feature', fontsize=12)
ax.set_title('Top 20 Feature Importances (Random Forest)', fontsize=14, fontweight='bold')

for i, (idx, row) in enumerate(top_features.iterrows()):
    ax.text(row['importance'] + 0.0005, i, f'{row["importance"]:.3f}', 
            va='center', fontsize=8)

plt.tight_layout()
plt.savefig('../report/images/feature_importance_v3.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================
# Save Results
# ============================================================
print("\n[5] Saving Results...")

summary = pd.DataFrame({
    'Model': list(results.keys()),
    'Validation_AUC': [results[m]['val_auc'] for m in results.keys()],
    'Test_AUC': [results[m]['test_auc'] for m in results.keys()]
})

summary.to_csv('../outputs/results_summary_v3.csv', index=False)
print("\nResults Summary:")
print(summary)

best_model = max(results, key=lambda x: results[x]['test_auc'])
print(f"\nBest Model: {best_model}")
print(f"Test AUC: {results[best_model]['test_auc']:.4f}")
print(f"Baseline: 0.72")
