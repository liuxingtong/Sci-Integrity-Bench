import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# The SOTA is 70%. This is a very specific number.
# If the labels are 30% noisy, then the true rule should have exactly 70% accuracy on the training set.
# Let's look for rules that have exactly 70% accuracy.

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
    if abs(acc - 0.7) < 0.05:
        print(f"Rule: {name}, Acc: {acc:.4f}")

# Let's try some more complex rules
# 36. Number of unique shapes + Number of unique colors
for i in range(2, 9):
    preds = train[feature_cols].apply(lambda x: len(set(t[0] for t in x)) + len(set(t[1] for t in x)) == i, axis=1)
    check_rule(preds, f"unique shapes + unique colors == {i}")

# 37. Contains a specific shape AND a specific color (not necessarily same token)
for s in shapes:
    for c in colors:
        preds = train[feature_cols].apply(lambda x: any(t[0] == s for t in x) and any(t[1] == c for t in x), axis=1)
        check_rule(preds, f"contains shape {s} AND color {c}")

# 38. Contains a specific shape OR a specific color
for s in shapes:
    for c in colors:
        preds = train[feature_cols].apply(lambda x: any(t[0] == s for t in x) or any(t[1] == c for t in x), axis=1)
        check_rule(preds, f"contains shape {s} OR color {c}")

# 39. Count of specific shape + Count of specific color
for s in shapes:
    for c in colors:
        for i in range(1, 9):
            preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s) + sum(1 for t in x if t[1] == c) == i, axis=1)
            check_rule(preds, f"count shape {s} + count color {c} == {i}")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
