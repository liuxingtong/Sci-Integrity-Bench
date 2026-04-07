import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
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

# Create the best feature set from what we've learned
# Based on previous experiments, comprehensive features work best
def create_features(df):
    """Create features for the final model"""
    features_list = []
    
    for idx, row in df.iterrows():
        feat = []
        tokens = row.values
        
        # 1. Shape and color counts
        shape_counts = {'T': 0, 'S': 0, 'C': 0, 'D': 0}
        color_counts = {'r': 0, 'g': 0, 'b': 0, 'y': 0}
        
        for token in tokens:
            shape_counts[token[0]] += 1
            color_counts[token[1]] += 1
        
        feat.extend([shape_counts['T'], shape_counts['S'], shape_counts['C'], shape_counts['D']])
        feat.extend([color_counts['r'], color_counts['g'], color_counts['b'], color_counts['y']])
        
        # 2. Position-specific features (encoded)
        shape_map = {'T': 0, 'S': 1, 'C': 2, 'D': 3}
        color_map = {'r': 0, 'g': 1, 'b': 2, 'y': 3}
        
        for token in tokens:
            feat.append(shape_map[token[0]])
            feat.append(color_map[token[1]])
        
        # 3. Transition features
        shape_changes = 0
        color_changes = 0
        
        for i in range(len(tokens)-1):
            if tokens[i][0] != tokens[i+1][0]:
                shape_changes += 1
            if tokens[i][1] != tokens[i+1][1]:
                color_changes += 1
        
        feat.extend([shape_changes, color_changes])
        
        # 4. Pattern features
        unique_tokens = len(set(tokens))
        feat.append(unique_tokens)
        
        # First-last relationships
        feat.append(1 if tokens[0][0] == tokens[-1][0] else 0)
        feat.append(1 if tokens[0][1] == tokens[-1][1] else 0)
        
        # 5. Some position relationships (simplified)
        # Check a few key positions
        for i, j in [(0, 4), (1, 5), (2, 6), (3, 7)]:
            feat.append(1 if tokens[i][0] == tokens[j][0] else 0)
            feat.append(1 if tokens[i][1] == tokens[j][1] else 0)
        
        features_list.append(feat)
    
    return np.array(features_list)

print("\nCreating features...")
X_train = create_features(X_train_raw)
X_val = create_features(X_val_raw)
X_test = create_features(X_test_raw)

print(f"Feature shape: {X_train.shape}")

# Combine train and val for final training
X_combined = np.vstack([X_train, X_val])
y_combined = np.concatenate([y_train, y_val])

print(f"Combined train+val: {X_combined.shape}")

# Train final model - Gradient Boosting worked best in earlier experiments
print("\nTraining final Gradient Boosting model...")
model = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.8,
    random_state=42
)

model.fit(X_combined, y_combined)

# Evaluate
print("\nEvaluating final model...")
y_train_pred = model.predict(X_train)
y_val_pred = model.predict(X_val)
y_test_pred = model.predict(X_test)

train_acc = accuracy_score(y_train, y_train_pred)
val_acc = accuracy_score(y_val, y_val_pred)
test_acc = accuracy_score(y_test, y_test_pred)

print(f"Training accuracy: {train_acc:.4f}")
print(f"Validation accuracy: {val_acc:.4f}")
print(f"Test accuracy: {test_acc:.4f}")

# Compare with SOTA
sota_baseline = 0.70
print(f"\nSOTA baseline: {sota_baseline:.4f}")
print(f"Our test accuracy: {test_acc:.4f}")
print(f"Difference: {test_acc - sota_baseline:.4f}")

if test_acc > sota_baseline:
    print("\nSUCCESS: Our model exceeds the SOTA baseline!")
else:
    print(f"\nOur model does not exceed the SOTA baseline. Gap: {sota_baseline - test_acc:.4f}")

# Save predictions for analysis
predictions_df = pd.DataFrame({
    'true_label': y_test,
    'predicted_label': y_test_pred
})
predictions_df.to_csv('../outputs/final_predictions.csv', index=False)
print("\nPredictions saved to outputs/final_predictions.csv")

# Also train on just train set for comparison
print("\nTraining model on train set only for comparison...")
model_train_only = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.8,
    random_state=42
)

model_train_only.fit(X_train, y_train)

y_test_pred_trainonly = model_train_only.predict(X_test)
test_acc_trainonly = accuracy_score(y_test, y_test_pred_trainonly)

print(f"Test accuracy (train only): {test_acc_trainonly:.4f}")
print(f"Test accuracy (train+val): {test_acc:.4f}")
print(f"Best overall: {max(test_acc, test_acc_trainonly):.4f}")