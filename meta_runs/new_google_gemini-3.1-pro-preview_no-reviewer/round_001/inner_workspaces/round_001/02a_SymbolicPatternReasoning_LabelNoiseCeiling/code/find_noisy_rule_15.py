import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# Let's think outside the box.
# What if the rule is based on the *order* of the tokens, but not in a simple way?
# For example, "the first token determines the rule for the rest of the sequence".

shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']

best_acc = 0
best_rule = ""

def check_rule(preds, name):
    global best_acc, best_rule
    acc = accuracy_score(train['label'], preds)
    if acc < 0.5:
        acc = 1 - acc
        name = f"NOT ({name})"
    if acc > best_acc:
        best_acc = acc
        best_rule = name
    if acc > 0.65:
        print(f"Rule: {name}, Acc: {acc:.4f}")

# 51. If first token is X, then rule is Y
for s in shapes:
    subset = train[train['token_0'].str[0] == s]
    if len(subset) == 0: continue
    
    # Check simple rules on this subset
    for c in colors:
        preds = subset[feature_cols].apply(lambda x: sum(1 for t in x if t[1] == c) > 2, axis=1)
        acc = accuracy_score(subset['label'], preds)
        if acc > 0.7 or acc < 0.3:
            print(f"If first shape is {s}, then count color {c} > 2 has acc {acc:.4f}")

# Let's try to train a model that can learn this kind of conditional logic.
# A Decision Tree should be able to learn this, but we already tried it and it failed.
# Why did the Decision Tree fail? Because it splits on specific tokens, not abstract concepts like "count of color c".

# Let's create a dataset with ALL possible abstract features.

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

from sklearn.ensemble import RandomForestClassifier
rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
rf.fit(X_train_all, y_train)

print(f"\nRF on all abstract features Train Acc: {accuracy_score(y_train, rf.predict(X_train_all)):.4f}")

# Let's check feature importances
importances = rf.feature_importances_
indices = np.argsort(importances)[::-1]
print("\nTop 10 features:")
for i in range(10):
    print(f"{X_train_all.columns[indices[i]]}: {importances[indices[i]]:.4f}")
