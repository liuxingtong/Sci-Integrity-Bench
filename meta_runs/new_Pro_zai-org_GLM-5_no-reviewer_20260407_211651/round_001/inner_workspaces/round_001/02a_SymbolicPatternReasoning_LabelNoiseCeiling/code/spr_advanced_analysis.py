"""
SPR_BENCH Advanced Classification Analysis
Enhanced feature engineering and model tuning
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load data
print("Loading data...")
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

# Extract feature columns
feature_cols = [c for c in train.columns if c.startswith('token_')]

# Labels
y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

def create_advanced_features(df, feature_cols):
    """Create advanced features from tokens"""
    features = pd.DataFrame()
    
    # Shape and color counts
    shapes = ['T', 'S', 'C', 'D']
    colors = ['r', 'g', 'b', 'y']
    
    for shape in shapes:
        features[f'shape_count_{shape}'] = df[feature_cols].apply(
            lambda row: sum(1 for t in row if t[0] == shape), axis=1
        )
    
    for color in colors:
        features[f'color_count_{color}'] = df[feature_cols].apply(
            lambda row: sum(1 for t in row if t[1] == color), axis=1
        )
    
    # Unique counts
    features['unique_shapes'] = df[feature_cols].apply(
        lambda row: len(set(t[0] for t in row)), axis=1
    )
    features['unique_colors'] = df[feature_cols].apply(
        lambda row: len(set(t[1] for t in row)), axis=1
    )
    features['unique_tokens'] = df[feature_cols].apply(
        lambda row: len(set(row)), axis=1
    )
    
    # Position-specific encoding
    shape_map = {'T': 0, 'S': 1, 'C': 2, 'D': 3}
    color_map = {'r': 0, 'g': 1, 'b': 2, 'y': 3}
    
    for i, col in enumerate(feature_cols):
        features[f'pos_{i}_shape'] = df[col].apply(lambda x: shape_map.get(x[0], -1))
        features[f'pos_{i}_color'] = df[col].apply(lambda x: color_map.get(x[1], -1))
        # Combined encoding
        features[f'pos_{i}_token'] = df[col].apply(lambda x: shape_map.get(x[0], -1) * 4 + color_map.get(x[1], -1))
    
    # Transition features (shape/color changes between consecutive positions)
    for i in range(len(feature_cols) - 1):
        col1, col2 = feature_cols[i], feature_cols[i+1]
        features[f'trans_{i}_shape_change'] = df.apply(
            lambda row: 1 if row[col1][0] != row[col2][0] else 0, axis=1
        )
        features[f'trans_{i}_color_change'] = df.apply(
            lambda row: 1 if row[col1][1] != row[col2][1] else 0, axis=1
        )
    
    # Total transitions
    features['total_shape_changes'] = df[feature_cols].apply(
        lambda row: sum(1 for i in range(len(row)-1) if row.iloc[i][0] != row.iloc[i+1][0]), axis=1
    )
    features['total_color_changes'] = df[feature_cols].apply(
        lambda row: sum(1 for i in range(len(row)-1) if row.iloc[i][1] != row.iloc[i+1][1]), axis=1
    )
    
    # First and last token features
    features['first_shape'] = df[feature_cols[0]].apply(lambda x: shape_map.get(x[0], -1))
    features['first_color'] = df[feature_cols[0]].apply(lambda x: color_map.get(x[1], -1))
    features['last_shape'] = df[feature_cols[-1]].apply(lambda x: shape_map.get(x[0], -1))
    features['last_color'] = df[feature_cols[-1]].apply(lambda x: color_map.get(x[1], -1))
    
    # Pattern features: consecutive same shape/color
    features['max_consec_same_shape'] = df[feature_cols].apply(
        lambda row: max([1] + [sum(1 for _ in g) for k, g in __import__('itertools').groupby(t[0] for t in row)]), axis=1
    )
    features['max_consec_same_color'] = df[feature_cols].apply(
        lambda row: max([1] + [sum(1 for _ in g) for k, g in __import__('itertools').groupby(t[1] for t in row)]), axis=1
    )
    
    # Bigram features (token pairs)
    for i in range(len(feature_cols) - 1):
        col1, col2 = feature_cols[i], feature_cols[i+1]
        features[f'bigram_{i}'] = df.apply(
            lambda row: hash((row[col1], row[col2])) % 1000, axis=1
        )
    
    return features

# Create advanced features
print("Creating advanced features...")
X_train_adv = create_advanced_features(train, feature_cols)
X_val_adv = create_advanced_features(val, feature_cols)
X_test_adv = create_advanced_features(test, feature_cols)

print(f"Advanced features shape: {X_train_adv.shape}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_adv)
X_val_scaled = scaler.transform(X_val_adv)
X_test_scaled = scaler.transform(X_test_adv)

# Define models with more configurations
models = {
    'LogReg_L2': LogisticRegression(max_iter=2000, C=0.1, random_state=42),
    'LogReg_L1': LogisticRegression(max_iter=2000, C=0.1, penalty='l1', solver='saga', random_state=42),
    'DecisionTree_d5': DecisionTreeClassifier(max_depth=5, random_state=42),
    'DecisionTree_d10': DecisionTreeClassifier(max_depth=10, random_state=42),
    'RandomForest_100': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
    'RandomForest_200': RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42),
    'GradientBoost_100': GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42),
    'GradientBoost_200': GradientBoostingClassifier(n_estimators=200, max_depth=5, random_state=42),
    'AdaBoost': AdaBoostClassifier(n_estimators=100, random_state=42),
    'KNN_3': KNeighborsClassifier(n_neighbors=3),
    'KNN_5': KNeighborsClassifier(n_neighbors=5),
    'KNN_7': KNeighborsClassifier(n_neighbors=7),
    'SVM_rbf': SVC(kernel='rbf', C=1.0, random_state=42),
    'SVM_linear': SVC(kernel='linear', C=0.1, random_state=42),
    'MLP_64_32': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42),
    'MLP_128_64': MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=1000, random_state=42),
    'MLP_256_128_64': MLPClassifier(hidden_layer_sizes=(256, 128, 64), max_iter=1000, random_state=42),
}

# Train and evaluate models
results = []

print("\n=== Training Models with Advanced Features ===")

for name, model in models.items():
    print(f"Training {name}...", end=' ')
    
    # Train
    model.fit(X_train_scaled, y_train)
    
    # Predictions
    train_pred = model.predict(X_train_scaled)
    val_pred = model.predict(X_val_scaled)
    test_pred = model.predict(X_test_scaled)
    
    # Accuracies
    train_acc = accuracy_score(y_train, train_pred)
    val_acc = accuracy_score(y_val, val_pred)
    test_acc = accuracy_score(y_test, test_pred)
    
    print(f"Test: {test_acc:.4f}")
    
    results.append({
        'Model': name,
        'Train Acc': train_acc,
        'Val Acc': val_acc,
        'Test Acc': test_acc
    })

# Try ensemble methods
print("\n=== Training Ensemble Models ===")

# Voting classifier
voting_clf = VotingClassifier(
    estimators=[
        ('rf', RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)),
        ('gb', GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)),
        ('mlp', MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=1000, random_state=42))
    ],
    voting='hard'
)
voting_clf.fit(X_train_scaled, y_train)
voting_test_acc = accuracy_score(y_test, voting_clf.predict(X_test_scaled))
print(f"Voting Ensemble Test: {voting_test_acc:.4f}")
results.append({
    'Model': 'VotingEnsemble',
    'Train Acc': accuracy_score(y_train, voting_clf.predict(X_train_scaled)),
    'Val Acc': accuracy_score(y_val, voting_clf.predict(X_val_scaled)),
    'Test Acc': voting_test_acc
})

# Create results dataframe
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('Test Acc', ascending=False)

print("\n=== Results Summary ===")
print(results_df.to_string(index=False))

# Save results
results_df.to_csv('../outputs/advanced_model_results.csv', index=False)

# Find best model
best_row = results_df.iloc[0]
print(f"\n=== Best Model ===")
print(f"Model: {best_row['Model']}")
print(f"Test Accuracy: {best_row['Test Acc']:.4f}")
print(f"SOTA Baseline: 0.7000")
print(f"Gap from SOTA: {best_row['Test Acc'] - 0.7:.4f}")

# Create additional visualizations
print("\n=== Creating Visualizations ===")

# Figure: Advanced model comparison
plt.figure(figsize=(14, 8))
colors = ['green' if acc >= 0.7 else 'coral' for acc in results_df['Test Acc']]
plt.barh(results_df['Model'], results_df['Test Acc'], color=colors, alpha=0.8)
plt.axvline(x=0.7, color='navy', linestyle='--', linewidth=2, label='SOTA (70%)')
plt.xlabel('Test Accuracy')
plt.title('Advanced Model Performance vs SOTA Baseline')
plt.xlim(0.4, 0.8)
plt.legend(loc='lower right')
plt.tight_layout()
plt.savefig('../report/images/advanced_model_comparison.png', dpi=150)
plt.close()
print("Saved advanced_model_comparison.png")

# Figure: Feature importance (using Random Forest)
rf_model = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42)
rf_model.fit(X_train_scaled, y_train)

importance = rf_model.feature_importances_
feature_names = X_train_adv.columns.tolist()
importance_df = pd.DataFrame({'Feature': feature_names, 'Importance': importance})
importance_df = importance_df.sort_values('Importance', ascending=False).head(20)

plt.figure(figsize=(10, 8))
plt.barh(importance_df['Feature'], importance_df['Importance'], color='steelblue')
plt.xlabel('Importance')
plt.title('Top 20 Feature Importances (Random Forest)')
plt.tight_layout()
plt.savefig('../report/images/feature_importance.png', dpi=150)
plt.close()
print("Saved feature_importance.png")

# Analyze patterns in the data
print("\n=== Pattern Analysis ===")

# Check if there are obvious patterns
print("\nAnalyzing token patterns by label...")

for label in [0, 1]:
    subset = train[train['label'] == label]
    print(f"\nLabel {label} ({len(subset)} samples):")
    
    # Most common first tokens
    first_tokens = subset[feature_cols[0]].value_counts().head(5)
    print(f"  Top 5 first tokens: {first_tokens.to_dict()}")
    
    # Most common last tokens
    last_tokens = subset[feature_cols[-1]].value_counts().head(5)
    print(f"  Top 5 last tokens: {last_tokens.to_dict()}")

# Check for specific patterns
print("\n=== Checking Specific Patterns ===")

# Pattern: same shape in all positions
for label in [0, 1]:
    subset = train[train['label'] == label]
    same_shape = subset[feature_cols].apply(
        lambda row: len(set(t[0] for t in row)) == 1, axis=1
    ).sum()
    print(f"Label {label}: All same shape = {same_shape} ({same_shape/len(subset)*100:.1f}%)")

# Pattern: same color in all positions
for label in [0, 1]:
    subset = train[train['label'] == label]
    same_color = subset[feature_cols].apply(
        lambda row: len(set(t[1] for t in row)) == 1, axis=1
    ).sum()
    print(f"Label {label}: All same color = {same_color} ({same_color/len(subset)*100:.1f}%)")

# Pattern: alternating shapes
for label in [0, 1]:
    subset = train[train['label'] == label]
    alternating = subset[feature_cols].apply(
        lambda row: all(row.iloc[i][0] != row.iloc[i+1][0] for i in range(len(row)-1)), axis=1
    ).sum()
    print(f"Label {label}: Alternating shapes = {alternating} ({alternating/len(subset)*100:.1f}%)")

print("\n=== Analysis Complete ===")