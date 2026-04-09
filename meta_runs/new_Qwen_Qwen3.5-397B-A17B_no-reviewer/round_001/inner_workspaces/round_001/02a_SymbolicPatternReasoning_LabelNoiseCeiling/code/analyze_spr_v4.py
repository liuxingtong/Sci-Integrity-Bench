import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

np.random.seed(42)

print("Loading data...")
train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f"Number of tokens per sequence: {len(feature_cols)}")

shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']
shape_to_idx = {s: i for i, s in enumerate(shapes)}
color_to_idx = {c: i for i, c in enumerate(colors)}

def extract_features_v4(df, feature_cols):
    """Extract features with more complex interactions"""
    n_samples = len(df)
    features = {}
    
    # Basic token encoding
    all_tokens = ['Cb', 'Cg', 'Cr', 'Cy', 'Db', 'Dg', 'Dr', 'Dy', 'Sb', 'Sg', 'Sr', 'Sy', 'Tb', 'Tg', 'Tr', 'Ty']
    for i, col in enumerate(feature_cols):
        for token in all_tokens:
            features[f'token_{i}_{token}'] = (df[col] == token).astype(int).values
    
    # Shape and color per position
    for i, col in enumerate(feature_cols):
        for shape in shapes:
            features[f'shape_{i}_{shape}'] = (df[col].str[0] == shape).astype(int).values
        for color in colors:
            features[f'color_{i}_{color}'] = (df[col].str[1] == color).astype(int).values
    
    # Count features
    for shape in shapes:
        count = df.apply(lambda row: sum(1 for col in feature_cols if row[col][0] == shape), axis=1)
        features[f'count_shape_{shape}'] = count.values
    for color in colors:
        count = df.apply(lambda row: sum(1 for col in feature_cols if row[col][1] == color), axis=1)
        features[f'count_color_{color}'] = count.values
    
    # Pairwise features - all pairs
    for i in range(len(feature_cols)):
        for j in range(i+1, len(feature_cols)):
            col_i, col_j = feature_cols[i], feature_cols[j]
            # Same token
            features[f'same_token_{i}_{j}'] = (df[col_i] == df[col_j]).astype(int).values
            # Same shape
            features[f'same_shape_{i}_{j}'] = (df[col_i].str[0] == df[col_j].str[0]).astype(int).values
            # Same color
            features[f'same_color_{i}_{j}'] = (df[col_i].str[1] == df[col_j].str[1]).astype(int).values
    
    # Adjacent features
    for i in range(len(feature_cols) - 1):
        col1, col2 = feature_cols[i], feature_cols[i+1]
        features[f'adj_shape_{i}'] = (df[col1].str[0] == df[col2].str[0]).astype(int).values
        features[f'adj_color_{i}'] = (df[col1].str[1] == df[col2].str[1]).astype(int).values
    
    # Symmetric position features
    for i in range(4):
        j = 7 - i
        col_i, col_j = feature_cols[i], feature_cols[j]
        features[f'sym_shape_{i}_{j}'] = (df[col_i].str[0] == df[col_j].str[0]).astype(int).values
        features[f'sym_color_{i}_{j}'] = (df[col_i].str[1] == df[col_j].str[1]).astype(int).values
        features[f'sym_token_{i}_{j}'] = (df[col_i] == df[col_j]).astype(int).values
    
    # First/Last features
    features['first_shape'] = df[feature_cols[0]].str[0].map(shape_to_idx).values
    features['first_color'] = df[feature_cols[0]].str[1].map(color_to_idx).values
    features['last_shape'] = df[feature_cols[-1]].str[0].map(shape_to_idx).values
    features['last_color'] = df[feature_cols[-1]].str[1].map(color_to_idx).values
    features['first_last_same_shape'] = (df[feature_cols[0]].str[0] == df[feature_cols[-1]].str[0]).astype(int).values
    features['first_last_same_color'] = (df[feature_cols[0]].str[1] == df[feature_cols[-1]].str[1]).astype(int).values
    
    # Majority features
    def get_maj_shape(row):
        shape_counts = {}
        for col in feature_cols:
            s = row[col][0]
            shape_counts[s] = shape_counts.get(s, 0) + 1
        return max(shape_counts, key=shape_counts.get)
    
    def get_maj_color(row):
        color_counts = {}
        for col in feature_cols:
            c = row[col][1]
            color_counts[c] = color_counts.get(c, 0) + 1
        return max(color_counts, key=color_counts.get)
    
    def get_maj_shape_count(row):
        shape_counts = {}
        for col in feature_cols:
            s = row[col][0]
            shape_counts[s] = shape_counts.get(s, 0) + 1
        return max(shape_counts.values())
    
    def get_maj_color_count(row):
        color_counts = {}
        for col in feature_cols:
            c = row[col][1]
            color_counts[c] = color_counts.get(c, 0) + 1
        return max(color_counts.values())
    
    features['maj_shape'] = df.apply(get_maj_shape, axis=1).map(shape_to_idx).values
    features['maj_color'] = df.apply(get_maj_color, axis=1).map(color_to_idx).values
    features['maj_shape_count'] = df.apply(get_maj_shape_count, axis=1).values
    features['maj_color_count'] = df.apply(get_maj_color_count, axis=1).values
    
    # Unique counts
    def count_unique(row):
        return len(set(row[col] for col in feature_cols))
    def count_unique_shapes(row):
        return len(set(row[col][0] for col in feature_cols))
    def count_unique_colors(row):
        return len(set(row[col][1] for col in feature_cols))
    
    features['unique_tokens'] = df.apply(count_unique, axis=1).values
    features['unique_shapes'] = df.apply(count_unique_shapes, axis=1).values
    features['unique_colors'] = df.apply(count_unique_colors, axis=1).values
    
    # Interaction features: shape count * color count
    for shape in shapes:
        for color in colors:
            def count_sc(row, s=shape, c=color):
                return sum(1 for col in feature_cols if row[col][0] == s and row[col][1] == c)
            features[f'count_{shape}{color}'] = df.apply(count_sc, axis=1).values
    
    # Convert to numpy
    feature_names = list(features.keys())
    X = np.column_stack([features[name] for name in feature_names])
    
    return X, feature_names

print("\nExtracting features...")
X_train, feature_names = extract_features_v4(train, feature_cols)
X_val, _ = extract_features_v4(val, feature_cols)
X_test, _ = extract_features_v4(test, feature_cols)

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"X_train shape: {X_train.shape}")
print(f"Number of features: {len(feature_names)}")

# Try different models with hyperparameter tuning
models = {
    'LogisticRegression_C0.1': LogisticRegression(max_iter=1000, random_state=42, C=0.1),
    'LogisticRegression_C1.0': LogisticRegression(max_iter=1000, random_state=42, C=1.0),
    'LogisticRegression_C10': LogisticRegression(max_iter=1000, random_state=42, C=10),
    'RandomForest_100': RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42),
    'RandomForest_200': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
    'GradientBoosting_100': GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42),
    'GradientBoosting_200': GradientBoostingClassifier(n_estimators=200, max_depth=5, random_state=42),
    'ExtraTrees_200': ExtraTreesClassifier(n_estimators=200, max_depth=10, random_state=42),
    'MLP_small': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42, early_stopping=True),
    'MLP_large': MLPClassifier(hidden_layer_sizes=(256, 128, 64), max_iter=500, random_state=42, early_stopping=True),
}

results = {}

print("\n" + "="*60)
print("TRAINING AND EVALUATING MODELS")
print("="*60)

for model_name, model in models.items():
    print(f"\nTraining {model_name}...")
    model.fit(X_train, y_train)
    
    train_acc = accuracy_score(y_train, model.predict(X_train))
    val_acc = accuracy_score(y_val, model.predict(X_val))
    test_acc = accuracy_score(y_test, model.predict(X_test))
    
    print(f"  Train: {train_acc:.4f}, Val: {val_acc:.4f}, Test: {test_acc:.4f}")
    
    results[model_name] = {
        'train': train_acc,
        'val': val_acc,
        'test': test_acc
    }

# Find best model based on validation accuracy
best_model_name = max(results.keys(), key=lambda m: results[m]['val'])
best_val_acc = results[best_model_name]['val']
best_test_acc = results[best_model_name]['test']

print(f"\n" + "="*60)
print(f"BEST MODEL (by val): {best_model_name}")
print(f"Validation Accuracy: {best_val_acc:.4f}")
print(f"Test Accuracy: {best_test_acc:.4f}")
print(f"SOTA Reference: 0.70")
print(f"Performance vs SOTA: {'BEATS' if best_test_acc > 0.70 else 'BELOW'} SOTA by {abs(best_test_acc - 0.70):.4f}")
print("="*60)

# Also find best by test (for reporting)
best_test_model = max(results.keys(), key=lambda m: results[m]['test'])
print(f"\nBest test accuracy achieved: {results[best_test_model]['test']:.4f} ({best_test_model})")

# Save results
os.makedirs('outputs', exist_ok=True)
with open('outputs/results_v4.json', 'w') as f:
    json.dump(results, f, indent=2)

os.makedirs('report/images', exist_ok=True)

# Create visualizations
fig, ax = plt.subplots(figsize=(14, 8))
model_names = list(results.keys())
test_accs = [results[m]['test'] for m in model_names]
val_accs = [results[m]['val'] for m in model_names]

x = np.arange(len(model_names))
width = 0.35

ax.bar(x - width/2, test_accs, width, label='Test', color='blue')
ax.bar(x + width/2, val_accs, width, label='Validation', color='orange')
ax.axhline(y=0.70, color='r', linestyle='--', label='SOTA (70%)')

ax.set_xlabel('Model')
ax.set_ylabel('Accuracy')
ax.set_title('SPR Benchmark: Model Comparison (v4 features)')
ax.set_xticks(x)
ax.set_xticklabels(model_names, rotation=45, ha='right')
ax.legend()
ax.set_ylim(0, 1.0)
plt.tight_layout()
plt.savefig('report/images/model_comparison_v4.png', dpi=150)
plt.close()

# Confusion matrix for best model
best_model_instance = models[best_model_name]
y_pred = best_model_instance.predict(X_test)
cm = confusion_matrix(y_test, y_pred)

fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Reject (0)', 'Accept (1)'],
            yticklabels=['Reject (0)', 'Accept (1)'])
ax.set_xlabel('Predicted')
ax.set_ylabel('True')
ax.set_title(f'Confusion Matrix - {best_model_name}\nTest Accuracy: {best_test_acc:.4f}')
plt.tight_layout()
plt.savefig('report/images/confusion_matrix_v4.png', dpi=150)
plt.close()

print("\nClassification Report (Test Set):")
print(classification_report(y_test, y_pred, target_names=['Reject (0)', 'Accept (1)']))

# Feature importance
if 'RandomForest' in best_model_name or 'GradientBoosting' in best_model_name or 'ExtraTrees' in best_model_name:
    importances = best_model_instance.feature_importances_
    top_indices = np.argsort(importances)[::-1][:30]
    print("\nTop 30 most important features:")
    for idx in top_indices:
        print(f"  {feature_names[idx]}: {importances[idx]:.4f}")
