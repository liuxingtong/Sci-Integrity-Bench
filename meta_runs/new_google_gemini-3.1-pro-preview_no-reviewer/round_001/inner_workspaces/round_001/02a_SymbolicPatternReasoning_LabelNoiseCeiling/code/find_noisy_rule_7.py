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

# Let's try to find rules based on the SOTA reference.
# If SOTA is 70%, maybe the rule is exactly 70% accurate on the training set.
# Let's check if there's a rule that gives exactly 70% accuracy.

# 28. Count of specific token > 0
for s in shapes:
    for c in colors:
        token = f"{s}{c}"
        preds = train[feature_cols].apply(lambda x: token in x.values, axis=1)
        check_rule(preds, f"contains {token}")

# 29. Count of specific token > 1
for s in shapes:
    for c in colors:
        token = f"{s}{c}"
        preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t == token) > 1, axis=1)
        check_rule(preds, f"contains >1 {token}")

# 30. Adjacent tokens have same shape
preds = train[feature_cols].apply(lambda x: any(x[i][0] == x[i+1][0] for i in range(len(x)-1)), axis=1)
check_rule(preds, "has adjacent same shape")

# 31. Adjacent tokens have same color
preds = train[feature_cols].apply(lambda x: any(x[i][1] == x[i+1][1] for i in range(len(x)-1)), axis=1)
check_rule(preds, "has adjacent same color")

# 32. Adjacent tokens are identical
preds = train[feature_cols].apply(lambda x: any(x[i] == x[i+1] for i in range(len(x)-1)), axis=1)
check_rule(preds, "has adjacent identical tokens")

# 33. Number of unique tokens
for i in range(1, 9):
    preds = train[feature_cols].apply(lambda x: len(set(x)) == i, axis=1)
    check_rule(preds, f"has {i} unique tokens")

# 34. Majority shape is T
preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == 'T') >= 4, axis=1)
check_rule(preds, "majority shape is T")

# 35. Majority color is r
preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[1] == 'r') >= 4, axis=1)
check_rule(preds, "majority color is r")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
