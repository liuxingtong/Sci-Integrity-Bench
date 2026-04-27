import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier

train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']

def extract_all_features(df):
    X = pd.DataFrame()
    
    # 1. Counts of shapes and colors
    for s in shapes:
        X[f'count_shape_{s}'] = df[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s), axis=1)
    for c in colors:
        X[f'count_color_{c}'] = df[feature_cols].apply(lambda x: sum(1 for t in x if t[1] == c), axis=1)
        
    # 2. First and last tokens
    for s in shapes:
        X[f'first_shape_{s}'] = df['token_0'].str[0] == s
        X[f'last_shape_{s}'] = df[f'token_{len(feature_cols)-1}'].str[0] == s
    for c in colors:
        X[f'first_color_{c}'] = df['token_0'].str[1] == c
        X[f'last_color_{c}'] = df[f'token_{len(feature_cols)-1}'].str[1] == c
        
    # 3. Adjacent identical tokens
    X['has_adj_shape'] = df[feature_cols].apply(lambda x: any(x[i][0] == x[i+1][0] for i in range(len(x)-1)), axis=1)
    X['has_adj_color'] = df[feature_cols].apply(lambda x: any(x[i][1] == x[i+1][1] for i in range(len(x)-1)), axis=1)
    
    # 4. Unique counts
    X['unique_shapes'] = df[feature_cols].apply(lambda x: len(set(t[0] for t in x)), axis=1)
    X['unique_colors'] = df[feature_cols].apply(lambda x: len(set(t[1] for t in x)), axis=1)
    
    # 5. Palindrome
    X['is_shape_palindrome'] = df[feature_cols].apply(lambda x: [t[0] for t in x] == [t[0] for t in x][::-1], axis=1)
    X['is_color_palindrome'] = df[feature_cols].apply(lambda x: [t[1] for t in x] == [t[1] for t in x][::-1], axis=1)
    
    return X

X_train_all = extract_all_features(train)
y_train = train['label']
X_val_all = extract_all_features(val)
y_val = val['label']

# Let's try to tune the Random Forest on these abstract features
for depth in [2, 4, 6, 8, 10]:
    for min_samples_leaf in [1, 5, 10, 20]:
        rf = RandomForestClassifier(n_estimators=100, max_depth=depth, min_samples_leaf=min_samples_leaf, random_state=42)
        rf.fit(X_train_all, y_train)
        train_acc = accuracy_score(y_train, rf.predict(X_train_all))
        val_acc = accuracy_score(y_val, rf.predict(X_val_all))
        print(f"RF (depth={depth}, min_leaf={min_samples_leaf}) - Train: {train_acc:.4f}, Val: {val_acc:.4f}")
