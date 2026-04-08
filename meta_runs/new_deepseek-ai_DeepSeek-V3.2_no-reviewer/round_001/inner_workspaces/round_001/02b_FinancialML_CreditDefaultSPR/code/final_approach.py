import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, StackingClassifier
from sklearn.feature_selection import SelectFromModel
import xgboost as xgb
import lightgbm as lgb
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Try to import xgboost and lightgbm, install if not available
try:
    import xgboost
    print("XGBoost available")
except ImportError:
    print("Installing XGBoost...")
    import subprocess
    subprocess.check_call(["pip", "install", "xgboost"])
    import xgboost

try:
    import lightgbm
    print("LightGBM available")
except ImportError:
    print("Installing LightGBM...")
    import subprocess
    subprocess.check_call(["pip", "install", "lightgbm"])
    import lightgbm

# Load data
train = pd.read_csv('../data/train.csv')
val = pd.read_csv('../data/val.csv')
test = pd.read_csv('../data/test.csv')

y_train = train['default_flag'].values
y_val = val['default_flag'].values
y_test = test['default_flag'].values

print("=== Final Comprehensive Approach ===")
print(f"Training samples: {len(train)}")

# Create comprehensive feature set
print("\n--- Creating Comprehensive Feature Set ---")

# 1. Basic symbol frequencies
symbols = ['1', '2', 'A', 'B', 'C', 'D']
basic_features = []
for df in [train, val, test]:
    features = pd.DataFrame(index=df.index)
    for sym in symbols:
        features[f'freq_{sym}'] = df['sym_seq'].apply(lambda x: x.count(sym))
    basic_features.append(features)

train_basic, val_basic, test_basic = basic_features

# 2. N-gram features (3-grams as they worked best)
from sklearn.feature_extraction.text import CountVectorizer
vectorizer = CountVectorizer(analyzer='char', ngram_range=(3, 3))
X_train_ngram = vectorizer.fit_transform(train['sym_seq'])
X_val_ngram = vectorizer.transform(val['sym_seq'])
X_test_ngram = vectorizer.transform(test['sym_seq'])

# Convert to dense array for stacking
X_train_ngram_dense = X_train_ngram.toarray()
X_val_ngram_dense = X_val_ngram.toarray()
X_test_ngram_dense = X_test_ngram.toarray()

print(f"N-gram features: {X_train_ngram_dense.shape[1]}")

# 3. Position encoding
def position_one_hot(sequences):
    n_samples = len(sequences)
    n_features = 20 * 6
    X = np.zeros((n_samples, n_features))
    symbol_to_idx = {'1': 0, '2': 1, 'A': 2, 'B': 3, 'C': 4, 'D': 5}
    for i, seq in enumerate(sequences):
        for pos, symbol in enumerate(seq):
            feature_idx = pos * 6 + symbol_to_idx[symbol]
            X[i, feature_idx] = 1
    return X

X_train_pos = position_one_hot(train['sym_seq'])
X_val_pos = position_one_hot(val['sym_seq'])
X_test_pos = position_one_hot(test['sym_seq'])

print(f"Position encoding features: {X_train_pos.shape[1]}")

# 4. Advanced sequence features
def extract_advanced_features(sequences):
    features = []
    for seq in sequences:
        # Run length statistics
        runs = []
        current_run = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i-1]:
                current_run += 1
            else:
                runs.append(current_run)
                current_run = 1
        runs.append(current_run)
        
        # Transition counts
        transitions = 0
        for i in range(1, len(seq)):
            if seq[i] != seq[i-1]:
                transitions += 1
        
        # Digit vs letter patterns
        digits = sum(1 for c in seq if c in ['1', '2'])
        letters = sum(1 for c in seq if c in ['A', 'B', 'C', 'D'])
        
        features.append([
            np.mean(runs), np.std(runs), np.max(runs), np.min(runs),  # run stats
            transitions / len(seq),  # transition rate
            digits, letters, digits - letters,  # digit/letter stats
            len(set(seq))  # unique symbols
        ])
    
    return np.array(features)

X_train_adv = extract_advanced_features(train['sym_seq'])
X_val_adv = extract_advanced_features(val['sym_seq'])
X_test_adv = extract_advanced_features(test['sym_seq'])

print(f"Advanced features: {X_train_adv.shape[1]}")

# Combine all features
X_train_combined = np.hstack([
    train_basic.values,
    X_train_ngram_dense,
    X_train_pos,
    X_train_adv
])

X_val_combined = np.hstack([
    val_basic.values,
    X_val_ngram_dense,
    X_val_pos,
    X_val_adv
])

X_test_combined = np.hstack([
    test_basic.values,
    X_test_ngram_dense,
    X_test_pos,
    X_test_adv
])

print(f"\nCombined features shape: {X_train_combined.shape}")
print(f"Total features: {X_train_combined.shape[1]}")

# Standardize
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_combined)
X_val_scaled = scaler.transform(X_val_combined)
X_test_scaled = scaler.transform(X_test_combined)

# Feature selection using RandomForest
print("\n--- Feature Selection ---")
selector = SelectFromModel(
    RandomForestClassifier(n_estimators=100, random_state=42),
    threshold='median'
)
X_train_selected = selector.fit_transform(X_train_scaled, y_train)
X_val_selected = selector.transform(X_val_scaled)
X_test_selected = selector.transform(X_test_scaled)

print(f"Selected features: {X_train_selected.shape[1]} (from {X_train_scaled.shape[1]})")

# Try advanced models
print("\n--- Training Advanced Models ---")

models = {
    'XGBoost': xgb.XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
        eval_metric='logloss'
    ),
    'LightGBM': lgb.LGBMClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    ),
    'GradientBoosting': GradientBoostingClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    ),
    'RandomForest': RandomForestClassifier(
        n_estimators=200,
        max_depth=5,
        random_state=42
    )
}

results = {}
best_auc = 0
best_model = None
best_model_name = ""

for name, model in models.items():
    print(f"\nTraining {name}...")
    
    # Train
    model.fit(X_train_selected, y_train)
    
    # Validate
    y_val_pred = model.predict_proba(X_val_selected)[:, 1]
    val_auc = roc_auc_score(y_val, y_val_pred)
    
    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train_selected, y_train,
                                 cv=cv, scoring='roc_auc', n_jobs=-1)
    
    print(f"  Validation AUC: {val_auc:.4f}")
    print(f"  CV AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    
    results[name] = {
        'model': model,
        'val_auc': val_auc,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std()
    }
    
    if val_auc > best_auc:
        best_auc = val_auc
        best_model = model
        best_model_name = name

print(f"\n=== Best Model: {best_model_name} with Validation AUC: {best_auc:.4f} ===")

# Evaluate on test set
y_test_pred = best_model.predict_proba(X_test_selected)[:, 1]
test_auc = roc_auc_score(y_test, y_test_pred)
print(f"Test AUC: {test_auc:.4f}")

# Compare with baseline
baseline_auc = 0.72
print(f"Baseline AUC: {baseline_auc:.4f}")
print(f"Difference from baseline: {test_auc - baseline_auc:.4f}")

# Create visualizations
os.makedirs('../report/images', exist_ok=True)

# 1. Model comparison
plt.figure(figsize=(10, 6))
model_names = list(results.keys())
val_aucs = [results[name]['val_auc'] for name in model_names]

bars = plt.bar(model_names, val_aucs, color=['blue', 'green', 'orange', 'red'])
plt.axhline(y=baseline_auc, color='black', linestyle='--', linewidth=2, 
            label=f'Baseline AUC={baseline_auc}')
plt.axhline(y=test_auc, color='purple', linestyle='--', linewidth=2,
            label=f'Best Test AUC={test_auc:.4f}')

plt.xlabel('Model')
plt.ylabel('Validation AUC')
plt.title('Advanced Model Performance')
plt.ylim(0.4, 0.8)
plt.legend()

# Add value labels
for bar, auc in zip(bars, val_aucs):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
             f'{auc:.3f}', ha='center', va='bottom')

plt.tight_layout()
plt.savefig('../report/images/advanced_models_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. ROC curve
plt.figure(figsize=(8, 6))
fpr, tpr, _ = roc_curve(y_test, y_test_pred)
plt.plot(fpr, tpr, label=f'{best_model_name} (AUC = {test_auc:.3f})', linewidth=2)
plt.plot([0, 1], [0, 1], 'k--', label='Random (AUC = 0.5)')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title(f'ROC Curve - {best_model_name}')
plt.legend(loc='lower right')
plt.grid(True, alpha=0.3)
plt.savefig('../report/images/final_roc_curve.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Feature importance for tree-based models
if hasattr(best_model, 'feature_importances_'):
    plt.figure(figsize=(12, 8))
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[::-1][:20]
    
    plt.barh(range(20), importances[indices[:20]], align='center')
    plt.yticks(range(20), [f'Feature {i}' for i in indices[:20]])
    plt.xlabel('Feature Importance')
    plt.title('Top 20 Feature Importances')
    plt.tight_layout()
    plt.savefig('../report/images/final_feature_importance.png', dpi=300, bbox_inches='tight')
    plt.close()

# 4. Prediction distribution
plt.figure(figsize=(10, 6))
plt.subplot(1, 2, 1)
plt.hist(y_test_pred[y_test == 0], bins=30, alpha=0.7, label='No Default', color='blue')
plt.hist(y_test_pred[y_test == 1], bins=30, alpha=0.7, label='Default', color='red')
plt.xlabel('Predicted Probability')
plt.ylabel('Frequency')
plt.title('Prediction Distribution')
plt.legend()

plt.subplot(1, 2, 2)
from sklearn.calibration import calibration_curve
prob_true, prob_pred = calibration_curve(y_test, y_test_pred, n_bins=10)
plt.plot(prob_pred, prob_true, marker='o', linewidth=2)
plt.plot([0, 1], [0, 1], 'k--', label='Perfectly Calibrated')
plt.xlabel('Mean Predicted Probability')
plt.ylabel('Fraction of Positives')
plt.title('Calibration Curve')
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/prediction_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualizations saved to report/images/")

# Save final results
with open('../outputs/final_results.txt', 'w') as f:
    f.write("Final Model Results\n")
    f.write("="*50 + "\n\n")
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Validation AUC: {best_auc:.4f}\n")
    f.write(f"Test AUC: {test_auc:.4f}\n")
    f.write(f"Baseline AUC: {baseline_auc:.4f}\n")
    f.write(f"Difference from baseline: {test_auc - baseline_auc:.4f}\n\n")
    
    f.write("All Model Results:\n")
    for name in results:
        f.write(f"  {name}: Val AUC={results[name]['val_auc']:.4f}, "
                f"CV AUC={results[name]['cv_mean']:.4f} (+/- {results[name]['cv_std']*2:.4f})\n")
    
    f.write("\nFeature Engineering Summary:\n")
    f.write(f"  Basic symbol frequencies: {train_basic.shape[1]} features\n")
    f.write(f"  3-gram features: {X_train_ngram_dense.shape[1]} features\n")
    f.write(f"  Position encoding: {X_train_pos.shape[1]} features\n")
    f.write(f"  Advanced sequence features: {X_train_adv.shape[1]} features\n")
    f.write(f"  Total combined features: {X_train_combined.shape[1]} features\n")
    f.write(f"  After selection: {X_train_selected.shape[1]} features\n")

print("\n=== Final Approach Complete ===")