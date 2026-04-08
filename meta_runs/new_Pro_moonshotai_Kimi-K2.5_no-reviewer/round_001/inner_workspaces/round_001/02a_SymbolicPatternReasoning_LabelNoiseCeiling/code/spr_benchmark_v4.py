"""
SPR Benchmark: Symbolic Pattern Reasoning Classification - Version 4
Using XGBoost with strong regularization and pattern analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# Load data
print("Loading data...")
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
n_positions = len(feature_cols)
print(f"Number of positions: {n_positions}")

# Parse tokens
SHAPES = {'T': 0, 'S': 1, 'C': 2, 'D': 3}
COLORS = {'r': 0, 'g': 1, 'b': 2, 'y': 3}

def parse_token(token):
    return SHAPES[token[0]], COLORS[token[1]]

def extract_comprehensive_features(df, feature_cols):
    """Extract comprehensive features with strong inductive bias."""
    n_samples = len(df)
    n_pos = len(feature_cols)
    
    # Parse all tokens
    shapes = np.zeros((n_samples, n_pos), dtype=int)
    colors = np.zeros((n_samples, n_pos), dtype=int)
    
    for i, col in enumerate(feature_cols):
        for j, token in enumerate(df[col]):
            s, c = parse_token(token)
            shapes[j, i] = s
            colors[j, i] = c
    
    features = []
    feature_names = []
    
    # 1. Raw shape/color at each position (ordinal)
    for i in range(n_pos):
        features.append(shapes[:, i:i+1])
        features.append(colors[:, i:i+1])
        feature_names.extend([f'shape_pos{i}', f'color_pos{i}'])
    
    # 2. Count of each shape/color in sequence
    for s in range(4):
        features.append((shapes == s).sum(axis=1, keepdims=True))
        feature_names.append(f'shape_{s}_count')
    for c in range(4):
        features.append((colors == c).sum(axis=1, keepdims=True))
        feature_names.append(f'color_{c}_count')
    
    # 3. Position of first/last occurrence of each shape/color
    for s in range(4):
        has_shape = (shapes == s)
        first_pos = np.where(has_shape.any(axis=1), has_shape.argmax(axis=1), -1)
        last_pos = np.where(has_shape.any(axis=1), n_pos - 1 - np.fliplr(has_shape).argmax(axis=1), -1)
        features.append(first_pos.reshape(-1, 1))
        features.append(last_pos.reshape(-1, 1))
        feature_names.extend([f'shape_{s}_first', f'shape_{s}_last'])
    
    for c in range(4):
        has_color = (colors == c)
        first_pos = np.where(has_color.any(axis=1), has_color.argmax(axis=1), -1)
        last_pos = np.where(has_color.any(axis=1), n_pos - 1 - np.fliplr(has_color).argmax(axis=1), -1)
        features.append(first_pos.reshape(-1, 1))
        features.append(last_pos.reshape(-1, 1))
        feature_names.extend([f'color_{c}_first', f'color_{c}_last'])
    
    # 4. Consecutive runs
    shape_runs = np.zeros((n_samples, 1))
    color_runs = np.zeros((n_samples, 1))
    for i in range(n_samples):
        s_run = 1
        c_run = 1
        for j in range(1, n_pos):
            if shapes[i, j] == shapes[i, j-1]:
                s_run += 1
            if colors[i, j] == colors[i, j-1]:
                c_run += 1
        shape_runs[i] = s_run
        color_runs[i] = c_run
    features.extend([shape_runs, color_runs])
    feature_names.extend(['shape_run_len', 'color_run_len'])
    
    # 5. Alternating patterns
    shape_alternates = np.zeros((n_samples, 1))
    color_alternates = np.zeros((n_samples, 1))
    for i in range(n_samples):
        s_alt = sum(1 for j in range(1, n_pos) if shapes[i, j] != shapes[i, j-1])
        c_alt = sum(1 for j in range(1, n_pos) if colors[i, j] != colors[i, j-1])
        shape_alternates[i] = s_alt
        color_alternates[i] = c_alt
    features.extend([shape_alternates, color_alternates])
    feature_names.extend(['shape_alternations', 'color_alternations'])
    
    # 6. Specific pattern: same shape at positions 0 and 4 (middle)
    mid_match = (shapes[:, 0:1] == shapes[:, 4:5]).astype(int)
    features.append(mid_match)
    feature_names.append('shape_pos0_eq_pos4')
    
    # 7. Symmetry features
    sym_shapes = (shapes == np.fliplr(shapes)).all(axis=1, keepdims=True).astype(int)
    sym_colors = (colors == np.fliplr(colors)).all(axis=1, keepdims=True).astype(int)
    features.extend([sym_shapes, sym_colors])
    feature_names.extend(['shape_symmetric', 'color_symmetric'])
    
    # 8. Pair features (position pairs)
    for i in range(n_pos):
        for j in range(i+1, n_pos):
            shape_match = (shapes[:, i:i+1] == shapes[:, j:j+1]).astype(int)
            color_match = (colors[:, i:i+1] == colors[:, j:j+1]).astype(int)
            features.extend([shape_match, color_match])
            feature_names.extend([f'shape_{i}_eq_{j}', f'color_{i}_eq_{j}'])
    
    X = np.hstack(features)
    return X, feature_names

print("\nExtracting features...")
X_train, feature_names = extract_comprehensive_features(train, feature_cols)
X_val, _ = extract_comprehensive_features(val, feature_cols)
X_test, _ = extract_comprehensive_features(test, feature_cols)

print(f"Feature matrix shapes: Train {X_train.shape}, Val {X_val.shape}, Test {X_test.shape}")
print(f"Total features: {len(feature_names)}")

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Define models with strong regularization
models = {
    'XGBoost (tuned)': xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.7,
        colsample_bytree=0.7,
        reg_alpha=1.0,
        reg_lambda=2.0,
        random_state=42,
        eval_metric='logloss'
    ),
    'XGBoost (deep)': xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.6,
        colsample_bytree=0.6,
        reg_alpha=2.0,
        reg_lambda=3.0,
        random_state=42,
        eval_metric='logloss'
    ),
    'Random Forest (tuned)': RandomForestClassifier(
        n_estimators=500,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    ),
    'Gradient Boosting (tuned)': GradientBoostingClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.7,
        random_state=42
    ),
    'Logistic Regression (L2)': LogisticRegression(
        max_iter=2000,
        C=0.1,
        penalty='l2',
        random_state=42
    ),
    'Logistic Regression (L1)': LogisticRegression(
        max_iter=2000,
        C=0.1,
        penalty='l1',
        solver='saga',
        random_state=42
    ),
}

results = []

print("\n" + "="*60)
print("Training and evaluating models...")
print("="*60)

for name, model in models.items():
    print(f"\n--- {name} ---")
    
    if 'Logistic' in name:
        model.fit(X_train_scaled, y_train)
        train_pred = model.predict(X_train_scaled)
        val_pred = model.predict(X_val_scaled)
        test_pred = model.predict(X_test_scaled)
    else:
        model.fit(X_train, y_train)
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        test_pred = model.predict(X_test)
    
    train_acc = accuracy_score(y_train, train_pred)
    val_acc = accuracy_score(y_val, val_pred)
    test_acc = accuracy_score(y_test, test_pred)
    
    print(f"Train Accuracy: {train_acc:.4f}")
    print(f"Val Accuracy:   {val_acc:.4f}")
    print(f"Test Accuracy:  {test_acc:.4f}")
    
    results.append({
        'Model': name,
        'Train Acc': train_acc,
        'Val Acc': val_acc,
        'Test Acc': test_acc
    })

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('Test Acc', ascending=False)

print("\n" + "="*60)
print("SUMMARY RESULTS")
print("="*60)
print(results_df.to_string(index=False))

results_df.to_csv('../outputs/model_results_v4.csv', index=False)

SOTA_BASELINE = 0.70

# Visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

x = np.arange(len(results_df))
width = 0.25

ax1 = axes[0]
bars1 = ax1.bar(x - width, results_df['Train Acc'], width, label='Train', color='steelblue', alpha=0.8)
bars2 = ax1.bar(x, results_df['Val Acc'], width, label='Validation', color='forestgreen', alpha=0.8)
bars3 = ax1.bar(x + width, results_df['Test Acc'], width, label='Test', color='coral', alpha=0.8)
ax1.axhline(y=SOTA_BASELINE, color='red', linestyle='--', linewidth=2, label=f'SOTA ({SOTA_BASELINE*100:.0f}%)')
ax1.set_xlabel('Model', fontsize=12)
ax1.set_ylabel('Accuracy', fontsize=12)
ax1.set_title('Model Performance (Tuned Regularization)', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(results_df['Model'], rotation=20, ha='right')
ax1.legend(loc='lower right')
ax1.set_ylim([0, 1.0])
ax1.grid(axis='y', alpha=0.3)

for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

ax2 = axes[1]
colors = ['green' if acc >= SOTA_BASELINE else 'orange' for acc in results_df['Test Acc']]
bars = ax2.barh(results_df['Model'], results_df['Test Acc'], color=colors, alpha=0.8)
ax2.axvline(x=SOTA_BASELINE, color='red', linestyle='--', linewidth=2, label=f'SOTA ({SOTA_BASELINE*100:.0f}%)')
ax2.set_xlabel('Test Accuracy', fontsize=12)
ax2.set_title('Test Accuracy vs SOTA Baseline', fontsize=14, fontweight='bold')
ax2.set_xlim([0, 1.0])
ax2.legend()
ax2.grid(axis='x', alpha=0.3)

for i, (bar, acc) in enumerate(zip(bars, results_df['Test Acc'])):
    ax2.text(acc + 0.01, bar.get_y() + bar.get_height()/2, f'{acc:.3f}', va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/model_comparison_v4.png', dpi=150, bbox_inches='tight')
print("\nFigure saved to report/images/model_comparison_v4.png")
plt.close()

# Best model analysis
best_model_idx = results_df['Test Acc'].idxmax()
best_model_name = results_df.loc[best_model_idx, 'Model']
print(f"\nBest model: {best_model_name}")

if 'Logistic' in best_model_name:
    best_model = models[best_model_name]
    best_model.fit(X_train_scaled, y_train)
    test_pred = best_model.predict(X_test_scaled)
else:
    best_model = models[best_model_name]
    best_model.fit(X_train, y_train)
    test_pred = best_model.predict(X_test)

cm = confusion_matrix(y_test, test_pred)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Reject (0)', 'Accept (1)'],
            yticklabels=['Reject (0)', 'Accept (1)'], ax=ax)
ax.set_xlabel('Predicted Label', fontsize=12)
ax.set_ylabel('True Label', fontsize=12)
ax.set_title(f'Confusion Matrix - {best_model_name}', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('../report/images/confusion_matrix_v4.png', dpi=150, bbox_inches='tight')
print("Figure saved to report/images/confusion_matrix_v4.png")
plt.close()

# Feature importance
if hasattr(best_model, 'feature_importances_'):
    fig, ax = plt.subplots(figsize=(12, 8))
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[-30:]
    
    ax.barh(range(len(indices)), importances[indices], color='steelblue', alpha=0.8)
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels([feature_names[i] if i < len(feature_names) else f'Feature {i}' for i in indices], fontsize=9)
    ax.set_xlabel('Feature Importance', fontsize=12)
    ax.set_title(f'Top 30 Feature Importances - {best_model_name}', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('../report/images/feature_importance_v4.png', dpi=150, bbox_inches='tight')
    print("Figure saved to report/images/feature_importance_v4.png")
    plt.close()

# Save report
report = classification_report(y_test, test_pred, target_names=['Reject (0)', 'Accept (1)'])
with open('../outputs/classification_report_v4.txt', 'w') as f:
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Test Accuracy: {results_df.loc[best_model_idx, 'Test Acc']:.4f}\n")
    f.write("\n" + "="*60 + "\n")
    f.write(report)

print("\nClassification report saved to outputs/classification_report_v4.txt")

print("\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)
print(f"SOTA Baseline: {SOTA_BASELINE*100:.1f}%")
print(f"Best Model: {best_model_name}")
print(f"Best Test Accuracy: {results_df['Test Acc'].max()*100:.2f}%")
print(f"Gap to SOTA: {(SOTA_BASELINE - results_df['Test Acc'].max())*100:.2f} percentage points")
