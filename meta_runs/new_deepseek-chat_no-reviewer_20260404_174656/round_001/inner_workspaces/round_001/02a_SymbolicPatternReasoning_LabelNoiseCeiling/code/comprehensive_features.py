import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train_raw = train[feature_cols]
y_train = train['label']
X_val_raw = val[feature_cols]
y_val = val['label']
X_test_raw = test[feature_cols]
y_test = test['label']

print("Data loaded successfully")
print(f"Train: {X_train_raw.shape}, Validation: {X_val_raw.shape}, Test: {X_test_raw.shape}")

# Comprehensive feature engineering
def extract_comprehensive_features(df):
    """Extract comprehensive features from token sequences"""
    features_list = []
    
    for idx, row in df.iterrows():
        seq_features = []
        tokens = row.values
        
        # 1. Basic counts
        shape_counts = {'T': 0, 'S': 0, 'C': 0, 'D': 0}
        color_counts = {'r': 0, 'g': 0, 'b': 0, 'y': 0}
        
        for token in tokens:
            shape = token[0]
            color = token[1]
            shape_counts[shape] += 1
            color_counts[color] += 1
        
        # Add shape and color counts
        seq_features.extend([shape_counts['T'], shape_counts['S'], shape_counts['C'], shape_counts['D']])
        seq_features.extend([color_counts['r'], color_counts['g'], color_counts['b'], color_counts['y']])
        
        # 2. Position-specific features (one-hot encoded as indices)
        # Encode each position as integer (0-15)
        shape_map = {'T': 0, 'S': 1, 'C': 2, 'D': 3}
        color_map = {'r': 0, 'g': 1, 'b': 2, 'y': 3}
        
        for i, token in enumerate(tokens):
            shape = token[0]
            color = token[1]
            # Encode as combined index (0-15)
            token_idx = shape_map[shape] * 4 + color_map[color]
            seq_features.append(token_idx)
        
        # 3. Transition features
        shape_changes = 0
        color_changes = 0
        
        for i in range(len(tokens)-1):
            if tokens[i][0] != tokens[i+1][0]:
                shape_changes += 1
            if tokens[i][1] != tokens[i+1][1]:
                color_changes += 1
        
        seq_features.extend([shape_changes, color_changes])
        
        # 4. Pattern features
        # Check for repetitions
        unique_tokens = len(set(tokens))
        seq_features.append(unique_tokens)
        
        # Check if first and last token are same shape/color
        seq_features.append(1 if tokens[0][0] == tokens[-1][0] else 0)
        seq_features.append(1 if tokens[0][1] == tokens[-1][1] else 0)
        
        # 5. Sequence patterns
        # Count of each shape at even vs odd positions
        even_shape_counts = {'T': 0, 'S': 0, 'C': 0, 'D': 0}
        odd_shape_counts = {'T': 0, 'S': 0, 'C': 0, 'D': 0}
        
        for i, token in enumerate(tokens):
            shape = token[0]
            if i % 2 == 0:
                even_shape_counts[shape] += 1
            else:
                odd_shape_counts[shape] += 1
        
        seq_features.extend([even_shape_counts['T'], even_shape_counts['S'], even_shape_counts['C'], even_shape_counts['D']])
        seq_features.extend([odd_shape_counts['T'], odd_shape_counts['S'], odd_shape_counts['C'], odd_shape_counts['D']])
        
        # 6. Dominant shape and color
        max_shape = max(shape_counts, key=shape_counts.get)
        max_color = max(color_counts, key=color_counts.get)
        seq_features.append(shape_map[max_shape])
        seq_features.append(color_map[max_color])
        
        features_list.append(seq_features)
    
    return np.array(features_list)

print("\nExtracting comprehensive features...")
X_train = extract_comprehensive_features(X_train_raw)
X_val = extract_comprehensive_features(X_val_raw)
X_test = extract_comprehensive_features(X_test_raw)

print(f"Feature shape: {X_train.shape}")
print(f"Number of features: {X_train.shape[1]}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Try multiple models
models = {
    'Logistic Regression (L2)': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
    'Random Forest (regularized)': RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_split=10, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42),
    'XGBoost (regularized)': xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, subsample=0.7, colsample_bytree=0.7, random_state=42, n_jobs=-1),
    'MLP Neural Network': MLPClassifier(hidden_layer_sizes=(64, 32), activation='relu', alpha=0.01, max_iter=500, random_state=42)
}

results = []

for name, model in models.items():
    print(f"\nTraining {name}...")
    
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
    
    results.append({
        'Model': name,
        'Train Acc': train_acc,
        'Val Acc': val_acc,
        'Test Acc': test_acc
    })
    
    print(f"  Training accuracy: {train_acc:.4f}")
    print(f"  Validation accuracy: {val_acc:.4f}")
    print(f"  Test accuracy: {test_acc:.4f}")

# Create results dataframe
results_df = pd.DataFrame(results)
print("\n" + "="*60)
print("SUMMARY OF RESULTS")
print("="*60)
print(results_df.to_string(index=False))

# Compare with SOTA
sota_baseline = 0.70
print(f"\nSOTA baseline: {sota_baseline:.4f}")
print("\nModels exceeding SOTA baseline:")
for _, row in results_df.iterrows():
    if row['Test Acc'] > sota_baseline:
        print(f"  {row['Model']}: {row['Test Acc']:.4f} (exceeds by {row['Test Acc'] - sota_baseline:.4f})")

if not any(results_df['Test Acc'] > sota_baseline):
    print("  None of the models exceed the SOTA baseline.")
    print(f"  Best model: {results_df.loc[results_df['Test Acc'].idxmax(), 'Model']} with test accuracy {results_df['Test Acc'].max():.4f}")