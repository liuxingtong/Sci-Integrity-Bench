import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# The task is "LabelNoiseCeiling".
# The SOTA is 70%.
# This means the labels are 30% noisy.
# If the labels are 30% noisy, the true rule should have exactly 70% accuracy on the training set.
# Let's look for rules that have exactly 70% accuracy on the training set.

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
    if abs(acc - 0.7) < 0.02:
        print(f"Rule: {name}, Acc: {acc:.4f}")

# 58. Count of specific shape == Count of specific color
for s in shapes:
    for c in colors:
        preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s) == sum(1 for t in x if t[1] == c), axis=1)
        check_rule(preds, f"count shape {s} == count color {c}")

# 59. Count of specific shape > Count of specific color
for s in shapes:
    for c in colors:
        preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s) > sum(1 for t in x if t[1] == c), axis=1)
        check_rule(preds, f"count shape {s} > count color {c}")

# 60. Sum of counts of two shapes == Sum of counts of two colors
import itertools
for s1, s2 in itertools.combinations(shapes, 2):
    for c1, c2 in itertools.combinations(colors, 2):
        preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] in (s1, s2)) == sum(1 for t in x if t[1] in (c1, c2)), axis=1)
        check_rule(preds, f"count {s1}+{s2} == count {c1}+{c2}")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
