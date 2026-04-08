"""
SPR Benchmark: Symbolic Pattern Reasoning Classification - Enhanced Version
Binary classification of symbolic sequences with hidden rule.
Using advanced feature engineering to capture symbolic patterns.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Load data
print("Loading data...")
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

print(f"Train shape: {train.shape}")
print(f"Val shape: {val.shape}")
print(f"Test shape: {test.shape}")

# Extract feature columns
feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f"Number of features: {len(feature_cols)}")

# Parse tokens into shape and color components
# Token format: Shape+Color (e.g., 'Tr' = Triangle-red)
SHAPES = {'T': 0, 'S': 1, 'C': 2, 'D': 3}  # Triangle, Square, Circle, Diamond
COLORS = {'r': 0, 'g': 1, 'b': 2, 'y': 3}  # red, green, blue, yellow

def parse_token(token):
    """Parse a token into shape and color components."""
    shape = token[0]
    color = token[1]
    return SHAPES[shape], COLORS[color]

def extract_features(df, feature_cols):
    """Extract rich features from symbolic sequences."""
    n_samples = len(df)
    n_positions = len(feature_cols)
    
    # Basic features: shape and color at each position
    shape_features = np.zeros((n_samples, n_positions))
    color_features = np.zeros((n_samples, n_positions))
    
    for i, col in enumerate(feature_cols):
        for j, token in enumerate(df[col]):
            shape, color = parse_token(token)
            shape_features[j, i] = shape
            color_features[j, i] = color
    
    features = []
    
    # 1. Raw shape and color features
    features.append(shape_features)
    features.append(color_features)
    
    # 2. Shape/color counts per sequence
    shape_counts = np.zeros((n_samples, 4))
    color_counts = np.zeros((n_samples, 4))
    for i in range(4):
        shape_counts[:, i] = (shape_features == i).sum(axis=1)
        color_counts[:, i] = (color_features == i).sum(axis=1)
    features.append(shape_counts)
    features.append(color_counts)
    
    # 3. Position-based features (first, last tokens)
    features.append(shape_features[:, [0, -1]])  # First and last shapes
    features.append(color_features[:, [0, -1]])  # First and last colors
    
    # 4. Transition features (consecutive same shape/color)
    shape_transitions = np.zeros((n_samples, n_positions - 1))
    color_transitions = np.zeros((n_samples, n_positions - 1))
    for i in range(n_positions - 1):
        shape_transitions[:, i] = (shape_features[:, i] == shape_features[:, i+1]).astype(int)
        color_transitions[:, i] = (color_features[:, i] == color_features[:, i+1]).astype(int)
    features.append(shape_transitions)
    features.append(color_transitions)
    
    # 5. Count of transitions
    features.append(shape_transitions.sum(axis=1, keepdims=True))
    features.append(color_transitions.sum(axis=1, keepdims=True))
    
    # 6. Unique shapes/colors per sequence
    unique_shapes = np.array([(shape_features[i] == j).any(axis=0).sum() for i in range(n_samples) for j in range(4)]).reshape(n_samples, 4)
    unique_colors = np.array([(color_features[i] == j).any(axis=0).sum() for i in range(n_samples) for j in range(4)]).reshape(n_samples, 4)
    features.append(unique_shapes)
    features.append(unique_colors)
    
    # 7. Pattern features: specific shape-color combinations
    for shape_idx in range(4):
        for color_idx in range(4):
            combo = ((shape_features == shape_idx) & (color_features == color_idx)).astype(int)
            features.append(combo.sum(axis=1, keepdims=True))
    
    # 8. Position parity features (odd/even positions)
    odd_positions = shape_features[:, 1::2].mean(axis=1, keepdims=True)
    even_positions = shape_features[:, 0::2].mean(axis=1, keepdims=True)
    features.append(odd_positions)
    features.append(even_positions)
    
    # Concatenate all features
    X = np.hstack(features)
    return X

print("\nExtracting features...")
X_train = extract_features(train, feature_cols)
X_val = extract_features(val, feature_cols)
X_test = extract_features(test, feature_cols)

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"Feature matrix shapes: Train {X_train.shape}, Val {X_val.shape}, Test {X_test.shape}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Define models to benchmark
models = {
    'Random Forest': RandomForestClassifier(n_estimators=300, max_depth=20, min_samples_split=5, random_state=42, n_jobs=-1),
    'Extra Trees': ExtraTreesClassifier(n_estimators=300, max_depth=20, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=300, max_depth=5, learning_rate=0.1, random_state=42),
    'Logistic Regression': LogisticRegression(max_iter=2000, C=1.0, random_state=42),
    'SVM (RBF)': SVC(kernel='rbf', C=1.0, random_state=42),
    'MLP': MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42, early_stopping=True),
}

# Store results
results = []

print("\n" + "="*60)
print("Training and evaluating models...")
print("="*60)

for name, model in models.items():
    print(f"\n--- {name} ---")
    
    # Use scaled data for LR, SVM, and MLP
    if name in ['Logistic Regression', 'SVM (RBF)', 'MLP']:
        model.fit(X_train_scaled, y_train)
        train_pred = model.predict(X_train_scaled)
        val_pred = model.predict(X_val_scaled)
        test_pred = model.predict(X_test_scaled)
    else:
        model.fit(X_train, y_train)
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        test_pred = model.predict(X_test)
    
    # Calculate accuracies
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

# Create results DataFrame
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('Test Acc', ascending=False)
print("\n" + "="*60)
print("SUMMARY RESULTS (sorted by Test Accuracy)")
print("="*60)
print(results_df.to_string(index=False))

# Save results
results_df.to_csv('../outputs/model_results_v2.csv', index=False)
print("\nResults saved to outputs/model_results_v2.csv")

# SOTA baseline
SOTA_BASELINE = 0.70

# Create visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Bar chart comparing accuracies
x = np.arange(len(results_df))
width = 0.25

ax1 = axes[0]
bars1 = ax1.bar(x - width, results_df['Train Acc'], width, label='Train', color='steelblue', alpha=0.8)
bars2 = ax1.bar(x, results_df['Val Acc'], width, label='Validation', color='forestgreen', alpha=0.8)
bars3 = ax1.bar(x + width, results_df['Test Acc'], width, label='Test', color='coral', alpha=0.8)

# Add SOTA baseline line
ax1.axhline(y=SOTA_BASELINE, color='red', linestyle='--', linewidth=2, label=f'SOTA ({SOTA_BASELINE*100:.0f}%)')

ax1.set_xlabel('Model', fontsize=12)
ax1.set_ylabel('Accuracy', fontsize=12)
ax1.set_title('Model Performance Comparison (Enhanced Features)', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(results_df['Model'], rotation=15, ha='right')
ax1.legend(loc='lower right')
ax1.set_ylim([0, 1.0])
ax1.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

# Plot 2: Test accuracy comparison with SOTA
ax2 = axes[1]
colors = ['green' if acc >= SOTA_BASELINE else 'orange' for acc in results_df['Test Acc']]
bars = ax2.barh(results_df['Model'], results_df['Test Acc'], color=colors, alpha=0.8)
ax2.axvline(x=SOTA_BASELINE, color='red', linestyle='--', linewidth=2, label=f'SOTA ({SOTA_BASELINE*100:.0f}%)')
ax2.set_xlabel('Test Accuracy', fontsize=12)
ax2.set_title('Test Accuracy vs SOTA Baseline', fontsize=14, fontweight='bold')
ax2.set_xlim([0, 1.0])
ax2.legend()
ax2.grid(axis='x', alpha=0.3)

# Add value labels
for i, (bar, acc) in enumerate(zip(bars, results_df['Test Acc'])):
    ax2.text(acc + 0.01, bar.get_y() + bar.get_height()/2, 
             f'{acc:.3f}', va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/model_comparison_v2.png', dpi=150, bbox_inches='tight')
print("Figure saved to report/images/model_comparison_v2.png")
plt.close()

# Create confusion matrix for best model
best_model_idx = results_df['Test Acc'].idxmax()
best_model_name = results_df.loc[best_model_idx, 'Model']
print(f"\nBest model: {best_model_name}")

# Retrain best model and get predictions
if best_model_name in ['Logistic Regression', 'SVM (RBF)', 'MLP']:
    best_model = models[best_model_name]
    best_model.fit(X_train_scaled, y_train)
    test_pred = best_model.predict(X_test_scaled)
else:
    best_model = models[best_model_name]
    best_model.fit(X_train, y_train)
    test_pred = best_model.predict(X_test)

# Confusion matrix
cm = confusion_matrix(y_test, test_pred)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Reject (0)', 'Accept (1)'],
            yticklabels=['Reject (0)', 'Accept (1)'],
            ax=ax)
ax.set_xlabel('Predicted Label', fontsize=12)
ax.set_ylabel('True Label', fontsize=12)
ax.set_title(f'Confusion Matrix - {best_model_name}', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('../report/images/confusion_matrix_v2.png', dpi=150, bbox_inches='tight')
print("Figure saved to report/images/confusion_matrix_v2.png")
plt.close()

# Feature importance for tree-based models
if hasattr(best_model, 'feature_importances_'):
    fig, ax = plt.subplots(figsize=(10, 6))
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[-20:]  # Top 20 features
    
    ax.barh(range(len(indices)), importances[indices], color='steelblue', alpha=0.8)
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels([f'Feature {i}' for i in indices])
    ax.set_xlabel('Feature Importance', fontsize=12)
    ax.set_title(f'Top 20 Feature Importances - {best_model_name}', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('../report/images/feature_importance_v2.png', dpi=150, bbox_inches='tight')
    print("Figure saved to report/images/feature_importance_v2.png")
    plt.close()

# Save detailed classification report
report = classification_report(y_test, test_pred, target_names=['Reject (0)', 'Accept (1)'])
with open('../outputs/classification_report_v2.txt', 'w') as f:
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Test Accuracy: {results_df.loc[best_model_idx, 'Test Acc']:.4f}\n")
    f.write("\n" + "="*60 + "\n")
    f.write(report)

print("\nClassification report saved to outputs/classification_report_v2.txt")

# Print final summary
print("\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)
print(f"SOTA Baseline: {SOTA_BASELINE*100:.1f}%")
print(f"Best Model: {best_model_name}")
print(f"Best Test Accuracy: {results_df['Test Acc'].max()*100:.2f}%")
print(f"Improvement over SOTA: {(results_df['Test Acc'].max() - SOTA_BASELINE)*100:.2f} percentage points")
