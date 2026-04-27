import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

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

# 1. Contains specific token
for s in shapes:
    for c in colors:
        token = f"{s}{c}"
        preds = train[feature_cols].apply(lambda x: token in x.values, axis=1)
        check_rule(preds, f"contains {token}")

# 2. Contains specific shape
for s in shapes:
    preds = train[feature_cols].apply(lambda x: any(t[0] == s for t in x), axis=1)
    check_rule(preds, f"contains shape {s}")

# 3. Contains specific color
for c in colors:
    preds = train[feature_cols].apply(lambda x: any(t[1] == c for t in x), axis=1)
    check_rule(preds, f"contains color {c}")

# 4. Token at specific position
for i, col in enumerate(feature_cols):
    for s in shapes:
        for c in colors:
            token = f"{s}{c}"
            preds = train[col] == token
            check_rule(preds, f"pos {i} is {token}")
            
    for s in shapes:
        preds = train[col].str[0] == s
        check_rule(preds, f"pos {i} shape is {s}")
        
    for c in colors:
        preds = train[col].str[1] == c
        check_rule(preds, f"pos {i} color is {c}")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
