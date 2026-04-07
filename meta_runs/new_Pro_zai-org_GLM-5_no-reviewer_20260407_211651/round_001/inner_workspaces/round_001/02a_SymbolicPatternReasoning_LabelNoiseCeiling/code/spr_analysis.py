"""
SPR_BENCH Classification Analysis
Binary classification of symbolic sequences
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
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

print(f"Train size: {len(train)}")
print(f"Val size: {len(val)}")
print(f"Test size: {len(test)}")

# Extract feature columns
feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f"Number of tokens per sequence: {len(feature_cols)}")
print(f"Token columns: {feature_cols}")

# Analyze data distribution
print("\n=== Data Distribution ===")
print(f"Train label distribution: {train['label'].value_counts().to_dict()}")
print(f"Val label distribution: {val['label'].value_counts().to_dict()}")
print(f"Test label distribution: {test['label'].value_counts().to_dict()}")

# Analyze token vocabulary
all_tokens = set()
for col in feature_cols:
    all_tokens.update(train[col].unique())
print(f"\nUnique tokens: {sorted(all_tokens)}")
print(f"Number of unique tokens: {len(all_tokens)}")

# Extract shapes and colors
shapes = set(t[0] for t in all_tokens)
colors = set(t[1] for t in all_tokens)
print(f"Shapes: {sorted(shapes)}")
print(f"Colors: {sorted(colors)}")

def encode_features(df, feature_cols, encoders=None, fit=False):
    """Encode token features using label encoding"""
    encoded = pd.DataFrame()
    
    if encoders is None:
        encoders = {}
    
    for col in feature_cols:
        if fit:
            le = LabelEncoder()
            encoded[col] = le.fit_transform(df[col])
            encoders[col] = le
        else:
            le = encoders[col]
            # Handle unseen labels
            encoded[col] = df[col].apply(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
    
    return encoded, encoders

def create_feature_engineering(df, feature_cols):
    """Create additional features from tokens"""
    features = pd.DataFrame()
    
    # Shape counts
    for shape in ['T', 'S', 'C', 'D']:
        features[f'shape_count_{shape}'] = df[feature_cols].apply(
            lambda row: sum(1 for t in row if t[0] == shape), axis=1
        )
    
    # Color counts
    for color in ['r', 'g', 'b', 'y']:
        features[f'color_count_{color}'] = df[feature_cols].apply(
            lambda row: sum(1 for t in row if t[1] == color), axis=1
        )
    
    # Unique shapes and colors
    features['unique_shapes'] = df[feature_cols].apply(
        lambda row: len(set(t[0] for t in row)), axis=1
    )
    features['unique_colors'] = df[feature_cols].apply(
        lambda row: len(set(t[1] for t in row)), axis=1
    )
    
    # Position-specific features
    for i, col in enumerate(feature_cols):
        features[f'pos_{i}_shape'] = df[col].apply(lambda x: ord(x[0]))
        features[f'pos_{i}_color'] = df[col].apply(lambda x: ord(x[1]))
    
    return features

# Prepare features
print("\n=== Preparing Features ===")

# Method 1: Label encoding
X_train_encoded, encoders = encode_features(train, feature_cols, fit=True)
X_val_encoded, _ = encode_features(val, feature_cols, encoders)
X_test_encoded, _ = encode_features(test, feature_cols, encoders)

# Method 2: Feature engineering
X_train_fe = create_feature_engineering(train, feature_cols)
X_val_fe = create_feature_engineering(val, feature_cols)
X_test_fe = create_feature_engineering(test, feature_cols)

# Labels
y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"Encoded features shape: {X_train_encoded.shape}")
print(f"Engineered features shape: {X_train_fe.shape}")

# Define models to test
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Decision Tree': DecisionTreeClassifier(max_depth=10, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42),
    'KNN': KNeighborsClassifier(n_neighbors=5),
    'SVM': SVC(kernel='rbf', random_state=42),
    'MLP': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
}

# Train and evaluate models
results = []

print("\n=== Training Models ===")
print("Using encoded features...")

for name, model in models.items():
    print(f"\nTraining {name}...")
    
    # Train
    model.fit(X_train_encoded, y_train)
    
    # Predictions
    train_pred = model.predict(X_train_encoded)
    val_pred = model.predict(X_val_encoded)
    test_pred = model.predict(X_test_encoded)
    
    # Accuracies
    train_acc = accuracy_score(y_train, train_pred)
    val_acc = accuracy_score(y_val, val_pred)
    test_acc = accuracy_score(y_test, test_pred)
    
    print(f"  Train Acc: {train_acc:.4f}")
    print(f"  Val Acc: {val_acc:.4f}")
    print(f"  Test Acc: {test_acc:.4f}")
    
    results.append({
        'Model': name,
        'Features': 'Encoded',
        'Train Acc': train_acc,
        'Val Acc': val_acc,
        'Test Acc': test_acc
    })

# Try with engineered features
print("\n=== Training with Engineered Features ===")

models_fe = {
    'Logistic Regression (FE)': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest (FE)': RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42),
    'Gradient Boosting (FE)': GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42),
    'MLP (FE)': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
}

for name, model in models_fe.items():
    print(f"\nTraining {name}...")
    
    # Train
    model.fit(X_train_fe, y_train)
    
    # Predictions
    train_pred = model.predict(X_train_fe)
    val_pred = model.predict(X_val_fe)
    test_pred = model.predict(X_test_fe)
    
    # Accuracies
    train_acc = accuracy_score(y_train, train_pred)
    val_acc = accuracy_score(y_val, val_pred)
    test_acc = accuracy_score(y_test, test_pred)
    
    print(f"  Train Acc: {train_acc:.4f}")
    print(f"  Val Acc: {val_acc:.4f}")
    print(f"  Test Acc: {test_acc:.4f}")
    
    results.append({
        'Model': name,
        'Features': 'Engineered',
        'Train Acc': train_acc,
        'Val Acc': val_acc,
        'Test Acc': test_acc
    })

# Create results dataframe
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('Test Acc', ascending=False)

print("\n=== Results Summary ===")
print(results_df.to_string(index=False))

# Save results
results_df.to_csv('../outputs/model_results.csv', index=False)

# Find best model
best_row = results_df.iloc[0]
print(f"\n=== Best Model ===")
print(f"Model: {best_row['Model']}")
print(f"Test Accuracy: {best_row['Test Acc']:.4f}")
print(f"SOTA Baseline: 0.7000")
print(f"Difference: {best_row['Test Acc'] - 0.7:.4f}")

# Create visualizations
print("\n=== Creating Visualizations ===")

# Figure 1: Model comparison bar chart
plt.figure(figsize=(12, 6))
colors = ['green' if acc >= 0.7 else 'red' for acc in results_df['Test Acc']]
bars = plt.bar(results_df['Model'], results_df['Test Acc'], color=colors, alpha=0.7)
plt.axhline(y=0.7, color='blue', linestyle='--', linewidth=2, label='SOTA Baseline (70%)')
plt.xlabel('Model')
plt.ylabel('Test Accuracy')
plt.title('Model Performance Comparison on SPR_BENCH')
plt.xticks(rotation=45, ha='right')
plt.ylim(0.4, 0.85)
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/model_comparison.png', dpi=150)
plt.close()
print("Saved model_comparison.png")

# Figure 2: Train/Val/Test accuracy comparison
fig, ax = plt.subplots(figsize=(14, 6))
x = np.arange(len(results_df))
width = 0.25

ax.bar(x - width, results_df['Train Acc'], width, label='Train', alpha=0.8)
ax.bar(x, results_df['Val Acc'], width, label='Validation', alpha=0.8)
ax.bar(x + width, results_df['Test Acc'], width, label='Test', alpha=0.8)
ax.axhline(y=0.7, color='red', linestyle='--', linewidth=2, label='SOTA (70%)')

ax.set_xlabel('Model')
ax.set_ylabel('Accuracy')
ax.set_title('Train/Validation/Test Accuracy by Model')
ax.set_xticks(x)
ax.set_xticklabels(results_df['Model'], rotation=45, ha='right')
ax.legend()
ax.set_ylim(0.4, 1.0)
plt.tight_layout()
plt.savefig('../report/images/train_val_test_comparison.png', dpi=150)
plt.close()
print("Saved train_val_test_comparison.png")

# Figure 3: Confusion matrix for best model
# Retrain best model to get confusion matrix
best_model_name = best_row['Model']
if '(FE)' in best_model_name:
    # Use engineered features
    if 'Random Forest' in best_model_name:
        best_model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42)
    elif 'Gradient Boosting' in best_model_name:
        best_model = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
    elif 'MLP' in best_model_name:
        best_model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
    else:
        best_model = LogisticRegression(max_iter=1000, random_state=42)
    best_model.fit(X_train_fe, y_train)
    test_pred = best_model.predict(X_test_fe)
else:
    # Use encoded features
    if 'Random Forest' in best_model_name:
        best_model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42)
    elif 'Gradient Boosting' in best_model_name:
        best_model = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
    elif 'Decision Tree' in best_model_name:
        best_model = DecisionTreeClassifier(max_depth=10, random_state=42)
    elif 'KNN' in best_model_name:
        best_model = KNeighborsClassifier(n_neighbors=5)
    elif 'SVM' in best_model_name:
        best_model = SVC(kernel='rbf', random_state=42)
    elif 'MLP' in best_model_name:
        best_model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
    else:
        best_model = LogisticRegression(max_iter=1000, random_state=42)
    best_model.fit(X_train_encoded, y_train)
    test_pred = best_model.predict(X_test_encoded)

cm = confusion_matrix(y_test, test_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True)
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title(f'Confusion Matrix - {best_model_name}')
plt.savefig('../report/images/confusion_matrix.png', dpi=150)
plt.close()
print("Saved confusion_matrix.png")

# Figure 4: Label distribution
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
for i, (name, df) in enumerate([('Train', train), ('Validation', val), ('Test', test)]):
    counts = df['label'].value_counts().sort_index()
    axes[i].bar(counts.index, counts.values, color=['coral', 'steelblue'])
    axes[i].set_xlabel('Label')
    axes[i].set_ylabel('Count')
    axes[i].set_title(f'{name} Set Label Distribution')
    axes[i].set_xticks([0, 1])
plt.tight_layout()
plt.savefig('../report/images/label_distribution.png', dpi=150)
plt.close()
print("Saved label_distribution.png")

# Figure 5: Performance vs SOTA
plt.figure(figsize=(10, 6))
model_names = results_df['Model'].tolist()
test_accs = results_df['Test Acc'].tolist()

# Sort by test accuracy
sorted_indices = np.argsort(test_accs)[::-1]
sorted_names = [model_names[i] for i in sorted_indices]
sorted_accs = [test_accs[i] for i in sorted_indices]

colors = ['forestgreen' if acc >= 0.7 else 'tomato' for acc in sorted_accs]
plt.barh(sorted_names, sorted_accs, color=colors, alpha=0.8)
plt.axvline(x=0.7, color='navy', linestyle='--', linewidth=2, label='SOTA (70%)')
plt.xlabel('Test Accuracy')
plt.title('Model Test Accuracy vs SOTA Baseline')
plt.xlim(0.4, 0.85)
plt.legend(loc='lower right')
plt.tight_layout()
plt.savefig('../report/images/performance_vs_sota.png', dpi=150)
plt.close()
print("Saved performance_vs_sota.png")

# Save detailed classification report for best model
clf_report = classification_report(y_test, test_pred, target_names=['Reject (0)', 'Accept (1)'])
with open('../outputs/classification_report.txt', 'w') as f:
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Test Accuracy: {best_row['Test Acc']:.4f}\n")
    f.write(f"\nClassification Report:\n")
    f.write(clf_report)
    f.write(f"\nConfusion Matrix:\n")
    f.write(str(cm))

print("\n=== Analysis Complete ===")
print(f"Results saved to ../outputs/model_results.csv")
print(f"Figures saved to ../report/images/")