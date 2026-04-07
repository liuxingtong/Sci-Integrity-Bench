import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier
import warnings
warnings.filterwarnings('ignore')

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

print("Final attempt with advanced gradient boosting models\n")
print("="*60)

# Create more sophisticated features
def create_interaction_features(df):
    """Create interaction features between positions."""
    features = []
    
    for i in range(df.shape[0]):
        row = df.iloc[i]
        row_features = []
        
        # Original tokens
        for pos in range(8):
            token = row[pos]
            # Encode as integer (0-15)
            shape_idx = {'T': 0, 'S': 1, 'C': 2, 'D': 3}[token[0]]
            color_idx = {'r': 0, 'g': 1, 'b': 2, 'y': 3}[token[1]]
            token_idx = shape_idx * 4 + color_idx
            row_features.append(token_idx)
        
        # Interactions between adjacent positions
        for pos in range(7):
            token1 = row[pos]
            token2 = row[pos + 1]
            shape1_idx = {'T': 0, 'S': 1, 'C': 2, 'D': 3}[token1[0]]
            color1_idx = {'r': 0, 'g': 1, 'b': 2, 'y': 3}[token1[1]]
            shape2_idx = {'T': 0, 'S': 1, 'C': 2, 'D': 3}[token2[0]]
            color2_idx = {'r': 0, 'g': 1, 'b': 2, 'y': 3}[token2[1]]
            
            # Shape interaction
            row_features.append(shape1_idx * 4 + shape2_idx)
            # Color interaction
            row_features.append(color1_idx * 4 + color2_idx)
        
        # First-last interaction
        first = row[0]
        last = row[7]
        shape_first = {'T': 0, 'S': 1, 'C': 2, 'D': 3}[first[0]]
        shape_last = {'T': 0, 'S': 1, 'C': 2, 'D': 3}[last[0]]
        row_features.append(shape_first * 4 + shape_last)
        
        features.append(row_features)
    
    return np.array(features)

print("Creating interaction features...")
X_train_feat = create_interaction_features(X_train)
X_val_feat = create_interaction_features(X_val)
X_test_feat = create_interaction_features(X_test)

print(f"Feature shape: {X_train_feat.shape}")

# Try XGBoost
print("\nTraining XGBoost...")
xgb_model = xgb.XGBClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    use_label_encoder=False,
    eval_metric='logloss'
)

xgb_model.fit(X_train_feat, y_train,
              eval_set=[(X_val_feat, y_val)],
              verbose=False)

y_train_pred = xgb_model.predict(X_train_feat)
y_val_pred = xgb_model.predict(X_val_feat)
y_test_pred = xgb_model.predict(X_test_feat)

train_acc = accuracy_score(y_train, y_train_pred)
val_acc = accuracy_score(y_val, y_val_pred)
test_acc = accuracy_score(y_test, y_test_pred)

print(f"XGBoost - Train: {train_acc:.4f}, Val: {val_acc:.4f}, Test: {test_acc:.4f}")

# Try LightGBM
print("\nTraining LightGBM...")
lgb_model = lgb.LGBMClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

lgb_model.fit(X_train_feat, y_train)

y_train_pred = lgb_model.predict(X_train_feat)
y_val_pred = lgb_model.predict(X_val_feat)
y_test_pred = lgb_model.predict(X_test_feat)

train_acc = accuracy_score(y_train, y_train_pred)
val_acc = accuracy_score(y_val, y_val_pred)
test_acc = accuracy_score(y_test, y_test_pred)

print(f"LightGBM - Train: {train_acc:.4f}, Val: {val_acc:.4f}, Test: {test_acc:.4f}")

# Try CatBoost
print("\nTraining CatBoost...")
cat_model = CatBoostClassifier(
    iterations=500,
    depth=6,
    learning_rate=0.1,
    random_seed=42,
    verbose=False
)

cat_model.fit(X_train_feat, y_train,
              eval_set=(X_val_feat, y_val),
              verbose=False)

y_train_pred = cat_model.predict(X_train_feat)
y_val_pred = cat_model.predict(X_val_feat)
y_test_pred = cat_model.predict(X_test_feat)

train_acc = accuracy_score(y_train, y_train_pred)
val_acc = accuracy_score(y_val, y_val_pred)
test_acc = accuracy_score(y_test, y_test_pred)

print(f"CatBoost - Train: {train_acc:.4f}, Val: {val_acc:.4f}, Test: {test_acc:.4f}")

# Try ensemble
print("\nCreating ensemble...")
from sklearn.ensemble import VotingClassifier

ensemble = VotingClassifier(
    estimators=[
        ('xgb', xgb_model),
        ('lgb', lgb_model),
        ('cat', cat_model)
    ],
    voting='soft'
)

ensemble.fit(X_train_feat, y_train)
y_train_pred = ensemble.predict(X_train_feat)
y_val_pred = ensemble.predict(X_val_feat)
y_test_pred = ensemble.predict(X_test_feat)

train_acc = accuracy_score(y_train, y_train_pred)
val_acc = accuracy_score(y_val, y_val_pred)
test_acc = accuracy_score(y_test, y_test_pred)

print(f"Ensemble - Train: {train_acc:.4f}, Val: {val_acc:.4f}, Test: {test_acc:.4f}")

# Compare with SOTA
sota_acc = 0.70
print("\n" + "="*60)
print("COMPARISON WITH SOTA (70%)")
print("="*60)
print(f"XGBoost Test Accuracy: {test_acc:.2%}")
print(f"Difference from SOTA: {test_acc - sota_acc:+.2%}")

if test_acc >= sota_acc:
    print("\nSUCCESS: Model achieves or exceeds SOTA!")
else:
    print(f"\nModel is {sota_acc - test_acc:.2%} below SOTA")

# Save results
results = pd.DataFrame({
    'Model': ['XGBoost', 'LightGBM', 'CatBoost', 'Ensemble'],
    'Train Accuracy': [
        accuracy_score(y_train, xgb_model.predict(X_train_feat)),
        accuracy_score(y_train, lgb_model.predict(X_train_feat)),
        accuracy_score(y_train, cat_model.predict(X_train_feat)),
        accuracy_score(y_train, ensemble.predict(X_train_feat))
    ],
    'Validation Accuracy': [
        accuracy_score(y_val, xgb_model.predict(X_val_feat)),
        accuracy_score(y_val, lgb_model.predict(X_val_feat)),
        accuracy_score(y_val, cat_model.predict(X_val_feat)),
        accuracy_score(y_val, ensemble.predict(X_val_feat))
    ],
    'Test Accuracy': [
        accuracy_score(y_test, xgb_model.predict(X_test_feat)),
        accuracy_score(y_test, lgb_model.predict(X_test_feat)),
        accuracy_score(y_test, cat_model.predict(X_test_feat)),
        accuracy_score(y_test, ensemble.predict(X_test_feat))
    ]
})

results.to_csv('../outputs/final_results.csv', index=False)
print("\nResults saved to outputs/final_results.csv")