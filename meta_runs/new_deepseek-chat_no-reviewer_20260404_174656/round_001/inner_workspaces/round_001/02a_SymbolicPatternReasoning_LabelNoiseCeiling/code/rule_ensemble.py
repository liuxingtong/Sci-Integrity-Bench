import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score
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

# Discover rules from training data
def discover_rules(X, y, min_samples=10, min_deviation=0.15):
    """Discover predictive rules from data"""
    rules = []
    
    # Check single position rules
    for pos in range(8):
        col = feature_cols[pos]
        unique_tokens = X[col].value_counts().head(20).index.tolist()  # Most common tokens
        
        for token in unique_tokens:
            mask = X[col] == token
            if mask.sum() >= min_samples:
                accuracy = y[mask].mean()
                if abs(accuracy - 0.5) >= min_deviation:
                    rules.append({
                        'type': 'single',
                        'col': col,
                        'token': token,
                        'accuracy': accuracy,
                        'coverage': mask.mean()
                    })
    
    # Check two-position rules
    from itertools import combinations
    
    for pos1, pos2 in combinations(range(8), 2):
        col1 = feature_cols[pos1]
        col2 = feature_cols[pos2]
        
        # Get common token combinations
        token_pairs = pd.crosstab(X[col1], X[col2]).stack()
        common_pairs = token_pairs[token_pairs >= min_samples].index.tolist()[:50]  # Limit to top 50
        
        for token1, token2 in common_pairs:
            mask = (X[col1] == token1) & (X[col2] == token2)
            if mask.sum() >= min_samples:
                accuracy = y[mask].mean()
                if abs(accuracy - 0.5) >= min_deviation:
                    rules.append({
                        'type': 'conjunction',
                        'col1': col1,
                        'token1': token1,
                        'col2': col2,
                        'token2': token2,
                        'accuracy': accuracy,
                        'coverage': mask.mean()
                    })
    
    return rules

print("\nDiscovering rules from training data...")
rules = discover_rules(X_train_raw, y_train, min_samples=5, min_deviation=0.2)
print(f"Discovered {len(rules)} predictive rules")

# Sort rules by predictive power
rules.sort(key=lambda x: abs(x['accuracy'] - 0.5), reverse=True)

print("\nTop 10 rules:")
for i, rule in enumerate(rules[:10]):
    if rule['type'] == 'single':
        print(f"  {i+1}. {rule['col']} = {rule['token']}: acc={rule['accuracy']:.3f}, cov={rule['coverage']:.3f}")
    else:
        print(f"  {i+1}. {rule['col1']} = {rule['token1']} AND {rule['col2']} = {rule['token2']}: acc={rule['accuracy']:.3f}, cov={rule['coverage']:.3f}")

# Create features from rules
def create_rule_features(X, rules, top_n=100):
    """Create binary features based on rules"""
    features = []
    
    # Use top N rules
    top_rules = rules[:top_n]
    
    for rule in top_rules:
        if rule['type'] == 'single':
            col = rule['col']
            token = rule['token']
            rule_feature = (X[col] == token).astype(int)
            
            # If rule accuracy < 0.5, invert the feature
            if rule['accuracy'] < 0.5:
                rule_feature = 1 - rule_feature
            
            features.append(rule_feature.values)
        else:
            col1 = rule['col1']
            token1 = rule['token1']
            col2 = rule['col2']
            token2 = rule['token2']
            
            rule_feature = ((X[col1] == token1) & (X[col2] == token2)).astype(int)
            
            # If rule accuracy < 0.5, invert the feature
            if rule['accuracy'] < 0.5:
                rule_feature = 1 - rule_feature
            
            features.append(rule_feature.values)
    
    # Stack features
    if features:
        return np.column_stack(features)
    else:
        return np.zeros((len(X), 1))

print(f"\nCreating rule-based features...")
X_train_rules = create_rule_features(X_train_raw, rules, top_n=200)
X_val_rules = create_rule_features(X_val_raw, rules, top_n=200)
X_test_rules = create_rule_features(X_test_raw, rules, top_n=200)

print(f"Rule feature shape: {X_train_rules.shape}")

# Also include basic features
def create_basic_features(X):
    """Create basic shape and color count features"""
    basic_features = []
    
    for idx, row in X.iterrows():
        feat = []
        
        # Shape and color counts
        shape_counts = {'T': 0, 'S': 0, 'C': 0, 'D': 0}
        color_counts = {'r': 0, 'g': 0, 'b': 0, 'y': 0}
        
        for col in feature_cols:
            token = row[col]
            shape_counts[token[0]] += 1
            color_counts[token[1]] += 1
        
        feat.extend([shape_counts['T'], shape_counts['S'], shape_counts['C'], shape_counts['D']])
        feat.extend([color_counts['r'], color_counts['g'], color_counts['b'], color_counts['y']])
        
        basic_features.append(feat)
    
    return np.array(basic_features)

print("Creating basic features...")
X_train_basic = create_basic_features(X_train_raw)
X_val_basic = create_basic_features(X_val_raw)
X_test_basic = create_basic_features(X_test_raw)

print(f"Basic feature shape: {X_train_basic.shape}")

# Combine rule features and basic features
X_train_combined = np.hstack([X_train_basic, X_train_rules])
X_val_combined = np.hstack([X_val_basic, X_val_rules])
X_test_combined = np.hstack([X_test_basic, X_test_rules])

print(f"Combined feature shape: {X_train_combined.shape}")

# Train classifiers
print("\nTraining classifiers on rule-based features...")

models = {
    'Random Forest': RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_split=5, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, max_depth=5, learning_rate=0.1, random_state=42),
}

results = []

for name, model in models.items():
    print(f"\nTraining {name}...")
    
    model.fit(X_train_combined, y_train)
    
    # Predict
    y_train_pred = model.predict(X_train_combined)
    y_val_pred = model.predict(X_val_combined)
    y_test_pred = model.predict(X_test_combined)
    
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
print("RESULTS")
print("="*60)
print(results_df.to_string(index=False))

# Compare with SOTA
sota_baseline = 0.70
print(f"\nSOTA baseline: {sota_baseline:.4f}")
print("\nModels exceeding SOTA baseline:")

best_test_acc = 0
best_model = ""

for _, row in results_df.iterrows():
    if row['Test Acc'] > best_test_acc:
        best_test_acc = row['Test Acc']
        best_model = row['Model']
    
    if row['Test Acc'] > sota_baseline:
        print(f"  {row['Model']}: {row['Test Acc']:.4f} (exceeds by {row['Test Acc'] - sota_baseline:.4f})")

if not any(results_df['Test Acc'] > sota_baseline):
    print(f"  None of the models exceed the SOTA baseline.")
    print(f"  Best model: {best_model} with test accuracy {best_test_acc:.4f}")
    print(f"  Gap to SOTA: {sota_baseline - best_test_acc:.4f}")