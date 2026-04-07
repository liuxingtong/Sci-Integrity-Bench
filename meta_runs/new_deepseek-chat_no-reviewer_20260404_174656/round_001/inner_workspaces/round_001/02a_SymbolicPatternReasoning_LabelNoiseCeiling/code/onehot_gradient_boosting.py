import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import OneHotEncoder
import xgboost as xgb
import lightgbm as lgb
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

# Method 1: One-hot encode each position separately
print("\n=== Method 1: One-hot encoding each position ===")

# Reshape data for one-hot encoding
# We have 8 positions, each with 16 possible tokens
# We'll one-hot encode each position separately
X_train_encoded_list = []
X_val_encoded_list = []
X_test_encoded_list = []

for i in range(len(feature_cols)):
    col = feature_cols[i]
    
    # One-hot encode this position
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    
    # Fit on train
    train_encoded = encoder.fit_transform(X_train_raw[[col]])
    val_encoded = encoder.transform(X_val_raw[[col]])
    test_encoded = encoder.transform(X_test_raw[[col]])
    
    X_train_encoded_list.append(train_encoded)
    X_val_encoded_list.append(val_encoded)
    X_test_encoded_list.append(test_encoded)
    
    print(f"Position {i}: {train_encoded.shape[1]} features")

# Concatenate all positions
X_train_oh = np.hstack(X_train_encoded_list)
X_val_oh = np.hstack(X_val_encoded_list)
X_test_oh = np.hstack(X_test_encoded_list)

print(f"\nTotal one-hot features: {X_train_oh.shape[1]}")

# Train XGBoost
print("\nTraining XGBoost on one-hot encoded features...")
xgb_model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1,
    eval_metric='logloss'
)

xgb_model.fit(X_train_oh, y_train,
              eval_set=[(X_val_oh, y_val)],
              verbose=False)

# Evaluate
y_train_pred_xgb = xgb_model.predict(X_train_oh)
y_val_pred_xgb = xgb_model.predict(X_val_oh)
y_test_pred_xgb = xgb_model.predict(X_test_oh)

train_acc_xgb = accuracy_score(y_train, y_train_pred_xgb)
val_acc_xgb = accuracy_score(y_val, y_val_pred_xgb)
test_acc_xgb = accuracy_score(y_test, y_test_pred_xgb)

print(f"XGBoost Results:")
print(f"  Training accuracy: {train_acc_xgb:.4f}")
print(f"  Validation accuracy: {val_acc_xgb:.4f}")
print(f"  Test accuracy: {test_acc_xgb:.4f}")

# Train LightGBM
print("\nTraining LightGBM on one-hot encoded features...")
lgb_model = lgb.LGBMClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

lgb_model.fit(X_train_oh, y_train,
              eval_set=[(X_val_oh, y_val)],
              eval_metric='binary_logloss',
              callbacks=[lgb.log_evaluation(0)])

# Evaluate
y_train_pred_lgb = lgb_model.predict(X_train_oh)
y_val_pred_lgb = lgb_model.predict(X_val_oh)
y_test_pred_lgb = lgb_model.predict(X_test_oh)

train_acc_lgb = accuracy_score(y_train, y_train_pred_lgb)
val_acc_lgb = accuracy_score(y_val, y_val_pred_lgb)
test_acc_lgb = accuracy_score(y_test, y_test_pred_lgb)

print(f"LightGBM Results:")
print(f"  Training accuracy: {train_acc_lgb:.4f}")
print(f"  Validation accuracy: {val_acc_lgb:.4f}")
print(f"  Test accuracy: {test_acc_lgb:.4f}")

# Compare with SOTA
sota_baseline = 0.70
print(f"\nSOTA baseline: {sota_baseline:.4f}")
print(f"\nXGBoost vs SOTA: {test_acc_xgb:.4f} vs {sota_baseline:.4f} (difference: {test_acc_xgb - sota_baseline:.4f})")
print(f"LightGBM vs SOTA: {test_acc_lgb:.4f} vs {sota_baseline:.4f} (difference: {test_acc_lgb - sota_baseline:.4f})")

if test_acc_xgb > sota_baseline or test_acc_lgb > sota_baseline:
    print("\nSUCCESS: At least one model exceeds the SOTA baseline!")
else:
    print("\nNeither model exceeds the SOTA baseline yet.")