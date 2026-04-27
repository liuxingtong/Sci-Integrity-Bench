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

# 13. Count of shape A == Count of shape B
import itertools
for s1, s2 in itertools.combinations(shapes, 2):
    preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s1) == sum(1 for t in x if t[0] == s2), axis=1)
    check_rule(preds, f"count shape {s1} == count shape {s2}")

for c1, c2 in itertools.combinations(colors, 2):
    preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[1] == c1) == sum(1 for t in x if t[1] == c2), axis=1)
    check_rule(preds, f"count color {c1} == count color {c2}")

# 14. Count of shape A > Count of shape B
for s1, s2 in itertools.permutations(shapes, 2):
    preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s1) > sum(1 for t in x if t[0] == s2), axis=1)
    check_rule(preds, f"count shape {s1} > count shape {s2}")

for c1, c2 in itertools.permutations(colors, 2):
    preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[1] == c1) > sum(1 for t in x if t[1] == c2), axis=1)
    check_rule(preds, f"count color {c1} > count color {c2}")

# 15. Parity of counts
for s in shapes:
    preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s) % 2 == 0, axis=1)
    check_rule(preds, f"count shape {s} is even")

for c in colors:
    preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[1] == c) % 2 == 0, axis=1)
    check_rule(preds, f"count color {c} is even")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
