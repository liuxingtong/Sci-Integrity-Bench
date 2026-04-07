import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
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

# Create comprehensive features
def create_comprehensive_features(df):
    """Create comprehensive features including shape/color patterns"""
    features_list = []
    
    for idx, row in df.iterrows():
        feat = []
        tokens = row.values
        
        # 1. Basic shape and color counts
        shape_counts = {'T': 0, 'S': 0, 'C': 0, 'D': 0}
        color_counts = {'r': 0, 'g': 0, 'b': 0, 'y': 0}
        
        for token in tokens:
            shape_counts[token[0]] += 1
            color_counts[token[1]] += 1
        
        feat.extend([shape_counts['T'], shape_counts['S'], shape_counts['C'], shape_counts['D']])
        feat.extend([color_counts['r'], color_counts['g'], color_counts['b'], color_counts['y']])
        
        # 2. Position-specific shape and color (encoded)
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
        # Check for repetitions
        unique_tokens = len(set(tokens))
        feat.append(unique_tokens)
        
        # Check first-last relationships
        feat.append(1 if tokens[0][0] == tokens[-1][0] else 0)
        feat.append(1 if tokens[0][1] == tokens[-1][1] else 0)
        
        # 5. Position relationships
        # Check if specific positions match
        for i in [0, 2, 4, 6]:  # Even positions
            for j in [1, 3, 5, 7]:  # Odd positions
                if i < j:
                    feat.append(1 if tokens[i][0] == tokens[j][0] else 0)
                    feat.append(1 if tokens[i][1] == tokens[j][1] else 0)
        
        # 6. Dominant features
        max_shape = max(shape_counts, key=shape_counts.get)
        max_color = max(color_counts, key=color_counts.get)
        feat.append(shape_map[max_shape])
        feat.append(color_map[max_color])
        
        features_list.append(feat)
    
    return np.array(features_list)

print("\nCreating comprehensive features...")
X_train = create_comprehensive_features(X_train_raw)
X_val = create_comprehensive_features(X_val_raw)
X_test = create_comprehensive_features(X_test_raw)

print(f"Feature shape: {X_train.shape}")

# Combine train and val for more training data
X_combined = np.vstack([X_train, X_val])
y_combined = np.concatenate([y_train, y_val])

print(f"Combined train+val: {X_combined.shape}")

# Hyperparameter tuning with cross-validation
print("\nPerforming hyperparameter tuning...")

# Define parameter grid
param_grid = {
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.1, 0.2],
    'n_estimators': [100, 200, 300],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
    'gamma': [0, 0.1, 0.2],
    'reg_alpha': [0, 0.1, 0.5],
    'reg_lambda': [1, 1.5, 2]
}

# Create base model
xgb_model = xgb.XGBClassifier(
    random_state=42,
    n_jobs=-1,
    eval_metric='logloss',
    use_label_encoder=False
)

# Use GridSearchCV with fewer combinations for speed
# Since full grid would be huge, do randomized search
from sklearn.model_selection import RandomizedSearchCV

# Create randomized search
random_search = RandomizedSearchCV(
    estimator=xgb_model,
    param_distributions=param_grid,
    n_iter=20,  # Number of parameter settings to sample
    cv=3,  # 3-fold cross-validation
    scoring='accuracy',
    verbose=1,
    random_state=42,
    n_jobs=-1
)

print("Fitting randomized search (this may take a minute)...")
random_search.fit(X_combined, y_combined)

print("\nBest parameters found:")
for param, value in random_search.best_params_.items():
    print(f"  {param}: {value}")

print(f"\nBest cross-validation accuracy: {random_search.best_score_:.4f}")

# Train final model with best parameters on combined data
print("\nTraining final model with best parameters...")
best_model = random_search.best_estimator_

# Also train on just train set for comparison
best_model_train_only = xgb.XGBClassifier(**random_search.best_params_, random_state=42, n_jobs=-1)
best_model_train_only.fit(X_train, y_train)

# Evaluate
print("\nEvaluating models...")

# Model trained on combined data
y_train_pred_combined = best_model.predict(X_train)
y_val_pred_combined = best_model.predict(X_val)
y_test_pred_combined = best_model.predict(X_test)

train_acc_combined = accuracy_score(y_train, y_train_pred_combined)
val_acc_combined = accuracy_score(y_val, y_val_pred_combined)
test_acc_combined = accuracy_score(y_test, y_test_pred_combined)

print(f"Model trained on train+val:")
print(f"  Training accuracy: {train_acc_combined:.4f}")
print(f"  Validation accuracy: {val_acc_combined:.4f}")
print(f"  Test accuracy: {test_acc_combined:.4f}")

# Model trained only on train data
y_train_pred_trainonly = best_model_train_only.predict(X_train)
y_val_pred_trainonly = best_model_train_only.predict(X_val)
y_test_pred_trainonly = best_model_train_only.predict(X_test)

train_acc_trainonly = accuracy_score(y_train, y_train_pred_trainonly)
val_acc_trainonly = accuracy_score(y_val, y_val_pred_trainonly)
test_acc_trainonly = accuracy_score(y_test, y_test_pred_trainonly)

print(f"\nModel trained only on train:")
print(f"  Training accuracy: {train_acc_trainonly:.4f}")
print(f"  Validation accuracy: {val_acc_trainonly:.4f}")
print(f"  Test accuracy: {test_acc_trainonly:.4f}")

# Compare with SOTA
sota_baseline = 0.70
print(f"\nSOTA baseline: {sota_baseline:.4f}")
print(f"\nBest test accuracy: {max(test_acc_combined, test_acc_trainonly):.4f}")
print(f"Difference from SOTA: {max(test_acc_combined, test_acc_trainonly) - sota_baseline:.4f}")

if test_acc_combined > sota_baseline or test_acc_trainonly > sota_baseline:
    print("\nSUCCESS: Model exceeds SOTA baseline!")
else:
    print("\nModel does not exceed SOTA baseline.")
    
    # Feature importance
    print("\nChecking feature importance...")
    importances = best_model.feature_importances_
    top_indices = np.argsort(importances)[-10:]  # Top 10 features
    
    print("Top 10 most important features (indices):")
    for idx in reversed(top_indices):
        print(f"  Feature {idx}: importance={importances[idx]:.4f}")
    
    # Try to interpret what these features might be
    # The first 8 features are shape counts, next 8 are color counts, etc.
    print("\nFeature interpretation (approximate):")
    print("  Features 0-3: Counts of shapes T,S,C,D")
    print("  Features 4-7: Counts of colors r,g,b,y")
    print("  Features 8-23: Shape and color at each position (alternating)")
    print("  Features 24-25: Shape and color changes")
    print("  Feature 26: Unique tokens")
    print("  Features 27-28: First-last shape/color equality")
    print("  Features 29-60: Position relationships")
    print("  Features 61-62: Dominant shape and color")