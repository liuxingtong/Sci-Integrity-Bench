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

# 11. Majority shape/color
def majority_shape(row):
    counts = {s: 0 for s in shapes}
    for t in row:
        counts[t[0]] += 1
    return max(counts, key=counts.get)

def majority_color(row):
    counts = {c: 0 for c in colors}
    for t in row:
        counts[t[1]] += 1
    return max(counts, key=counts.get)

maj_shapes = train[feature_cols].apply(majority_shape, axis=1)
for s in shapes:
    check_rule(maj_shapes == s, f"majority shape is {s}")

maj_colors = train[feature_cols].apply(majority_color, axis=1)
for c in colors:
    check_rule(maj_colors == c, f"majority color is {c}")

# 12. Contains specific sequence of shapes/colors
def contains_shape_seq(row, seq):
    row_shapes = [t[0] for t in row]
    for i in range(len(row_shapes) - len(seq) + 1):
        if row_shapes[i:i+len(seq)] == list(seq):
            return True
    return False

def contains_color_seq(row, seq):
    row_colors = [t[1] for t in row]
    for i in range(len(row_colors) - len(seq) + 1):
        if row_colors[i:i+len(seq)] == list(seq):
            return True
    return False

import itertools
for seq in itertools.product(shapes, repeat=2):
    preds = train[feature_cols].apply(lambda x: contains_shape_seq(x, seq), axis=1)
    check_rule(preds, f"contains shape seq {''.join(seq)}")

for seq in itertools.product(colors, repeat=2):
    preds = train[feature_cols].apply(lambda x: contains_color_seq(x, seq), axis=1)
    check_rule(preds, f"contains color seq {''.join(seq)}")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
