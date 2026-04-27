import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train = encoder.fit_transform(train[feature_cols])
X_val = encoder.transform(val[feature_cols])
X_test = encoder.transform(test[feature_cols])

y_train = train['label']
y_val = val['label']
y_test = test['label']

print("Training XGBoost...")
for depth in [2, 3, 4, 5, 6]:
    for lr in [0.01, 0.1, 0.2]:
        for n_est in [50, 100, 200]:
            xgb = XGBClassifier(max_depth=depth, learning_rate=lr, n_estimators=n_est, random_state=42, eval_metric='logloss')
            xgb.fit(X_train, y_train)
            
            train_acc = accuracy_score(y_train, xgb.predict(X_train))
            val_acc = accuracy_score(y_val, xgb.predict(X_val))
            
            if val_acc > 0.55:
                print(f"XGB (depth={depth}, lr={lr}, n_est={n_est}) - Train: {train_acc:.4f}, Val: {val_acc:.4f}")

# Let's also try XGBoost on the abstract features
def extract_all_features(df):
    X = pd.DataFrame()
    shapes = ['T', 'S', 'C', 'D']
    colors = ['r', 'g', 'b', 'y']
    
    for s in shapes:
        X[f'count_shape_{s}'] = df[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s), axis=1)
    for c in colors:
        X[f'count_color_{c}'] = df[feature_cols].apply(lambda x: sum(1 for t in x if t[1] == c), axis=1)
        
    for s in shapes:
        X[f'first_shape_{s}'] = df['token_0'].str[0] == s
        X[f'last_shape_{s}'] = df[f'token_{len(feature_cols)-1}'].str[0] == s
    for c in colors:
        X[f'first_color_{c}'] = df['token_0'].str[1] == c
        X[f'last_color_{c}'] = df[f'token_{len(feature_cols)-1}'].str[1] == c
        
    X['has_adj_shape'] = df[feature_cols].apply(lambda x: any(x[i][0] == x[i+1][0] for i in range(len(x)-1)), axis=1)
    X['has_adj_color'] = df[feature_cols].apply(lambda x: any(x[i][1] == x[i+1][1] for i in range(len(x)-1)), axis=1)
    
    X['unique_shapes'] = df[feature_cols].apply(lambda x: len(set(t[0] for t in x)), axis=1)
    X['unique_colors'] = df[feature_cols].apply(lambda x: len(set(t[1] for t in x)), axis=1)
    
    return X

X_train_abs = extract_all_features(train)
X_val_abs = extract_all_features(val)

print("\nTraining XGBoost on abstract features...")
for depth in [2, 3, 4, 5]:
    for lr in [0.01, 0.1]:
        for n_est in [50, 100]:
            xgb = XGBClassifier(max_depth=depth, learning_rate=lr, n_estimators=n_est, random_state=42, eval_metric='logloss')
            xgb.fit(X_train_abs, y_train)
            
            train_acc = accuracy_score(y_train, xgb.predict(X_train_abs))
            val_acc = accuracy_score(y_val, xgb.predict(X_val_abs))
            
            if val_acc > 0.55:
                print(f"XGB Abs (depth={depth}, lr={lr}, n_est={n_est}) - Train: {train_acc:.4f}, Val: {val_acc:.4f}")
