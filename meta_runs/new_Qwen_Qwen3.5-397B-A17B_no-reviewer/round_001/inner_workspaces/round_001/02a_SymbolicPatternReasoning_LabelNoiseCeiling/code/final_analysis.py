import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
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
print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']
all_tokens = ['Cb', 'Cg', 'Cr', 'Cy', 'Db', 'Dg', 'Dr', 'Dy', 'Sb', 'Sg', 'Sr', 'Sy', 'Tb', 'Tg', 'Tr', 'Ty']
shape_to_idx = {s: i for i, s in enumerate(shapes)}
color_to_idx = {c: i for i, c in enumerate(colors)}
token_to_idx = {t: i for i, t in enumerate(all_tokens)}

def extract_features(df, feature_cols):
    """Extract comprehensive features"""
    n_samples = len(df)
    features = {}
    
    # Token one-hot per position
    for i, col in enumerate(feature_cols):
        for token in all_tokens:
            features[f'token_{i}_{token}'] = (df[col] == token).astype(int).values
    
    # Shape/color per position
    for i, col in enumerate(feature_cols):
        for shape in shapes:
            features[f'shape_{i}_{shape}'] = (df[col].str[0] == shape).astype(int).values
        for color in colors:
            features[f'color_{i}_{color}'] = (df[col].str[1] == color).astype(int).values
    
    # Count features
    for shape in shapes:
        features[f'count_shape_{shape}'] = df.apply(lambda row: sum(1 for col in feature_cols if row[col][0] == shape), axis=1).values
    for color in colors:
        features[f'count_color_{color}'] = df.apply(lambda row: sum(1 for col in feature_cols if row[col][1] == color), axis=1).values
    
    # Pairwise same features
    for i in range(len(feature_cols)):
        for j in range(i+1, len(feature_cols)):
            features[f'same_shape_{i}_{j}'] = (df[feature_cols[i]].str[0] == df[feature_cols[j]].str[0]).astype(int).values
            features[f'same_color_{i}_{j}'] = (df[feature_cols[i]].str[1] == df[feature_cols[j]].str[1]).astype(int).values
    
    # Adjacent features
    for i in range(len(feature_cols) - 1):
        features[f'adj_shape_{i}'] = (df[feature_cols[i]].str[0] == df[feature_cols[i+1]].str[0]).astype(int).values
        features[f'adj_color_{i}'] = (df[feature_cols[i]].str[1] == df[feature_cols[i+1]].str[1]).astype(int).values
    
    # Symmetric features
    for i in range(4):
        j = 7 - i
        features[f'sym_shape_{i}_{j}'] = (df[feature_cols[i]].str[0] == df[feature_cols[j]].str[0]).astype(int).values
        features[f'sym_color_{i}_{j}'] = (df[feature_cols[i]].str[1] == df[feature_cols[j]].str[1]).astype(int).values
    
    # First/Last features
    features['first_last_same_shape'] = (df[feature_cols[0]].str[0] == df[feature_cols[-1]].str[0]).astype(int).values
    features['first_last_same_color'] = (df[feature_cols[0]].str[1] == df[feature_cols[-1]].str[1]).astype(int).values
    
    # Majority features
    def get_maj_shape_count(row, s):
        return sum(1 for col in feature_cols if row[col][0] == s)
    def get_maj_color_count(row, c):
        return sum(1 for col in feature_cols if row[col][1] == c)
    
    for shape in shapes:
        features[f'maj_{shape}_count'] = df.apply(lambda row, s=shape: get_maj_shape_count(row, s), axis=1).values
    for color in colors:
        features[f'maj_{color}_count'] = df.apply(lambda row, c=color: get_maj_color_count(row, c), axis=1).values
    
    # Unique counts
    features['unique_tokens'] = df.apply(lambda row: len(set(row[col] for col in feature_cols)), axis=1).values
    features['unique_shapes'] = df.apply(lambda row: len(set(row[col][0] for col in feature_cols)), axis=1).values
    features['unique_colors'] = df.apply(lambda row: len(set(row[col][1] for col in feature_cols)), axis=1).values
    
    feature_names = list(features.keys())
    X = np.column_stack([features[name] for name in feature_names])
    return X, feature_names

print("\nExtracting features...")
X_train, feature_names = extract_features(train, feature_cols)
X_val, _ = extract_features(val, feature_cols)
X_test, _ = extract_features(test, feature_cols)

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"Feature dimension: {X_train.shape[1]}")

# Models to evaluate
models = {
    'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42, C=0.1),
    'RandomForest': RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42),
    'GradientBoosting': GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42),
    'ExtraTrees': ExtraTreesClassifier(n_estimators=100, max_depth=5, random_state=42),
    'MLP': MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42, early_stopping=True),
}

results = {}
best_val_model = None
best_val_acc = 0

print("\n" + "="*60)
print("MODEL EVALUATION")
print("="*60)

for name, model in models.items():
    model.fit(X_train, y_train)
    train_acc = accuracy_score(y_train, model.predict(X_train))
    val_acc = accuracy_score(y_val, model.predict(X_val))
    test_acc = accuracy_score(y_test, model.predict(X_test))
    
    results[name] = {'train': train_acc, 'val': val_acc, 'test': test_acc}
    print(f"{name}: Train={train_acc:.4f}, Val={val_acc:.4f}, Test={test_acc:.4f}")
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_val_model = name

# Best model by validation
best_model = models[best_val_model]
best_test_acc = results[best_val_model]['test']

print(f"\nBest model (by val): {best_val_model}")
print(f"Test accuracy: {best_test_acc:.4f}")
print(f"SOTA reference: 0.70")

# Get predictions for best model
y_pred = best_model.predict(X_test)
precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')

# Save results
os.makedirs('outputs', exist_ok=True)
with open('outputs/final_results.json', 'w') as f:
    json.dump({
        'results': results,
        'best_model': best_val_model,
        'best_test_acc': best_test_acc,
        'sota': 0.70,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }, f, indent=2)

# Create figures
os.makedirs('report/images', exist_ok=True)

# Figure 1: Model comparison
fig, ax = plt.subplots(figsize=(12, 6))
model_names = list(results.keys())
x = np.arange(len(model_names))
width = 0.25

train_accs = [results[m]['train'] for m in model_names]
val_accs = [results[m]['val'] for m in model_names]
test_accs = [results[m]['test'] for m in model_names]

ax.bar(x - width, train_accs, width, label='Train', color='green', alpha=0.8)
ax.bar(x, val_accs, width, label='Validation', color='orange', alpha=0.8)
ax.bar(x + width, test_accs, width, label='Test', color='blue', alpha=0.8)
ax.axhline(y=0.70, color='red', linestyle='--', linewidth=2, label='SOTA (70%)')

ax.set_xlabel('Model', fontsize=12)
ax.set_ylabel('Accuracy', fontsize=12)
ax.set_title('SPR Benchmark: Model Performance Comparison', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(model_names, rotation=15)
ax.legend()
ax.set_ylim(0, 1.0)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/model_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 2: Confusion matrix
cm = confusion_matrix(y_test, y_pred)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Reject (0)', 'Accept (1)'],
            yticklabels=['Reject (0)', 'Accept (1)'])
ax.set_xlabel('Predicted Label', fontsize=12)
ax.set_ylabel('True Label', fontsize=12)
ax.set_title(f'Confusion Matrix - {best_val_model}\nTest Accuracy: {best_test_acc:.4f}', fontsize=12)
plt.tight_layout()
plt.savefig('report/images/confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 3: Train/Val/Test comparison for all models
fig, ax = plt.subplots(figsize=(14, 6))
x = np.arange(len(model_names))
width = 0.25

ax.bar(x - width, train_accs, width, label='Train', color='green')
ax.bar(x, val_accs, width, label='Validation', color='orange')
ax.bar(x + width, test_accs, width, label='Test', color='blue')
ax.axhline(y=0.70, color='red', linestyle='--', linewidth=2, label='SOTA (70%)')
ax.axhline(y=0.50, color='gray', linestyle=':', linewidth=1, label='Random (50%)')

ax.set_xlabel('Model', fontsize=12)
ax.set_ylabel('Accuracy', fontsize=12)
ax.set_title('SPR Benchmark: Complete Results Overview', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(model_names, rotation=15)
ax.legend()
ax.set_ylim(0, 1.0)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/complete_results.png', dpi=150, bbox_inches='tight')
plt.close()

print("\n" + "="*60)
print("CLASSIFICATION REPORT")
print("="*60)
print(classification_report(y_test, y_pred, target_names=['Reject (0)', 'Accept (1)']))

print("\nFigures saved to report/images/")
print("Results saved to outputs/final_results.json")
