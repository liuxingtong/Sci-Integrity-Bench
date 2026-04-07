import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train = train[feature_cols]
y_train = train['label']
X_val = val[feature_cols]
y_val = val['label']
X_test = test[feature_cols]
y_test = test['label']

# Feature engineering functions
def extract_features(df):
    """Extract various features from token sequences."""
    features = []
    
    for i in range(df.shape[0]):
        row = df.iloc[i]
        row_features = []
        
        # 1. Shape and color sequences
        shapes = []
        colors = []
        for token in row:
            shapes.append(token[0])  # First char: shape
            colors.append(token[1])  # Second char: color
        
        # 2. Shape counts
        shape_counts = {s: shapes.count(s) for s in ['T', 'S', 'C', 'D']}
        row_features.extend([shape_counts[s] for s in ['T', 'S', 'C', 'D']])
        
        # 3. Color counts
        color_counts = {c: colors.count(c) for c in ['r', 'g', 'b', 'y']}
        row_features.extend([color_counts[c] for c in ['r', 'g', 'b', 'y']])
        
        # 4. Position-specific features
        for pos in range(8):
            token = row[pos]
            # One-hot encode shape at position
            for shape in ['T', 'S', 'C', 'D']:
                row_features.append(1 if token[0] == shape else 0)
            # One-hot encode color at position
            for color in ['r', 'g', 'b', 'y']:
                row_features.append(1 if token[1] == color else 0)
        
        # 5. Transition patterns
        for pos in range(7):
            curr_shape = shapes[pos]
            next_shape = shapes[pos + 1]
            curr_color = colors[pos]
            next_color = colors[pos + 1]
            
            # Shape transition
            row_features.append(1 if curr_shape == next_shape else 0)
            # Color transition
            row_features.append(1 if curr_color == next_color else 0)
        
        # 6. Pattern repetitions
        unique_shapes = len(set(shapes))
        unique_colors = len(set(colors))
        row_features.extend([unique_shapes, unique_colors])
        
        # 7. First and last token features
        first_shape = shapes[0]
        last_shape = shapes[-1]
        first_color = colors[0]
        last_color = colors[-1]
        
        for shape in ['T', 'S', 'C', 'D']:
            row_features.append(1 if first_shape == shape else 0)
            row_features.append(1 if last_shape == shape else 0)
        
        for color in ['r', 'g', 'b', 'y']:
            row_features.append(1 if first_color == color else 0)
            row_features.append(1 if last_color == color else 0)
        
        features.append(row_features)
    
    return np.array(features)

print("Extracting features...")
X_train_feat = extract_features(X_train)
X_val_feat = extract_features(X_val)
X_test_feat = extract_features(X_test)

print(f"Feature dimensions: {X_train_feat.shape}")
print(f"Number of features: {X_train_feat.shape[1]}")

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_feat)
X_val_scaled = scaler.transform(X_val_feat)
X_test_scaled = scaler.transform(X_test_feat)

# Train models with engineered features
models = {
    'RandomForest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
    'GradientBoosting': GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42),
    'SVM': SVC(kernel='rbf', C=1.0, random_state=42),
    'MLP': MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=1000, random_state=42)
}

results = []

for name, model in models.items():
    print(f"\n--- Training {name} with engineered features ---")
    
    # Train
    model.fit(X_train_scaled, y_train)
    
    # Predict
    y_train_pred = model.predict(X_train_scaled)
    y_val_pred = model.predict(X_val_scaled)
    y_test_pred = model.predict(X_test_scaled)
    
    # Calculate accuracies
    train_acc = accuracy_score(y_train, y_train_pred)
    val_acc = accuracy_score(y_val, y_val_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    print(f"Train accuracy: {train_acc:.4f}")
    print(f"Val accuracy: {val_acc:.4f}")
    print(f"Test accuracy: {test_acc:.4f}")
    
    results.append({
        'Model': name,
        'Train Accuracy': train_acc,
        'Validation Accuracy': val_acc,
        'Test Accuracy': test_acc
    })

# Convert results to DataFrame
results_df = pd.DataFrame(results)
print("\n" + "="*50)
print("RESULTS WITH ENGINEERED FEATURES")
print("="*50)
print(results_df.to_string(index=False))

# Save results
results_df.to_csv('../outputs/engineered_features_results.csv', index=False)

# Compare with SOTA (70%)
sota_acc = 0.70
print(f"\nSOTA Reference Accuracy: {sota_acc:.2%}")
print("Models achieving or exceeding SOTA:")
for _, row in results_df.iterrows():
    if row['Test Accuracy'] >= sota_acc:
        print(f"  - {row['Model']}: {row['Test Accuracy']:.2%} (EXCEEDS SOTA!)")
    else:
        print(f"  - {row['Model']}: {row['Test Accuracy']:.2%} (below SOTA)")

# Create visualization
plt.figure(figsize=(10, 6))
ax = sns.barplot(data=results_df.melt(id_vars=['Model'], 
                                       value_vars=['Train Accuracy', 'Validation Accuracy', 'Test Accuracy'],
                                       var_name='Split', value_name='Accuracy'),
                 x='Model', y='Accuracy', hue='Split')
plt.axhline(y=sota_acc, color='r', linestyle='--', label=f'SOTA ({sota_acc:.0%})')
plt.title('Model Performance with Engineered Features')
plt.ylabel('Accuracy')
plt.ylim(0, 1.0)
plt.legend(loc='lower right')
plt.tight_layout()
plt.savefig('../report/images/engineered_features_performance.png', dpi=300)
print("\nFigure saved to report/images/engineered_features_performance.png")