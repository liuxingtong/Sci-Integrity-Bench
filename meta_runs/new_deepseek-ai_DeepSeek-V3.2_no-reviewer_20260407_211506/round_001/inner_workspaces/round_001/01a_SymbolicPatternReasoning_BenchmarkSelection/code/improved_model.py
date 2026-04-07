import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import OneHotEncoder
import warnings
warnings.filterwarnings('ignore')

# Set random seed
np.random.seed(42)

# Load registry
with open("../data/benchmark_registry.json") as f:
    registry = json.load(f)

# Selected benchmarks
selected_benchmarks = ['FDLOT', 'WVIOP', 'XPOFG', 'OQMEA']

# Function to engineer features
def engineer_features(df, all_possible_tokens=None):
    """Extract features from token sequence"""
    token_cols = [col for col in df.columns if col.startswith('token_')]
    
    # Create a copy to avoid modifying original
    df_feat = df.copy()
    
    # Extract shape and color for each position
    for col in token_cols:
        df_feat[f'{col}_shape'] = df[col].str[0]
        df_feat[f'{col}_color'] = df[col].str[1]
    
    # Get all unique shapes and colors
    all_shapes = ['C', 'S', 'T', 'D']
    all_colors = ['r', 'g', 'b', 'y']
    
    # Count shapes and colors in sequence
    shape_cols = [f'{col}_shape' for col in token_cols]
    color_cols = [f'{col}_color' for col in token_cols]
    
    for shape in all_shapes:
        df_feat[f'count_{shape}'] = (df_feat[shape_cols] == shape).sum(axis=1)
    for color in all_colors:
        df_feat[f'count_{color}'] = (df_feat[color_cols] == color).sum(axis=1)
    
    # Position-independent: token frequencies
    # Use all possible tokens if provided, otherwise infer from this df
    if all_possible_tokens is None:
        all_tokens = []
        for col in token_cols:
            all_tokens.extend(df[col].unique())
        all_possible_tokens = set(all_tokens)
    
    for token in all_possible_tokens:
        df_feat[f'count_{token}'] = 0
        for col in token_cols:
            df_feat[f'count_{token}'] += (df[col] == token).astype(int)
    
    # Drop intermediate columns
    cols_to_drop = []
    for col in token_cols:
        cols_to_drop.extend([f'{col}_shape', f'{col}_color'])
    df_feat = df_feat.drop(columns=cols_to_drop + token_cols)
    
    return df_feat, all_possible_tokens

# Results storage
results = []

for code in selected_benchmarks:
    print(f"\n{'='*60}")
    print(f"Training improved model for: {code}")
    
    # Load data
    train = pd.read_csv(f"../data/{code}_train.csv")
    val = pd.read_csv(f"../data/{code}_val.csv")
    test = pd.read_csv(f"../data/{code}_test.csv")
    
    # Engineer features - ensure consistent features across splits
    train_feat, all_tokens = engineer_features(train)
    val_feat, _ = engineer_features(val, all_possible_tokens=all_tokens)
    test_feat, _ = engineer_features(test, all_possible_tokens=all_tokens)
    
    # Separate features and target
    X_train = train_feat.drop('label', axis=1)
    y_train = train_feat['label']
    X_val = val_feat.drop('label', axis=1)
    y_val = val_feat['label']
    X_test = test_feat.drop('label', axis=1)
    y_test = test_feat['label']
    
    print(f"Original token positions: {len([c for c in train.columns if c.startswith('token_')])}")
    print(f"Engineered features: {X_train.shape[1]}")
    print(f"Unique tokens in training: {len(all_tokens)}")
    
    # Train Random Forest
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    rf.fit(X_train, y_train)
    
    # Predict
    y_val_pred = rf.predict(X_val)
    y_test_pred = rf.predict(X_test)
    
    val_acc = accuracy_score(y_val, y_val_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    sota_acc = registry[code]['sota_accuracy'] / 100
    diff = test_acc - sota_acc
    
    print(f"Validation accuracy: {val_acc:.4f}")
    print(f"Test accuracy: {test_acc:.4f}")
    print(f"SOTA accuracy: {sota_acc:.4f}")
    print(f"Difference (Our - SOTA): {diff:.4f}")
    
    results.append({
        'benchmark': code,
        'sota_accuracy': sota_acc * 100,
        'test_accuracy': test_acc * 100,
        'val_accuracy': val_acc * 100,
        'difference': diff * 100,
        'features': X_train.shape[1]
    })

# Print summary
print(f"\n{'='*60}")
print("Summary:")
for r in results:
    print(f"{r['benchmark']}: Test={r['test_accuracy']:.1f}%, SOTA={r['sota_accuracy']:.1f}%, Diff={r['difference']:.1f}%")

# Save results
results_df = pd.DataFrame(results)
results_df.to_csv("../outputs/results/improved_results.csv", index=False)